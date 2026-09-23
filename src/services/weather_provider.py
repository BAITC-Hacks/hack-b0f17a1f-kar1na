"""Weather forecasts, never reanalysis/observations masquerading as forecasts.

The operational Previous Runs GFS archive uses fixed 72h lead weather.
For targets [origin, origin+48h), its forecast reference time is <=origin-25h.
We conservatively allow a further 12h publication delay. This is a bound,
NOT a claim that the API supplies exact issue/publication timestamps.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
import hashlib
import json
import logging
import os
import time
import httpx
import numpy as np
import pandas as pd
from src.config import WEATHER_CACHE, utc
from src.utils import write_json

LOG = logging.getLogger(__name__)
ARCHIVE_URL = 'https://previous-runs-api.open-meteo.com/v1/forecast'
LIVE_URL = 'https://api.open-meteo.com/v1/forecast'
MODEL = 'gfs_global'
WIND_VARIABLE = 'wind_speed_80m'

class WeatherError(RuntimeError):
    pass

@dataclass
class WeatherResult:
    frame: pd.DataFrame
    metadata: dict

class WeatherProvider(Protocol):
    def get_forecast(self, latitude: float, longitude: float, forecast_origin, horizon_hours: int) -> WeatherResult:
        ...

def target_index(origin, hours: int) -> pd.DatetimeIndex:
    if hours not in (24, 48):
        raise ValueError('horizon_hours must be 24 or 48')
    origin = utc(origin)
    if origin != origin.floor('h'):
        raise ValueError('forecast_origin must be aligned to an hour')
    return pd.date_range(origin, periods=hours, freq='h', name='timestamp')

def validate_weather(frame: pd.DataFrame, origin, hours: int) -> None:
    expected = target_index(origin, hours)
    if not frame.index.equals(expected):
        raise WeatherError('Weather timestamps must exactly cover the requested hourly horizon')
    if not {'wind_speed', 'temperature'}.issubset(frame.columns):
        raise WeatherError('Weather is missing wind_speed/temperature')
    if not np.isfinite(frame[['wind_speed', 'temperature']].to_numpy()).all():
        raise WeatherError('Weather has missing or non-finite values')
    if not frame.wind_speed.between(0, 75).all() or not frame.temperature.between(-80, 60).all():
        raise WeatherError('Weather violates physical bounds (wind 0..75 m/s; temperature -80..60 C)')

class OpenMeteoProvider:
    def __init__(self, mode: str = 'archive', cache_dir: Path = WEATHER_CACHE, offline=None):
        if mode not in ('archive', 'live'):
            raise ValueError('mode must be archive or live')
        self.mode = mode
        self.cache_dir = Path(cache_dir)
        self.offline = (os.getenv('WEATHER_OFFLINE', 'false').lower() == 'true') if offline is None else offline
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory = {}
        self._provenance = {}

    def _fetch(self, params: dict, url: str, live=False) -> dict:
        key = hashlib.sha256(json.dumps([url, params], sort_keys=True).encode()).hexdigest()
        path = self.cache_dir / f'{key}.json'
        # Archive is immutable for reproducibility. Live cache expires after 30 min.
        if path.exists() and (not live or time.time()-path.stat().st_mtime < 1800):
            return json.loads(path.read_text())
        if self.offline:
            raise WeatherError(f'Offline cache miss: {path.name}')
        last = None
        for attempt in range(3):
            try:
                response = httpx.get(url, params=params, timeout=35)
                response.raise_for_status()
                data = response.json()
                if data.get('error'):
                    raise WeatherError(str(data.get('reason')))
                package = {'url': str(response.url), 'retrieved_at': pd.Timestamp.now(tz='UTC').isoformat(),
                           'params': params, 'response': data}
                write_json(path, package)
                return package
            except (httpx.HTTPError, ValueError, WeatherError) as exc:
                last = exc
                LOG.warning('Weather request attempt %d failed: %s', attempt+1, exc)
                if attempt < 2:
                    time.sleep(.5 * 2**attempt)
        raise WeatherError(f'Open-Meteo unavailable after 3 attempts: {last}')

    @staticmethod
    def _frame(package: dict, suffix: str) -> pd.DataFrame:
        try:
            hourly = package['response']['hourly']
            frame = pd.DataFrame({'wind_speed': hourly[WIND_VARIABLE+suffix],
                                  'temperature': hourly['temperature_2m'+suffix]},
                                 index=pd.to_datetime(hourly['time'], utc=True), dtype=float)
            frame.index.name = 'timestamp'
            return frame
        except (KeyError, ValueError) as exc:
            raise WeatherError(f'Malformed weather API response: {exc}') from exc

    def archive_range(self, latitude: float, longitude: float, start, end) -> pd.DataFrame:
        """Monthly cached requests; end exclusive. Also used to train on forecast inputs."""
        start, end = utc(start), utc(end)
        pieces = []
        first = pd.Timestamp(year=start.year, month=start.month, day=1, tz='UTC')
        for month in pd.date_range(first, end, freq='MS'):
            if month >= end:
                break
            key = (latitude, longitude, month.isoformat())
            if key not in self._memory:
                last = month + pd.offsets.MonthEnd(0)
                params = {'latitude': latitude, 'longitude': longitude, 'models': MODEL,
                          'hourly': f'temperature_2m_previous_day3,{WIND_VARIABLE}_previous_day3',
                          'start_date': month.strftime('%Y-%m-%d'), 'end_date': last.strftime('%Y-%m-%d'),
                          'wind_speed_unit': 'ms', 'timezone': 'UTC'}
                package = self._fetch(params, ARCHIVE_URL)
                self._memory[key] = self._frame(package, '_previous_day3')
                self._provenance[key] = {'request_url': package['url'], 'retrieved_at': package['retrieved_at'],
                    'response_sha256': hashlib.sha256(json.dumps(package['response'], sort_keys=True).encode()).hexdigest()}
            pieces.append(self._memory[key])
        if not pieces:
            raise WeatherError('Empty archive interval')
        frame = pd.concat(pieces).sort_index()
        return frame.loc[(frame.index >= start) & (frame.index < end)]

    def get_forecast(self, latitude: float, longitude: float, forecast_origin, horizon_hours: int) -> WeatherResult:
        origin = utc(forecast_origin)
        times = target_index(origin, horizon_hours)
        if self.mode == 'archive':
            frame = self.archive_range(latitude, longitude, times[0], times[-1]+pd.Timedelta(hours=1)).reindex(times)
            # Fixed-lead timestamp is a conservative availability bound, not an exact model run.
            available_bound = times[-1] - pd.Timedelta(hours=72) + pd.Timedelta(hours=12)
            if available_bound > origin:
                raise WeatherError('Archive weather could have been published after forecast origin')
            metadata = {'source': 'open_meteo_previous_runs', 'model': MODEL,
                        'forecast_lead_hours': 72, 'publication_delay_allowance_hours': 12,
                        'latest_availability_bound': available_bound.isoformat(),
                        'availability_basis': 'fixed lead API semantics; exact publication time not supplied',
                        'exact_run_id': None, 'is_fallback': False}
            metadata['archive_requests'] = [receipt for key,receipt in self._provenance.items()
                if key[0]==latitude and key[1]==longitude
                and pd.Timestamp(key[2])<=times[-1]
                and pd.Timestamp(key[2])+pd.offsets.MonthBegin(1)>times[0]]
        else:
            now = pd.Timestamp.now(tz='UTC')
            if origin < now.floor('h') or origin > now.ceil('h'):
                raise WeatherError('Live provider is only allowed at the current/next hour; use archive for replay')
            params = {'latitude': latitude, 'longitude': longitude, 'models': MODEL,
                      'hourly': f'temperature_2m,{WIND_VARIABLE}', 'forecast_days': 4,
                      'wind_speed_unit': 'ms', 'timezone': 'UTC'}
            package = self._fetch(params, LIVE_URL, live=True)
            frame = self._frame(package, '').reindex(times)
            metadata = {'source': 'open_meteo_live', 'model': MODEL, 'is_fallback': False,
                        'retrieved_at': package['retrieved_at'], 'exact_run_id': None}
        validate_weather(frame, origin, horizon_hours)
        metadata.update({'wind_height_m': 80, 'temperature_height_m': 2,
                         'requested_latitude': latitude, 'requested_longitude': longitude,
                         'wind_unit': 'm/s', 'temperature_unit': 'C',
                         'reference': 'https://open-meteo.com/en/docs/previous-runs-api' if self.mode=='archive' else 'https://open-meteo.com/en/docs'})
        return WeatherResult(frame, metadata)

class PersistenceWeatherProvider:
    """Explicit offline emergency forecast, using ONLY observed history before origin.
    Refuses >24h stale telemetry. It is not an archived meteorological forecast.
    """
    def __init__(self, history: pd.DataFrame):
        self.history = history

    def get_forecast(self, latitude, longitude, forecast_origin, horizon_hours):
        origin = utc(forecast_origin)
        past = self.history.loc[self.history.index < origin, ['wind_speed', 'temperature']].dropna()
        if past.empty or origin-(past.index[-1]+pd.Timedelta(hours=1)) > pd.Timedelta(hours=24):
            raise WeatherError('Persistence fallback requires weather observations no older than 24h')
        frame = pd.DataFrame({c: past[c].iloc[-1] for c in past.columns}, index=target_index(origin, horizon_hours))
        validate_weather(frame, origin, horizon_hours)
        return WeatherResult(frame, {'source': 'observed_weather_persistence', 'is_fallback': True,
                                     'observation_timestamp': past.index[-1].isoformat(),
                                     'warning': 'No NWP forecast available; constant last observed weather'})
