"""Hourly interval-start labels. A row at t is available only at t+1h.
Missing targets are NEVER imputed. No interpolation from future rows.
"""
import numpy as np
import pandas as pd
from src.config import PROCESSED
from src.data.loader import NUMERIC, load_turbine

BOUNDS = {'power': (0, 1), 'wind_speed': (0, 75), 'temperature': (-80, 60)}

def preprocess(df: pd.DataFrame):
    data = df[['timestamp'] + NUMERIC].copy().sort_values('timestamp')
    audit = {'policy': 'Invalid cells -> NaN; duplicate timestamps averaged; hourly mean requires >=4/6 valid samples; no target imputation.'}
    for col, (low, high) in BOUNDS.items():
        bad = data[col].notna() & (~np.isfinite(data[col]) | ~data[col].between(low, high))
        audit[f'invalid_{col}'] = int(bad.sum())
        data.loc[bad, col] = np.nan
    # Duplicates count as a single 10-minute sample; retain conflicting values by averaging.
    data = data.groupby('timestamp')[NUMERIC].mean().sort_index()
    expected = pd.date_range(data.index.min(), data.index.max(), freq='10min')
    audit['missing_10min_timestamps'] = len(expected.difference(data.index))
    off_grid = ((data.index.minute % 10) != 0) | (data.index.second != 0)
    if off_grid.any():
        raise ValueError('Input includes timestamps off the inspected 10-minute grid')
    hourly = data.resample('h').mean()
    counts = data.resample('h').count()
    for col in NUMERIC:
        hourly[col] = hourly[col].where(counts[col] >= 4)
        hourly[f'{col}_samples'] = counts[col]
    hourly.index.name = 'timestamp'
    audit.update({'hourly_rows': len(hourly), 'hourly_missing': hourly[NUMERIC].isna().sum().to_dict(),
                  'incomplete_hours': int((counts.min(axis=1) < 6).sum()),
                  'fully_missing_hours': int((counts.max(axis=1) == 0).sum()),
                  'longest_raw_gap_hours': float(data.index.to_series().diff().max().total_seconds()/3600)})
    return hourly, audit

def prepare_turbine(turbine_id: str):
    raw, report = load_turbine(turbine_id)
    hourly, audit = preprocess(raw)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    hourly.to_csv(PROCESSED / f'{turbine_id}_hourly.csv')
    report['preprocessing'] = audit
    return hourly, report

def read_hourly(turbine_id: str) -> pd.DataFrame:
    path = PROCESSED / f'{turbine_id}_hourly.csv'
    if not path.exists():
        raise FileNotFoundError('Processed data missing. Run python scripts/analyze_data.py')
    df = pd.read_csv(path)
    df['timestamp'] = pd.to_datetime(df.timestamp, utc=True)
    return df.set_index('timestamp')
