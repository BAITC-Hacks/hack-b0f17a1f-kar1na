"""Strict loader for the inspected UTF-8, comma-separated SCADA exports."""
from pathlib import Path
import csv
import hashlib
import pandas as pd
from src.config import LOCAL_TZ, RAW, TURBINES

COLUMNS = {
    'Статистическое время': 'timestamp',
    'Средняя скорость ветра(m/s)': 'wind_speed',
    'Нормализованная активная мощность': 'power',
    'Средняя температура окружающей среды(°C)': 'temperature',
}
NUMERIC = ['wind_speed', 'power', 'temperature']

def load_csv(path: Path):
    raw = Path(path).read_bytes()
    text = raw.decode('utf-8-sig', errors='strict')
    separator = csv.Sniffer().sniff(text[:8192], delimiters=',;\t').delimiter
    df = pd.read_csv(path, encoding='utf-8-sig', sep=separator)
    if not set(COLUMNS).issubset(df.columns):
        raise ValueError(f'{path}: expected columns {list(COLUMNS)}, got {list(df.columns)}')
    source_columns = list(df.columns)
    source_dtypes = df.dtypes.astype(str).to_dict()
    df = df.rename(columns=COLUMNS)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S', errors='raise')
    df['timestamp'] = df.timestamp.dt.tz_localize(LOCAL_TZ).dt.tz_convert('UTC')
    invalid = {}
    for col in NUMERIC:
        original = df[col]
        df[col] = pd.to_numeric(original, errors='coerce')
        invalid[col] = int((original.notna() & df[col].isna()).sum())
    report = {
        'file': str(path), 'sha256': hashlib.sha256(raw).hexdigest(),
        'encoding': 'UTF-8 (no BOM)' if not raw.startswith(b'\xef\xbb\xbf') else 'UTF-8 BOM',
        'separator': separator, 'source_columns': source_columns, 'source_dtypes': source_dtypes,
        'rows': len(df), 'date_start': df.timestamp.min(), 'date_end': df.timestamp.max(),
        'nulls': df[['timestamp'] + NUMERIC].isna().sum().to_dict(),
        'invalid_numeric_cells': invalid,
        'duplicate_rows': int(df.duplicated().sum()),
        'duplicate_timestamps': int(df.timestamp.duplicated().sum()),
        'out_of_order': int((df.timestamp.diff().dt.total_seconds() < 0).sum()),
        'interval_seconds': df.timestamp.sort_values().diff().dt.total_seconds().value_counts().to_dict(),
        'statistics': df[NUMERIC].describe(percentiles=[.01,.05,.25,.5,.75,.95,.99]).to_dict(),
        'correlations': df[NUMERIC].corr().to_dict(),
        'zero_power_rows': int(df.power.eq(0).sum()),
        'high_wind_low_power_rows': int(((df.wind_speed > 8) & (df.power < .05)).sum()),
    }
    return df, report

def load_turbine(turbine_id: str):
    if turbine_id not in TURBINES:
        raise ValueError(f'Unknown turbine: {turbine_id}')
    return load_csv(RAW / f'{turbine_id}.csv')
