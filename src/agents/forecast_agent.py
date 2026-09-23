"""Deterministic tool-using forecast agent with observable state and recovery.
No LLM/key required: the agent makes data-dependent retry/fallback/staleness decisions.
"""
import copy
import hashlib
import json
import logging
import os
import threading
import uuid
from typing import Optional
import numpy as np
import pandas as pd
from src.config import TURBINES, RESULTS, MODELS, TIMEZONE_LABEL, utc
from src.agents.assessment import assess_forecast, compare_forecasts
from src.data.preprocessing import read_hourly
from src.data.features import make_features, HISTORY_FEATURES
from src.models.predict import load_model, predict
from src.services.weather_provider import (OpenMeteoProvider, PersistenceWeatherProvider,
    WeatherResult, WeatherError, validate_weather)
from src.utils import clean_json, write_json

LOG=logging.getLogger(__name__)
STATES=['FETCHING_WEATHER','VALIDATING_DATA','PREPARING_FEATURES','RUNNING_MODEL','VALIDATING_FORECAST','COMPLETED','FAILED']

class AgentBusyError(RuntimeError): pass

class ForecastAgent:
    def __init__(self, result_dir=None):
        self.result_dir=result_dir or RESULTS/'forecasts'
        self._state_lock=threading.RLock()
        self._run_locks={t:threading.Lock() for t in TURBINES}
        self._status={t:{'turbine_id':t,'status':'IDLE','steps':[],'last_update':None} for t in TURBINES}

    def status(self, turbine_id=None):
        with self._state_lock:
            return copy.deepcopy(self._status[turbine_id] if turbine_id else self._status)

    def _step(self,turbine,state,message):
        now=pd.Timestamp.now(tz='UTC').isoformat()
        with self._state_lock:
            status=self._status[turbine]
            status.update(status=state,last_update=now)
            status['steps'].append({'state':state,'timestamp':now,'message':message})
        LOG.info('%s %s %s',turbine,state,message)

    def run(self,turbine_id: str,hours: int=48,mode: Optional[str]=None,origin=None,
            weather_override: Optional[WeatherResult]=None,provider=None) -> dict:
        if turbine_id not in TURBINES:
            raise ValueError(f'Unknown turbine: {turbine_id}')
        if hours not in (24,48): raise ValueError('hours must be 24 or 48')
        mode=mode or os.getenv('FORECAST_MODE','replay')
        if mode not in ('replay','live'): raise ValueError('mode must be replay or live')
        if origin is None:
            origin=pd.Timestamp.now(tz='UTC').ceil('h') if mode=='live' else utc(os.getenv('REPLAY_ORIGIN','2026-02-01T00:00:00+05:00'))
        origin=utc(origin)
        if origin!=origin.floor('h'): raise ValueError('origin must be aligned to an hour')
        if mode=='replay' and origin>pd.Timestamp.now(tz='UTC'):
            raise ValueError('Replay origin cannot be in the future')
        lock=self._run_locks[turbine_id]
        if not lock.acquire(blocking=False): raise AgentBusyError(f'{turbine_id}: forecast already running')
        run_id=uuid.uuid4().hex
        with self._state_lock:
            self._status[turbine_id]={'turbine_id':turbine_id,'run_id':run_id,'status':'IDLE','steps':[],
                'forecast_origin':origin.isoformat(),'horizon_hours':hours,'mode':mode,'last_update':None}
        try:
            cfg=TURBINES[turbine_id]
            warnings=[]
            self._step(turbine_id,'FETCHING_WEATHER','Resolve configuration, obtain forecast; retry up to 3 times')
            history=read_hourly(turbine_id)
            history=history.loc[history.index<origin]
            if weather_override is not None:
                weather=weather_override
                issued=utc(weather.metadata['issued_at'])
                if issued>origin: raise WeatherError('Custom weather was issued after forecast origin')
            else:
                provider=provider or OpenMeteoProvider('live' if mode=='live' else 'archive')
                try:
                    weather=provider.get_forecast(cfg['latitude'],cfg['longitude'],origin,hours)
                except WeatherError as exc:
                    if os.getenv('WEATHER_ALLOW_FALLBACK','true').lower()!='true': raise
                    self._step(turbine_id,'FETCHING_WEATHER',f'NWP unavailable: {exc}; try explicit persistence fallback')
                    weather=PersistenceWeatherProvider(history).get_forecast(cfg['latitude'],cfg['longitude'],origin,hours)
                    warnings.append(f'Weather fallback: {exc}')
            self._step(turbine_id,'VALIDATING_DATA','Check hourly coverage, units, finite values and physical bounds')
            validate_weather(weather.frame,origin,hours)
            # Validate causality for every provider, including injected integrations.
            bound=weather.metadata.get('latest_availability_bound') or weather.metadata.get('issued_at')
            if mode=='replay' and not weather.metadata.get('is_fallback'):
                if bound is None or utc(bound)>origin:
                    raise WeatherError('Replay weather requires an availability bound at/before origin')
            observed=history.dropna(subset=['power','wind_speed','temperature'])
            latest=observed.index[-1] if len(observed) else None
            age=(origin-latest-pd.Timedelta(hours=1)).total_seconds()/3600 if latest is not None else None
            if age is None or age>1:
                warnings.append(f'SCADA is stale: {age} hours. Missing origin lags remain missing; no invented telemetry.')
            if mode=='live':
                warnings.append('Live weather has newer lead times than the 72h archive used for training; live skill is not validated.')
            if weather.metadata.get('is_fallback'):
                warnings.append('Prediction intervals are not calibrated for weather persistence fallback.')
            self._step(turbine_id,'PREPARING_FEATURES','Build origin-relative lags, past rolling windows and target calendar features')
            features=make_features(history,origin,weather.frame)
            if features[HISTORY_FEATURES].isna().all(axis=None):
                warnings.append('No recent SCADA features; model uses weather/calendar only. Interval coverage in this regime is unverified.')
            bundle=load_model(turbine_id)
            self._step(turbine_id,'RUNNING_MODEL',f"Run {bundle['model_type']} ({hours} hours)")
            forecast,checks=predict(bundle,history,origin,weather.frame)
            self._step(turbine_id,'VALIDATING_FORECAST',f'Check complete horizon and normalized bounds: {checks}')
            if checks['suspicious_jumps']:
                warnings.append(f"{checks['suspicious_jumps']} hourly jumps exceed 0.6; flagged without smoothing")
            if len(forecast)!=hours or not np.isfinite(forecast.to_numpy()).all():
                raise ValueError('Forecast failed horizon/finite-value validation')
            fingerprint=hashlib.sha256(weather.frame.to_csv().encode()).hexdigest()
            model_hash=hashlib.sha256((MODELS/f'{turbine_id}.joblib').read_bytes()).hexdigest()
            history_hash=hashlib.sha256(history.tail(24).to_csv().encode()).hexdigest()
            provenance={k:v for k,v in weather.metadata.items() if k!='retrieved_at'}
            input_hash=hashlib.sha256(f'{fingerprint}:{model_hash}:{history_hash}:{origin}:{hours}:{mode}:{json.dumps(provenance,sort_keys=True)}'.encode()).hexdigest()
            previous=None
            # Keep independent revision chains for each origin, mode and horizon.
            context_key=hashlib.sha256(f'{turbine_id}:{origin}:{hours}:{mode}'.encode()).hexdigest()[:20]
            context_path=self.result_dir/f'{turbine_id}_context_{context_key}.json'
            if context_path.exists():
                previous=json.loads(context_path.read_text())
            rows=[{'timestamp':ts.isoformat(),**r.to_dict()} for ts,r in forecast.iterrows()]
            peak=forecast.predicted_power.idxmax()
            payload={'turbine_id':turbine_id,'run_id':run_id,'generated_at':pd.Timestamp.now(tz='UTC').isoformat(),
                'forecast_origin':origin.isoformat(),'horizon_hours':hours,'mode':mode,
                'display_timezone':TIMEZONE_LABEL,'input_sha256':input_hash,
                'power_unit':'normalized','timestamp_convention':'UTC interval start; each point covers one hour',
                'forecast':rows,'weather':{**weather.metadata,'input_sha256':fingerprint},
                'forecast_summary':{'next_24h_average':float(forecast.predicted_power.iloc[:24].mean()),
                    'next_24h_peak':float(forecast.predicted_power.iloc[:24].max()),
                    'peak_time':peak.isoformat(),'horizon_peak':float(forecast.predicted_power.max())},
                'model':{k:bundle[k] for k in ['model_type','trained_until','interval_method','interval_nominal_coverage']},
                'history_latest_timestamp':latest.isoformat() if latest is not None else None,
                'history_age_hours':age,'sanity_checks':checks,'warnings':warnings,
                'agent':self.status(turbine_id)}
            payload['model']['sha256']=model_hash
            payload['revision']=compare_forecasts(previous,payload)
            payload['assessment']=assess_forecast(payload)
            if previous and previous.get('input_sha256')==input_hash:
                self._step(turbine_id,'COMPLETED','Inputs unchanged; reuse the validated forecast version')
                previous['agent']=self.status(turbine_id)
                previous['unchanged']=True
                previous['agent']['run_id']=previous['run_id']
                with self._state_lock:
                    self._status[turbine_id]['run_id']=previous['run_id']
                return clean_json(previous)
            # Validate response before marking complete or publishing a result.
            from src.api.schemas import ForecastResponse
            ForecastResponse.model_validate(payload)
            path=self.result_dir/f'{turbine_id}_{run_id}.json'
            write_json(path,payload)
            self._step(turbine_id,'COMPLETED','Forecast validated and saved; frontend JSON ready')
            payload['agent']=self.status(turbine_id)
            write_json(path,payload)
            write_json(self.result_dir/f'{turbine_id}_latest.json',payload)
            write_json(context_path,payload)
            return clean_json(payload)
        except Exception as exc:
            self._step(turbine_id,'FAILED',str(exc))
            LOG.exception('Forecast failed for %s',turbine_id)
            raise
        finally:
            lock.release()
