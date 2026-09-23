"""Metrics exclude absent targets and report coverage explicitly."""
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def metrics(actual, predicted) -> dict:
    y, p = np.asarray(actual,dtype=float), np.asarray(predicted,dtype=float)
    mask = np.isfinite(y) & np.isfinite(p)
    n = int(mask.sum())
    if not n:
        return {'n': 0, 'mae': None, 'normalized_mae': None, 'rmse': None, 'r2': None}
    y,p = y[mask],p[mask]
    mae = float(mean_absolute_error(y,p))
    return {'n': n, 'mae': mae, 'normalized_mae': mae,
            'rmse': float(np.sqrt(mean_squared_error(y,p))),
            'r2': float(r2_score(y,p)) if n>1 and np.var(y)>0 else None}

def summarize(predictions: pd.DataFrame) -> dict:
    summary = {}
    for turbine, frame in predictions.groupby('turbine_id'):
        valid = frame.actual_power.notna()
        model = metrics(frame.actual_power,frame.predicted_power)
        summary[turbine] = {'model': model,
            'baseline': metrics(frame.actual_power,frame.baseline_power),
            'rows': len(frame), 'scored_rows': int(valid.sum()),
            'unique_target_hours': int(frame.loc[valid,'target_timestamp'].nunique()),
            'target_coverage': float(valid.mean()),
            'status': 'evaluated' if valid.any() else 'unscored_missing_actuals',
            'horizons': {label: {
                'model': metrics(part.actual_power,part.predicted_power),
                'baseline': metrics(part.actual_power,part.baseline_power)}
                for label,part in [('1_24',frame[frame.horizon<=24]),('25_48',frame[frame.horizon>24])]},
            'by_horizon': {int(h):metrics(g.actual_power,g.predicted_power) for h,g in frame.groupby('horizon')},
            'interval_coverage': float(((frame.loc[valid,'actual_power']>=frame.loc[valid,'lower_power']) &
                                         (frame.loc[valid,'actual_power']<=frame.loc[valid,'upper_power'])).mean()) if valid.any() else None,
        }
    return summary
