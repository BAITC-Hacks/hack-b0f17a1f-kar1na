"""Direct multi-horizon learning from forecast weather, not future observations."""
import logging
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from src.config import TURBINES, MODELS, SEED, local_date
from src.data.features import make_features, HISTORY_FEATURES
from src.data.preprocessing import read_hourly
from src.services.weather_provider import OpenMeteoProvider

LOG = logging.getLogger(__name__)
TRAIN_END = local_date('2025-12-01')
CALIBRATION_END = local_date('2026-01-01')
MODEL_END = local_date('2026-02-01')

def supervised_dataset(history, forecast_weather, start, end):
    xs, ys, origins = [], [], []
    for origin in pd.date_range(start, end-pd.Timedelta(days=1), freq='D'):
        times = pd.date_range(origin, periods=48, freq='h')
        weather = forecast_weather.reindex(times)
        x = make_features(history,origin,weather)
        y = history.power.reindex(times)
        # Purge samples whose target interval ends beyond cutoff.
        valid = y.notna() & np.isfinite(weather).all(axis=1) & (times < end)
        xs.append(x.loc[valid]); ys.append(y.loc[valid]); origins.extend([origin]*int(valid.sum()))
    if not xs or sum(map(len,xs)) == 0:
        raise ValueError('No usable training samples: check input dates and archived weather')
    return pd.concat(xs),pd.concat(ys),pd.DatetimeIndex(origins)

def fit_estimator(x,y):
    # Add missing-history cases so live forecasts can work honestly without fresh SCADA.
    # Exact past lags are never carried forward across long outages.
    augmented=x.iloc[::4].copy()
    augmented[HISTORY_FEATURES]=np.nan
    xx=pd.concat([x,augmented],ignore_index=True)
    yy=np.concatenate([y.to_numpy(),y.iloc[::4].to_numpy()])
    estimator=HistGradientBoostingRegressor(max_iter=180, max_leaf_nodes=15,
        learning_rate=.06, l2_regularization=8, min_samples_leaf=40,
        early_stopping=False, random_state=SEED)
    # Disable default random early-stopping split; no random time-series split anywhere.
    with threadpool_limits(limits=2):
        estimator.fit(xx,yy)
    return estimator

def fit_turbine(turbine_id, provider=None):
    history=read_hourly(turbine_id)
    provider=provider or OpenMeteoProvider()
    cfg=TURBINES[turbine_id]
    start=local_date('2024-01-02')
    weather=provider.archive_range(cfg['latitude'],cfg['longitude'],start,MODEL_END)
    x,y,_=supervised_dataset(history,weather,start,TRAIN_END)
    model=fit_estimator(x,y)
    cx,cy,_=supervised_dataset(history,weather,TRAIN_END,CALIBRATION_END)
    with threadpool_limits(limits=2):
        residual=np.abs(cy.to_numpy()-np.clip(model.predict(cx),0,1))
    radii={}
    for label,mask in [('1_24',cx.horizon.to_numpy()<=24),('25_48',cx.horizon.to_numpy()>24)]:
        # Conservative finite-sample conformal quantile. Temporal dependence prevents a coverage guarantee.
        n=int(mask.sum()); q=min(1,np.ceil((n+1)*.9)/n)
        radii[label]=float(np.quantile(residual[mask],q,method='higher'))
    common={'turbine_id':turbine_id,'feature_names':list(x.columns),'interval_radius':radii,
        'interval_nominal_coverage':.9,'interval_method':'December holdout absolute residual quantiles by lead bucket; empirical, not guaranteed',
        'seed':SEED,'training_start':start.isoformat(),'calibration_start':TRAIN_END.isoformat(),
        'calibration_end_exclusive':CALIBRATION_END.isoformat(),
        'weather_source':'GFS Previous Runs, 72h fixed lead, 80m wind',
        'model_type':'HistGradientBoostingRegressor, direct 1..48h',
        'training_rows':len(x),'calibration_rows':len(cx),
        'created_at':pd.Timestamp.now(tz='UTC').isoformat()}
    MODELS.mkdir(parents=True,exist_ok=True)
    evaluation={**common,'estimator':model,'trained_until':TRAIN_END.isoformat(),
                'usage':'Frozen January evaluation model; December calibrates intervals only'}
    joblib.dump(evaluation,MODELS/f'{turbine_id}_evaluation.joblib')
    # Refit for deployment using all labels before February; January metrics refer to evaluation model.
    dx,dy,_=supervised_dataset(history,weather,start,MODEL_END)
    deployed={**common,'estimator':fit_estimator(dx,dy),'trained_until':MODEL_END.isoformat(),
              'training_rows':len(dx),'usage':'February/live deployment model; holdout interval radius transferred from earlier model'}
    joblib.dump(deployed,MODELS/f'{turbine_id}.joblib')
    LOG.info('%s trained: evaluation=%d deployment=%d calibration=%d',turbine_id,len(x),len(dx),len(cx))
    return {k:v for k,v in deployed.items() if k!='estimator'}
