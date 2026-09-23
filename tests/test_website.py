"""Contract checks for the integrated dashboard's daily history endpoint."""
import pandas as pd
from fastapi.testclient import TestClient
from src.api import main


def test_history_preserves_gaps_and_requires_coverage(monkeypatch):
    index = pd.date_range('2026-01-01', periods=48, freq='h', tz='Etc/GMT-5').tz_convert('UTC')
    frame = pd.DataFrame({'power': .5, 'wind_speed': 8., 'temperature': -2.}, index=index)
    frame.index.name = 'timestamp'
    frame.loc[index[24:30], 'power'] = float('nan')
    monkeypatch.setattr(main, 'read_hourly', lambda _: frame)
    response = TestClient(main.app).get('/api/history/turbine_1')
    assert response.status_code == 200
    points = response.json()['points']
    assert len(points) == 2
    assert points[0]['timestamp'] == '2026-01-01T00:00:00+05:00'
    assert response.json()['timezone'] == 'UTC+05:00'
    assert points[0]['power'] == .5
    assert points[1]['power'] is None
    assert points[1]['wind_speed'] == 8.


def test_unknown_history_turbine():
    assert TestClient(main.app).get('/api/history/unknown').status_code == 404
