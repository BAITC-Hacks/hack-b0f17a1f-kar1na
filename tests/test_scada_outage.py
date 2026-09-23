"""Outage evaluation must withhold telemetry even after it becomes past data."""
import importlib
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import local_date
from src.data.features import HISTORY_FEATURES, make_features


def test_outage_withholds_new_observations_and_preserves_initial_history(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    available_history = importlib.import_module('check_scada_outage').available_history
    cutoff = local_date('2026-01-01')
    index = pd.date_range(cutoff-pd.Timedelta(hours=24), periods=96, freq='h')
    history = pd.DataFrame({'power': .5, 'wind_speed': 8., 'temperature': 2.}, index=index)
    initial = available_history(history, cutoff, cutoff)
    assert len(initial) == 24
    weather = pd.DataFrame({'wind_speed': 8., 'temperature': 2.},
                           index=pd.date_range(cutoff, periods=48, freq='h'))
    assert make_features(initial, cutoff, weather)[HISTORY_FEATURES].notna().all().all()
    later = cutoff+pd.Timedelta(days=2)
    changed = history.copy()
    changed.loc[changed.index >= cutoff, :] = 999
    pd.testing.assert_frame_equal(available_history(changed, later, cutoff), initial)
    weather.index = pd.date_range(later, periods=48, freq='h')
    assert np.isnan(make_features(initial, later, weather)[HISTORY_FEATURES]).all().all()
