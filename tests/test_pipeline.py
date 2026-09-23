"""Real-data integration tests plus boundary/counterfactual leakage tests.
No HTTP network is needed: archived weather is read from committed cache.
"""
import copy
import json
import threading
import joblib
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from src.config import TURBINES, RAW, MODELS, RESULTS, local_date
from src.data.loader import load_turbine, load_csv
from src.data.preprocessing import preprocess, read_hourly
from src.data.features import make_features, HISTORY_FEATURES
from src.models.predict import predict, load_model
from src.models.train import supervised_dataset
from src.models.evaluate import metrics
from src.services.weather_provider import (OpenMeteoProvider, PersistenceWeatherProvider, WeatherResult,
    WeatherError, validate_weather, target_index)
from src.agents.forecast_agent import ForecastAgent, AgentBusyError
from src.api.main import app
from src.api.schemas import ForecastResponse

@pytest.fixture(scope='module')
def history(): return read_hourly('turbine_1')

@pytest.fixture(scope='module')
def origin(): return local_date('2026-02-01')

@pytest.fixture(scope='module')
def weather(origin):
    cfg=TURBINES['turbine_1']
    return OpenMeteoProvider(offline=True).get_forecast(cfg['latitude'],cfg['longitude'],origin,48)

@pytest.fixture
def client(monkeypatch,tmp_path):
    monkeypatch.setenv('WEATHER_OFFLINE','true')
    monkeypatch.setenv('FORECAST_MODE','replay')
    monkeypatch.setenv('REPLAY_ORIGIN','2026-02-01T00:00:00+05:00')
    import src.api.main as api
    monkeypatch.setattr(api,'agent',ForecastAgent(tmp_path))
    with TestClient(app) as client:
        yield client

@pytest.mark.parametrize('turbine,rows',[('turbine_1',142360),('turbine_2',149499)])
def test_real_csv(turbine,rows):
    df,report=load_turbine(turbine)
    assert len(df)==rows
    assert report['separator']==',' and 'UTF-8' in report['encoding']
    assert df.timestamp.max()<local_date('2026-02-01')
    assert df.timestamp.is_unique
    assert report['nulls']['power']==0

def test_csv_schema_rejected(tmp_path):
    path=tmp_path/'bad.csv'; path.write_text('a,b\n1,2\n')
    with pytest.raises(ValueError): load_csv(path)

def test_hourly_cleaning_and_target_missing():
    times=pd.date_range('2026-01-01',periods=12,freq='10min',tz='UTC')
    df=pd.DataFrame({'timestamp':times,'power':.5,'wind_speed':8.,'temperature':2.})
    # Six valid readings for hour 0; only three for hour 1 -> missing target.
    df=df.iloc[:9]
    duplicate=df.iloc[[0]].copy()
    combined=pd.concat([df,duplicate],ignore_index=True)
    hourly,audit=preprocess(combined)
    assert hourly.power.iloc[0]==.5 and hourly.power_samples.iloc[0]==6
    assert np.isnan(hourly.power.iloc[1])
    bad=df.copy(); bad.loc[0,'power']=2; bad.loc[1,'wind_speed']=-1
    _,audit=preprocess(bad)
    assert audit['invalid_power']==1 and audit['invalid_wind_speed']==1

def test_origin_features_and_no_future_leakage(history,origin,weather):
    x=make_features(history,origin,weather.frame)
    assert set(HISTORY_FEATURES).issubset(x.columns)
    assert x.horizon.tolist()==list(range(1,49))
    assert x.power_lag_1.iloc[0]==history.loc[origin-pd.Timedelta(hours=1),'power']
    assert x.power_lag_24.iloc[0]==history.loc[origin-pd.Timedelta(hours=24),'power']
    expected=history.power.loc[(history.index<origin)&(history.index>=origin-pd.Timedelta(hours=3))].mean()
    assert x.rolling_power_mean_3.iloc[0]==pytest.approx(expected)
    poisoned=pd.concat([history,pd.DataFrame({'power':999.,'wind_speed':999.,'temperature':999.},index=weather.frame.index)])
    pd.testing.assert_frame_equal(x,make_features(poisoned,origin,weather.frame))
    bundle=load_model('turbine_1')
    a,_=predict(bundle,history,origin,weather.frame)
    b,_=predict(bundle,poisoned,origin,weather.frame)
    pd.testing.assert_frame_equal(a,b)

def test_stale_lags_not_carried_forward(history,origin,weather):
    later=origin+pd.Timedelta(days=10)
    w=weather.frame.copy(); w.index=target_index(later,48)
    x=make_features(history,later,w)
    assert x[HISTORY_FEATURES].isna().all(axis=None)

def test_training_targets_purged_at_cutoff(history,origin,weather):
    start=origin-pd.Timedelta(days=3)
    end=origin-pd.Timedelta(days=1)
    cfg=TURBINES['turbine_1']
    w=OpenMeteoProvider(offline=True).archive_range(cfg['latitude'],cfg['longitude'],start,origin)
    x,y,origins=supervised_dataset(history,w,start,end)
    assert (x.index<end).all()
    assert (origins<=x.index).all()
    poisoned=history.copy(); poisoned.loc[poisoned.index>=end,'power']=999
    a,b,_=supervised_dataset(poisoned,w,start,end)
    pd.testing.assert_frame_equal(x,a); pd.testing.assert_series_equal(y,b)

def test_future_trained_model_rejected(history,origin,weather):
    bundle=load_model('turbine_1').copy()
    bundle['trained_until']=(origin+pd.Timedelta(days=1)).isoformat()
    with pytest.raises(ValueError,match='leakage'): predict(bundle,history,origin,weather.frame)

def test_archived_weather_causality(origin,weather):
    assert weather.metadata['source']=='open_meteo_previous_runs'
    assert weather.metadata['forecast_lead_hours']==72
    assert pd.Timestamp(weather.metadata['latest_availability_bound'])<origin
    assert not weather.metadata['is_fallback']
    validate_weather(weather.frame,origin,48)

@pytest.mark.parametrize('kind',['missing','negative','nan','duplicate','unsorted'])
def test_weather_rejected(kind,weather,origin):
    w=weather.frame.copy()
    if kind=='missing': w=w.iloc[:-1]
    elif kind=='negative': w.iloc[0,0]=-1
    elif kind=='nan': w.iloc[1,1]=np.nan
    elif kind=='duplicate': w.index=pd.DatetimeIndex([w.index[0]]+list(w.index[:-1]))
    elif kind=='unsorted': w=w.iloc[::-1]
    with pytest.raises(WeatherError): validate_weather(w,origin,48)

def test_naive_time_rejected(history,weather):
    with pytest.raises(ValueError,match='timezone'): make_features(history,pd.Timestamp('2026-02-01'),weather.frame)

def test_fallback_refuses_stale(history,origin):
    p=PersistenceWeatherProvider(history)
    result=p.get_forecast(0,0,origin,24)
    assert result.metadata['is_fallback']
    with pytest.raises(WeatherError): p.get_forecast(0,0,origin+pd.Timedelta(days=3),24)

def test_empty_actuals_are_not_fake_metrics():
    assert metrics([np.nan,np.nan],[.2,.5])=={'n':0,'mae':None,'normalized_mae':None,'rmse':None,'r2':None}

def test_prediction_schema_and_saved_result(history,origin,weather,tmp_path):
    a=ForecastAgent(tmp_path)
    result=a.run('turbine_1',48,origin=origin,provider=OpenMeteoProvider(offline=True))
    ForecastResponse.model_validate(result)
    assert result['agent']['status']=='COMPLETED'
    assert len(result['agent']['steps'])==6
    saved=json.loads((tmp_path/'turbine_1_latest.json').read_text())
    assert saved['run_id']==result['run_id']
    assert a.status('turbine_1')['status']=='COMPLETED'

def test_new_weather_recalculates(origin,weather,tmp_path):
    a=ForecastAgent(tmp_path)
    metadata={'issued_at':(origin-pd.Timedelta(hours=3)).isoformat(),'source':'test_counterfactual','is_fallback':False}
    first=a.run('turbine_1',48,origin=origin,weather_override=WeatherResult(weather.frame,metadata))
    changed=weather.frame.copy(); changed.wind_speed=changed.wind_speed+5
    second=a.run('turbine_1',48,origin=origin,weather_override=WeatherResult(changed,metadata))
    assert first['weather']['input_sha256']!=second['weather']['input_sha256']
    assert first['forecast']!=second['forecast']
    assert first['run_id']!=second['run_id']

def test_agent_failure_and_lock_release(origin,weather,tmp_path):
    a=ForecastAgent(tmp_path)
    invalid=WeatherResult(weather.frame,{'issued_at':(origin+pd.Timedelta(hours=1)).isoformat()})
    with pytest.raises(WeatherError): a.run('turbine_1',origin=origin,weather_override=invalid)
    assert a.status('turbine_1')['status']=='FAILED'
    a.run('turbine_1',origin=origin,provider=OpenMeteoProvider(offline=True))
    assert a.status('turbine_1')['status']=='COMPLETED'

def test_busy_agent(origin,tmp_path):
    a=ForecastAgent(tmp_path)
    a._run_locks['turbine_1'].acquire()
    try:
        with pytest.raises(AgentBusyError): a.run('turbine_1',origin=origin)
    finally: a._run_locks['turbine_1'].release()

def test_health_turbines_and_cors(client):
    assert client.get('/api/health').json()['ready'] is True
    assert len(client.get('/api/turbines').json()['turbines'])==2
    assert client.get('/api/turbines/turbine_1').json()['latitude']==43.645150
    response=client.options('/api/health',headers={'Origin':'http://localhost:5173','Access-Control-Request-Method':'GET'})
    assert response.headers['access-control-allow-origin']=='http://localhost:5173'

@pytest.mark.parametrize('turbine',['turbine_1','turbine_2'])
@pytest.mark.parametrize('hours',[24,48])
def test_api_forecast(client,turbine,hours):
    response=client.get(f'/api/forecast/{turbine}?hours={hours}')
    assert response.status_code==200,response.text
    result=ForecastResponse.model_validate(response.json())
    assert len(result.forecast)==hours
    assert result.agent['status']=='COMPLETED'

def test_all_details_backtest_and_status(client):
    response=client.get('/api/forecast/all?hours=24')
    assert response.status_code==200 and len(response.json())==2
    response=client.get('/api/turbines/turbine_1/details?hours=24')
    assert response.status_code==200,response.text
    data=response.json()
    assert data['current']['is_live'] is False
    assert data['model']['mae']>0 and len(data['forecast'])==24
    assert client.get('/api/agent/status').json()['agents']['turbine_1']['status']=='COMPLETED'
    m=client.get('/api/backtest/metrics').json()
    assert m['turbines']['turbine_1']['status']=='unscored_missing_actuals'
    response=client.get('/api/backtest/turbine_1?limit=3')
    assert response.status_code==200,response.text
    assert response.json()['predictions'][0]['actual_power'] is None
    assert client.get('/api/validation/metrics').status_code==200

def test_bad_requests(client):
    assert client.get('/api/forecast/missing').status_code==404
    assert client.get('/api/forecast/turbine_1?hours=25').status_code==422
    assert client.post('/api/forecast/recalculate',json={'turbine_id':'missing'}).status_code==422
    assert client.post('/api/forecast/recalculate',json={'turbine_id':'turbine_1','forecast_origin':'2026-02-01T00:00:00'}).status_code==422

def test_recalculate_endpoint(client,weather,origin):
    points=[{'timestamp':ts.isoformat(),**row.to_dict()} for ts,row in weather.frame.iterrows()]
    body={'turbine_id':'turbine_1','hours':48,'forecast_origin':origin.isoformat(),
          'weather':points,'weather_issued_at':(origin-pd.Timedelta(hours=3)).isoformat()}
    response=client.post('/api/forecast/recalculate',json=body)
    assert response.status_code==200,response.text
    assert response.json()['weather']['source']=='user_supplied_forecast'
    body['weather_issued_at']=(origin+pd.Timedelta(hours=1)).isoformat()
    assert client.post('/api/forecast/recalculate',json=body).status_code==503

def test_backtest_artifact_no_labels_faked():
    df=pd.read_csv(RESULTS/'backtest_predictions.csv')
    assert len(df)==2*28*48
    assert df.actual_power.isna().all() and df.error.isna().all()
    assert (pd.to_datetime(df.weather_availability_bound,utc=True)<=pd.to_datetime(df.forecast_origin,utc=True)).all()
    assert (pd.to_datetime(df.model_trained_until,utc=True)<=pd.to_datetime(df.forecast_origin,utc=True)).all()
    assert (df.groupby(['turbine_id','forecast_origin']).size()==48).all()
