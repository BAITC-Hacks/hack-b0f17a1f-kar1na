"""Agent contracts: tool execution, failure recovery, causal data and versioning."""
import json
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from src.config import local_date, TURBINES
from src.agents.forecast_agent import ForecastAgent
from src.agents.copilot import Copilot, OpenAIUnavailable, ResponsesClient
from src.agents.monitor import ForecastMonitor
from src.services.weather_provider import OpenMeteoProvider, WeatherResult, WeatherError


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setenv('WEATHER_OFFLINE', 'true')
    monkeypatch.setenv('AGENT_MONITOR_ENABLED', 'false')


class ToolClient:
    def __init__(self, names=None):
        self.names = names or ['inspect_inputs', 'run_forecast', 'assess_forecast', 'read_validation', 'compare_revision']
        self.requests = []

    def create(self, **body):
        self.requests.append(json.loads(json.dumps(body)))
        n = len(self.requests)-1
        if n < len(self.names):
            return {'output': [{'type': 'function_call', 'name': self.names[n], 'arguments': '{}', 'call_id': str(n)}]}
        return {'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': 'Прогноз проверен инструментами.'}]}],
                'usage': {'input_tokens': 12, 'output_tokens': 8}}


def test_llm_tools_execute_and_are_returned(tmp_path):
    client = ToolClient()
    result = Copilot(ForecastAgent(tmp_path/'f'), client, tmp_path/'a').run('turbine_1')
    assert result['status'] == 'completed' and result['engine'] == 'openai'
    assert [t['tool'] for t in result['tools']] == client.names
    assert all(t['status'] == 'ok' for t in result['tools'])
    assert len(result['forecast']['forecast']) == 48
    assert result['assessment']['peak_time_astana'].endswith('+05:00')
    assert result['usage']['output_tokens'] == 8
    assert all(r['store'] is False for r in client.requests)
    assert any(i['type']=='function_call_output' for i in client.requests[-1]['input'] if 'type' in i)


def test_llm_outage_does_not_fake_success(tmp_path):
    class Down:
        def create(self, **_): raise OpenAIUnavailable('HTTP 429')
    result = Copilot(ForecastAgent(tmp_path/'f'), Down(), tmp_path/'a').run('turbine_2', hours=24)
    assert result['status'] == 'degraded'
    assert result['engine'] == 'deterministic_recovery'
    assert result['llm_error'] == 'HTTP 429'
    assert len(result['forecast']['forecast']) == 24
    assert all(t['actor'] == 'recovery' for t in result['tools'])


def test_missing_key_does_not_use_network(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    with pytest.raises(OpenAIUnavailable, match='не настроен'):
        ResponsesClient().create()


def test_upstream_error_body_not_exposed(monkeypatch):
    import httpx
    monkeypatch.setenv('OPENAI_API_KEY','test-not-a-real-key')
    monkeypatch.setattr(httpx,'post',lambda *a,**k: httpx.Response(401,json={'error':{'message':'private-secret'}}))
    with pytest.raises(OpenAIUnavailable) as error:
        ResponsesClient().create()
    assert '401' in str(error.value) and 'private-secret' not in str(error.value)


def test_untrusted_tool_name_cannot_execute(tmp_path):
    result=Copilot(ForecastAgent(tmp_path/'f'),ToolClient(['delete_files','inspect_inputs','run_forecast','assess_forecast']),tmp_path/'a').run('turbine_1')
    assert result['tools'][0]['status']=='error'
    assert result['status']=='completed'


def test_loop_budget_recovers(tmp_path):
    result=Copilot(ForecastAgent(tmp_path/'f'),ToolClient(['unknown']*20),tmp_path/'a').run('turbine_1')
    assert result['status']=='degraded' and len(result['tools'])<=10


def test_scada_tool_excludes_future_and_metrics_are_cutoff_gated(tmp_path):
    # Jan 1 origin must not reveal the Jan evaluation report, and deployment model must fail its cutoff.
    result=Copilot(ForecastAgent(tmp_path/'f'),ToolClient(['inspect_inputs','read_validation','run_forecast']),tmp_path/'a').run('turbine_1',origin=local_date('2026-01-01'))
    assert pd.Timestamp(result['tools'][0]['result']['latest_complete_hour'])<local_date('2026-01-01')
    assert result['tools'][1]['status']=='error'
    assert result['forecast'] is None and result['status']=='failed'


def test_unchanged_inputs_reuse_version_changed_inputs_create_revision(tmp_path):
    a=ForecastAgent(tmp_path)
    first=a.run('turbine_1')
    second=a.run('turbine_1')
    assert first['run_id']==second['run_id'] and second['unchanged']
    cfg=TURBINES['turbine_1'];origin=local_date('2026-02-01')
    w=OpenMeteoProvider(offline=True).get_forecast(cfg['latitude'],cfg['longitude'],origin,48)
    w.frame.wind_speed+=2
    third=a.run('turbine_1',weather_override=WeatherResult(w.frame,{'issued_at':(origin-pd.Timedelta(hours=4)).isoformat(),'source':'counterfactual','is_fallback':False}))
    assert third['run_id']!=first['run_id']
    assert third['revision']['previous_run_id']==first['run_id']
    assert third['revision']['overlap_hours']==48
    assert third['revision']['mean_absolute_change']>0


def test_injected_provider_cannot_bypass_causality(tmp_path):
    origin=local_date('2026-02-01');cfg=TURBINES['turbine_1']
    w=OpenMeteoProvider(offline=True).get_forecast(cfg['latitude'],cfg['longitude'],origin,48)
    w.metadata['latest_availability_bound']=(origin+pd.Timedelta(hours=1)).isoformat()
    class Bad:
        def get_forecast(self,*_): return w
    with pytest.raises(WeatherError,match='availability'):
        ForecastAgent(tmp_path).run('turbine_1',provider=Bad())


def test_monitor_updates_and_then_reports_unchanged(tmp_path):
    m=ForecastMonitor(ForecastAgent(tmp_path/'f'),tmp_path/'m')
    first=m.tick();second=m.tick()
    assert all(v['status']=='updated' for v in first['turbines'].values())
    assert all(v['status']=='unchanged' for v in second['turbines'].values())
    assert (tmp_path/'m'/'status.json').exists()


def test_monitor_failure_is_visible_and_recovers(tmp_path):
    class Agent:
        def run(self,*_): raise WeatherError('unavailable')
    m=ForecastMonitor(Agent(),tmp_path/'m')
    assert m.tick()['status']=='degraded'
    m.agent=ForecastAgent(tmp_path/'f')
    assert m.tick()['status']=='watching'


def test_agent_api_export_and_secret_absence(monkeypatch,tmp_path):
    from src.api import main
    a=ForecastAgent(tmp_path/'f')
    monkeypatch.setattr(main,'agent',a)
    monkeypatch.setattr(main,'copilot',Copilot(a,ToolClient(),tmp_path/'a'))
    c=TestClient(main.app)
    r=c.post('/api/agent/run',json={'turbine_id':'turbine_1','hours':24})
    assert r.status_code==200 and r.json()['status']=='completed'
    assert c.post('/api/agent/run',json={'hours':25}).status_code==422
    assert c.post('/api/agent/run',json={'forecast_origin':'2026-02-01'}).status_code==422
    assert c.get('/api/health').json()['display_timezone']=='Asia/Almaty'
    r=c.get('/api/export/turbine_1?hours=24')
    assert r.status_code==200 and 'timestamp_astana' in r.text and '+05:00' in r.text
    assert len(r.text.strip().splitlines())==25
    assert 'OPENAI_API_KEY' not in c.get('/api/health').text
