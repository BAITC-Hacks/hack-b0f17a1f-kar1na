"""FastAPI integration for a two-turbine 3D dashboard."""
import json
import logging
import os
from typing import Literal, Optional
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.config import TURBINES, RESULTS, MODELS, PROCESSED
from src.agents.forecast_agent import ForecastAgent, AgentBusyError
from src.data.preprocessing import read_hourly
from src.services.weather_provider import WeatherError, WeatherResult
from src.api.schemas import ForecastResponse, RecalculateRequest
from src.utils import clean_json

logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(name)s %(message)s')
app=FastAPI(title='AlemWind Forecast API',version='1.0.0',description='Normalized hourly wind power, 24/48h; UTC timestamps.')
app.add_middleware(CORSMiddleware,allow_origins=os.getenv('CORS_ORIGINS','http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173').split(','),
    allow_credentials=False,allow_methods=['GET','POST','OPTIONS'],allow_headers=['Content-Type'])
agent=ForecastAgent()

@app.exception_handler(WeatherError)
async def weather_error(request,exc):
    return JSONResponse(status_code=503,content={'detail':str(exc),'error':'weather_unavailable'})

@app.exception_handler(FileNotFoundError)
async def missing_artifact(request,exc):
    return JSONResponse(status_code=503,content={'detail':str(exc),'error':'missing_artifact'})

@app.exception_handler(AgentBusyError)
async def busy(request,exc):
    return JSONResponse(status_code=409,content={'detail':str(exc),'error':'agent_busy'})

@app.exception_handler(ValueError)
async def invalid_value(request,exc):
    return JSONResponse(status_code=422,content={'detail':str(exc),'error':'invalid_input'})

def known(turbine_id):
    if turbine_id not in TURBINES: raise HTTPException(404,'Unknown turbine')
    return TURBINES[turbine_id]

def artifact(name):
    path=RESULTS/name
    if not path.exists(): raise HTTPException(503,f'Missing {name}; run training/backtest scripts')
    return json.loads(path.read_text())

@app.get('/api/health')
def health():
    artifacts={t:{'model':(MODELS/f'{t}.joblib').exists(),'processed_data':(PROCESSED/f'{t}_hourly.csv').exists()} for t in TURBINES}
    return {'status':'ok','ready':all(all(v.values()) for v in artifacts.values()),'artifacts':artifacts,
            'default_mode':os.getenv('FORECAST_MODE','replay'),'timezone':'UTC','power_unit':'normalized'}

@app.get('/api/turbines')
def turbines():
    return {'turbines':list(TURBINES.values())}

@app.get('/api/turbines/{turbine_id}')
def turbine(turbine_id: str):
    return known(turbine_id)

# Static paths before variable paths.
@app.get('/api/forecast/all',response_model=list[ForecastResponse])
def forecast_all(hours: int=Query(48,ge=24,le=48,json_schema_extra={"enum":[24,48]}),mode: Optional[Literal['replay','live']]=None):
    return [agent.run(t,hours,mode) for t in TURBINES]

@app.get('/api/forecast/{turbine_id}',response_model=ForecastResponse)
def forecast(turbine_id: str,hours: int=Query(48,ge=24,le=48,json_schema_extra={"enum":[24,48]}),mode: Optional[Literal['replay','live']]=None):
    known(turbine_id)
    return agent.run(turbine_id,hours,mode)

@app.get('/api/backtest/metrics')
def backtest_metrics():
    return artifact('backtest_metrics.json')

@app.get('/api/validation/metrics')
def validation_metrics():
    return artifact('metrics.json')

@app.get('/api/backtest/{turbine_id}')
def backtest(turbine_id: str,limit: int=Query(200,ge=1,le=3000),offset: int=Query(0,ge=0)):
    known(turbine_id)
    path=RESULTS/'backtest_predictions.csv'
    if not path.exists(): raise HTTPException(503,'Run python scripts/run_backtest.py')
    frame=pd.read_csv(path)
    selected=frame[frame.turbine_id==turbine_id]
    return clean_json({'turbine_id':turbine_id,'total':len(selected),'offset':offset,'limit':limit,
                      'predictions':selected.iloc[offset:offset+limit].to_dict('records')})

@app.get('/api/agent/status')
def agent_status():
    return {'agents':agent.status(),'poll_interval_ms':500}

@app.post('/api/forecast/recalculate',response_model=ForecastResponse)
def recalculate(request: RecalculateRequest):
    override=None
    if request.weather is not None:
        records=[p.model_dump() for p in request.weather]
        frame=pd.DataFrame(records)
        frame['timestamp']=pd.to_datetime(frame.timestamp,utc=True)
        override=WeatherResult(frame.set_index('timestamp'),{'source':'user_supplied_forecast',
            'issued_at':request.weather_issued_at.isoformat(),'is_fallback':False,
            'provenance':'Caller declares issue time; authenticity is not independently verified'})
    return agent.run(request.turbine_id,request.hours,request.mode,request.forecast_origin,override)

@app.get('/api/turbines/{turbine_id}/details')
def details(turbine_id: str,hours: int=Query(48,ge=24,le=48,json_schema_extra={"enum":[24,48]}),mode: Optional[Literal['replay','live']]=None):
    cfg=known(turbine_id)
    result=agent.run(turbine_id,hours,mode)
    history=read_hourly(turbine_id)
    history=history.loc[history.index<pd.Timestamp(result['forecast_origin'])].dropna(subset=['power','wind_speed','temperature'])
    current=None
    if not history.empty:
        row=history.iloc[-1]
        current={'timestamp':history.index[-1].isoformat(),'power':float(row.power),
            'wind_speed':float(row.wind_speed),'temperature':float(row.temperature),
            'is_live':False,'source':'latest_available_SCADA','age_hours':result['history_age_hours']}
    validation=artifact('metrics.json')
    model_metrics=validation['turbines'][turbine_id]['model']
    return {**cfg,'current':current,'forecast_origin':result['forecast_origin'],'generated_at':result['generated_at'],
        'mode':result['mode'],'forecast_summary':result['forecast_summary'],'forecast':result['forecast'],
        'weather':result['weather'],'model':{**result['model'],**model_metrics,
            'metrics_period':'January 2026','metrics_model':'frozen evaluation model (trained before December), not deployment refit'},
        'agent':result['agent'],'warnings':result['warnings']}
