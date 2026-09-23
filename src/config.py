"""Central configuration. Every internal timestamp is timezone-aware UTC."""
from datetime import timedelta, timezone
from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
LOCAL_TZ = timezone(timedelta(hours=int(os.getenv('DATA_UTC_OFFSET_HOURS', '5'))))
DISPLAY_TIMEZONE = 'Asia/Almaty'  # IANA zone used for Astana; UTC+05 in 2026.
TIMEZONE_LABEL = 'Астана · UTC+05:00'
RAW = ROOT / 'data/raw'
PROCESSED = ROOT / 'data/processed'
MODELS = ROOT / 'models'
RESULTS = ROOT / 'results'
WEATHER_CACHE = ROOT / 'data/weather'
SEED = 42
TURBINES = {
    f'turbine_{i}': {
        'id': f'turbine_{i}', 'name': f'Turbine {i}',
        'latitude': float(os.getenv(f'TURBINE_{i}_LATITUDE', str(lat))),
        'longitude': float(os.getenv(f'TURBINE_{i}_LONGITUDE', str(lon))),
        'power_unit': 'normalized', 'power_range': [0.0, 1.0],
        'rated_power_kw': None, 'hub_height_m': None,
        'coordinate_source': url,
    }
    for i, lat, lon, url in [
        (1, 43.645150, 78.535604, 'https://maps.app.goo.gl/iN6svMt69D5qRpFU9'),
        (2, 43.643198, 78.538828, 'https://maps.app.goo.gl/8UQMwsYavY6nLvFY8'),
    ]
}

def utc(value):
    import pandas as pd
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        raise ValueError('Timestamp must include a timezone offset')
    return ts.tz_convert('UTC')

def local_date(value: str):
    import pandas as pd
    return pd.Timestamp(value).tz_localize(LOCAL_TZ).tz_convert('UTC')
