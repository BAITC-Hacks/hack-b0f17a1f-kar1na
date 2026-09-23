import json
import pytest
from fastapi.testclient import TestClient
from src.agents.forecast_agent import ForecastAgent
from src.agents.turbine_insights import TurbineInsights, COMPONENTS
from src.agents.copilot import OpenAIUnavailable


class Explainer:
    def __init__(self): self.calls=[]
    def create(self,**body):
        self.calls.append(body)
        return {'output':[{'type':'message','content':[{'type':'output_text','text':'Генератор преобразует вращение в электрическую энергию. Диагностической телеметрии нет.'}]}]}


@pytest.fixture
def service(tmp_path,monkeypatch):
    monkeypatch.setenv('WEATHER_OFFLINE','true')
    return TurbineInsights(ForecastAgent(tmp_path),Explainer())


@pytest.mark.parametrize('component',list(COMPONENTS))
def test_component_context_is_grounded(service,component):
    result=service.inspect('turbine_1',component)
    context=result['context']
    assert context['component']==component
    assert context['component_condition']=='unknown_no_component_telemetry'
    assert context['manufacturer'] is None and context['rated_power_kw'] is None
    assert context['latest_observation']['is_live'] is False
    assert context['latest_observation']['timestamp'].endswith('+05:00')
    assert context['forecast_origin']=='2026-02-01T00:00:00+05:00'
    assert service.client.calls[0]['store'] is False
    assert 'ambient_temperature' in service.client.calls[0]['input']


def test_same_context_cached_but_turbine_component_and_question_are_distinct(service):
    first=service.inspect('turbine_1','generator')
    assert service.inspect('turbine_1','generator')['cached']
    assert len(service.client.calls)==1
    second=service.inspect('turbine_2','generator')
    assert second['context']['turbine_id']=='turbine_2'
    assert second['context']['latitude']!=first['context']['latitude']
    service.inspect('turbine_2','gearbox')
    service.inspect('turbine_2','gearbox',question='Как работает?')
    assert len(service.client.calls)==4


def test_explanation_outage_preserves_real_data(service):
    class Down:
        def create(self,**_): raise OpenAIUnavailable('Unavailable')
    service.client=Down()
    r=service.inspect('turbine_1','rotor')
    assert r['engine']=='data_summary' and r['llm_error']
    assert r['context']['latest_observation']['power'] is not None
    assert not service._cache


def test_inspection_api_validates_scope(service,monkeypatch):
    from src.api import main
    monkeypatch.setattr(main,'insights',service)
    c=TestClient(main.app)
    assert c.post('/api/agent/inspect',json={'turbine_id':'turbine_2','component':'generator'}).status_code==200
    assert c.post('/api/agent/inspect',json={'turbine_id':'unknown'}).status_code==422
    assert c.post('/api/agent/inspect',json={'turbine_id':'turbine_1','component':'unknown'}).status_code==422
    assert c.post('/api/agent/inspect',json={'turbine_id':'turbine_1','question':'x'*1001}).status_code==422
