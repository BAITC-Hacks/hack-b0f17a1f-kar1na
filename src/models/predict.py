from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from src.config import MODELS, utc
from src.data.features import make_features


def load_model(turbine_id: str, directory: Path = MODELS) -> dict:
    path = directory / f'{turbine_id}.joblib'
    if not path.exists():
        raise FileNotFoundError('Trained model missing. Run python scripts/train_models.py')
    # Only load trusted local artifacts; pickle/joblib is not safe for untrusted uploads.
    return joblib.load(path)

def predict(bundle: dict, history: pd.DataFrame, origin, weather: pd.DataFrame):
    origin = utc(origin)
    if utc(bundle['trained_until']) > origin:
        raise ValueError('Model training cutoff is after forecast origin (leakage)')
    if utc(bundle['calibration_end_exclusive']) > origin:
        raise ValueError('Interval calibration cutoff is after forecast origin (leakage)')
    x = make_features(history, origin, weather)
    if list(x.columns) != bundle['feature_names']:
        raise ValueError('Model feature schema mismatch')
    with threadpool_limits(limits=2):
        raw = bundle['estimator'].predict(x)
    if not np.isfinite(raw).all():
        raise ValueError('Model produced NaN/Inf')
    prediction = np.clip(raw, 0, 1)
    widths = np.where(x.horizon.to_numpy() <= 24, bundle['interval_radius']['1_24'],bundle['interval_radius']['25_48'])
    frame = weather.copy()
    frame['predicted_power'] = prediction
    frame['lower_power'] = np.clip(prediction-widths, 0, 1)
    frame['upper_power'] = np.clip(prediction+widths, 0, 1)
    corrections = {'clipped_values': int((raw!=prediction).sum()),
                   'reason': 'Normalized target documented and observed in [0,1]',
                   'suspicious_jumps': int((np.abs(np.diff(prediction))>.6).sum())}
    return frame, corrections
