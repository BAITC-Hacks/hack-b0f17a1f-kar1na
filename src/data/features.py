"""Direct multi-horizon features. History is sliced strictly before origin.
All lags/rolling windows refer to origin, NOT the future target timestamp.
"""
import numpy as np
import pandas as pd
from src.config import LOCAL_TZ, utc

POWER_LAGS = (1, 3, 6, 12, 24)
WIND_LAGS = (1, 3, 6, 24)
WINDOWS = (3, 6, 12, 24)
HISTORY_FEATURES = ([f'power_lag_{n}' for n in POWER_LAGS] + [f'wind_lag_{n}' for n in WIND_LAGS]
    + [f'rolling_{col}_{stat}_{w}' for col in ('wind', 'power') for w in WINDOWS for stat in ('mean', 'std')])

def history_features(history: pd.DataFrame, origin) -> dict:
    origin = utc(origin)
    # Complete hour required: t+1h <= origin. Nothing at/after origin can be used.
    past = history.loc[history.index < origin]
    idx = pd.date_range(origin-pd.Timedelta(hours=24), periods=24, freq='h')
    window = past.reindex(idx)
    values = {}
    for col, lags in [('power', POWER_LAGS), ('wind_speed', WIND_LAGS)]:
        name = 'wind' if col == 'wind_speed' else col
        for n in lags:
            values[f'{name}_lag_{n}'] = window[col].iloc[-n]
        for w in WINDOWS:
            s = window[col].iloc[-w:]
            # At least half the window must be actually observed.
            ok = s.count() >= max(2, int(np.ceil(w/2)))
            values[f'rolling_{name}_mean_{w}'] = s.mean() if ok else np.nan
            values[f'rolling_{name}_std_{w}'] = s.std() if ok else np.nan
    return values

def make_features(history: pd.DataFrame, origin, weather: pd.DataFrame) -> pd.DataFrame:
    origin = utc(origin)
    times = pd.DatetimeIndex(weather.index)
    if times.tz is None or (times < origin).any() or (times >= origin + pd.Timedelta(hours=48)).any():
        raise ValueError('Feature targets must be timezone-aware and inside [origin, origin+48h)')
    local = times.tz_convert(LOCAL_TZ)
    x = weather[['wind_speed', 'temperature']].astype(float).copy()
    x['hour'] = local.hour
    x['day_of_week'] = local.dayofweek
    x['month'] = local.month
    x['day_of_year'] = local.dayofyear
    for col, period in [('hour', 24), ('month', 12), ('day_of_year', 365.25)]:
        x[f'{col}_sin'] = np.sin(2*np.pi*x[col]/period)
        x[f'{col}_cos'] = np.cos(2*np.pi*x[col]/period)
    x['horizon'] = (times-origin).total_seconds()/3600 + 1
    for col, value in history_features(history, origin).items():
        x[col] = value
    return x
