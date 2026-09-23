import logging
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from src.config import TURBINES, MODELS, LOCAL_TZ, RESULTS, local_date
from src.data.preprocessing import read_hourly
from src.models.predict import predict
from src.models.evaluate import summarize
from src.services.weather_provider import OpenMeteoProvider
from src.utils import write_json

LOG=logging.getLogger(__name__)

def run_backtest(start='2026-02-01',end='2026-03-01',evaluation=False,hours=48):
    """Daily rolling origins, frozen weights. New actual history only if genuinely present.
    End is exclusive for scoring, but all issued 48h trajectories are retained.
    """
    provider=OpenMeteoProvider()
    start_ts,end_ts=local_date(start),local_date(end)
    rows=[]
    for turbine,cfg in TURBINES.items():
        history=read_hourly(turbine)
        suffix='_evaluation' if evaluation else ''
        bundle=joblib.load(MODELS/f'{turbine}{suffix}.joblib')
        for origin in pd.date_range(start_ts,end_ts-pd.Timedelta(days=1),freq='D'):
            weather=provider.get_forecast(cfg['latitude'],cfg['longitude'],origin,hours)
            past=history.loc[history.index<origin]
            prediction,_=predict(bundle,past,origin,weather.frame)
            valid_past=past.power.dropna()
            baseline=float(valid_past.iloc[-1]) if len(valid_past) else np.nan
            last_time=valid_past.index[-1] if len(valid_past) else None
            for h,(ts,row) in enumerate(prediction.iterrows(),start=1):
                in_period=start_ts<=ts<end_ts
                actual=history.power.get(ts,np.nan) if in_period else np.nan
                rows.append({'forecast_origin':origin.isoformat(),'target_timestamp':ts.isoformat(),
                    'turbine_id':turbine,'horizon':h,'predicted_power':row.predicted_power,
                    'actual_power':actual,'error':row.predicted_power-actual,'baseline_power':baseline,
                    'wind_speed':row.wind_speed,'temperature':row.temperature,
                    'lower_power':row.lower_power,'upper_power':row.upper_power,
                    'in_evaluation_period':in_period,'weather_source':weather.metadata['source'],
                    'weather_lead_hours':72,'weather_availability_bound':(ts-pd.Timedelta(hours=60)).isoformat(),
                    'history_latest_timestamp':last_time.isoformat() if last_time is not None else None,
                    'history_age_hours':(origin-last_time-pd.Timedelta(hours=1)).total_seconds()/3600 if last_time is not None else None,
                    'model_trained_until':bundle['trained_until']})
        LOG.info('%s replay complete: %s through %s',turbine,start,end)
    frame=pd.DataFrame(rows)
    prefix='validation' if evaluation else 'backtest'
    RESULTS.mkdir(parents=True,exist_ok=True)
    frame.to_csv(RESULTS/f'{prefix}_predictions.csv',index=False)
    scored=frame[frame.in_evaluation_period]
    summary={'period_start':start,'period_end_exclusive':end,'timezone':'UTC+05:00',
        'horizon_hours':hours,'origin_frequency':'daily at local 00:00; preceding day closing boundary',
        'weather_policy':'Operational GFS forecasts at 72h fixed lead; 12h publication allowance; no future observations',
        'model_policy':'frozen weights; only observed complete past hours enter lags',
        'metrics_weighting':'all origin-target pairs (overlapping horizons counted separately)',
        'unscored_outside_period':int((~frame.in_evaluation_period).sum()),
        'turbines':summarize(scored)}
    write_json(RESULTS/f'{prefix}_metrics.json',summary)
    return summary
