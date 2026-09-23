"""Paired January evaluation: freeze telemetry at Jan 1, never refit models.

Run: .venv/bin/python scripts/check_scada_outage.py
Uses saved validation weather; no network or paid API calls.
"""
import _bootstrap
import hashlib

import joblib
import numpy as np
import pandas as pd

from src.config import MODELS, PROCESSED, RESULTS, TURBINES, local_date
from src.data.features import HISTORY_FEATURES, make_features
from src.data.preprocessing import read_hourly
from src.models.evaluate import summarize
from src.models.predict import predict
from src.utils import write_json


def available_history(history, origin, cutoff):
    """Keep completed observations before both the issue time and outage."""
    return history.loc[history.index < min(origin, cutoff)]


def main():
    cutoff = local_date('2026-01-01')
    source = RESULTS / 'validation_predictions.csv'
    saved = pd.read_csv(source)
    assert len(saved) == 2*31*48 and set(saved.turbine_id) == set(TURBINES)
    assert not saved.duplicated(['turbine_id', 'forecast_origin', 'horizon']).any()
    rows = []
    hashes = {str(source.name): hashlib.sha256(source.read_bytes()).hexdigest()}
    for turbine in TURBINES:
        history = read_hourly(turbine)
        hourly_path = PROCESSED / f'{turbine}_hourly.csv'
        hashes[hourly_path.name] = hashlib.sha256(hourly_path.read_bytes()).hexdigest()
        model_path = MODELS / f'{turbine}_evaluation.joblib'
        hashes[model_path.name] = hashlib.sha256(model_path.read_bytes()).hexdigest()
        bundle = joblib.load(model_path)
        for origin_text, group in saved[saved.turbine_id == turbine].groupby('forecast_origin'):
            origin = pd.Timestamp(origin_text)
            assert cutoff <= origin < local_date('2026-02-01')
            group = group.sort_values('horizon').copy()
            times = pd.DatetimeIndex(pd.to_datetime(group.target_timestamp, utc=True))
            assert len(group) == 48 and times.equals(pd.date_range(origin, periods=48, freq='h'))
            assert (pd.to_datetime(group.weather_availability_bound, utc=True) <= origin).all()
            weather = pd.DataFrame(group[['wind_speed', 'temperature']].to_numpy(),
                                   columns=['wind_speed', 'temperature'], index=times)
            # Reproduce the control first; fail if artifacts/weather no longer match.
            fresh, _ = predict(bundle, history.loc[history.index < origin], origin, weather)
            np.testing.assert_allclose(fresh.predicted_power, group.predicted_power, atol=1e-12, rtol=0)
            actual = history.power.reindex(times).to_numpy()
            in_period = times < local_date('2026-02-01')
            np.testing.assert_allclose(actual[in_period], group.actual_power.to_numpy()[in_period],
                                       atol=1e-12, rtol=0, equal_nan=True)
            past = available_history(history, origin, cutoff)
            stale, _ = predict(bundle, past, origin, weather)
            features = make_features(past, origin, weather)
            if origin >= cutoff+pd.Timedelta(days=1):
                assert features[HISTORY_FEATURES].isna().all().all()
            if origin == cutoff:
                np.testing.assert_allclose(stale.predicted_power, fresh.predicted_power, atol=1e-12, rtol=0)
            for column in ('predicted_power', 'lower_power', 'upper_power'):
                group[column] = stale[column].to_numpy()
            last = past.power.dropna()
            group['baseline_power'] = last.iloc[-1] if len(last) else np.nan
            group['history_cutoff'] = cutoff.isoformat()
            group['history_latest_timestamp'] = last.index[-1].isoformat() if len(last) else None
            group['history_age_hours'] = (origin-last.index[-1]-pd.Timedelta(hours=1)).total_seconds()/3600 if len(last) else np.nan
            group['history_features_available'] = features[HISTORY_FEATURES].notna().sum(axis=1).to_numpy()
            group['error'] = group.predicted_power - group.actual_power
            rows.append(group)
    outage = pd.concat(rows, ignore_index=True)
    control = saved[saved.in_evaluation_period].copy()
    scored = outage[outage.in_evaluation_period].copy()
    fresh_metrics, stale_metrics = summarize(control), summarize(scored)
    comparison = {}
    for turbine in TURBINES:
        f, s = fresh_metrics[turbine], stale_metrics[turbine]
        part = scored[scored.turbine_id == turbine]
        comparison[turbine] = {
            'fresh': f, 'outage': s,
            'mae_change_percent': 100*(s['model']['mae']/f['model']['mae']-1),
            'outage_mean_interval_width': float((part.upper_power-part.lower_power).mean()),
            'fully_missing_history_pairs': int((part.history_features_available == 0).sum()),
        }
    report = {
        'period_start': '2026-01-01', 'period_end_exclusive': '2026-02-01',
        'history_cutoff': cutoff.isoformat(), 'timezone': 'UTC+05:00',
        'method': 'Frozen evaluation weights and original archived weather. All SCADA from January 1 withheld from features; January power used only for scoring. No refit or interval recalibration.',
        'baseline': 'Outage persistence holds last observed pre-January power; fresh persistence updates daily. These are different information sets.',
        'weighting': 'Same origin-target pairs as original January validation; overlapping forecasts count separately. February targets excluded.',
        'limitations': 'One historical outage simulation, not measured February/live quality. January weather and evaluation weights differ from February deployment.',
        'source_sha256': hashes, 'turbines': comparison,
    }
    destination = RESULTS / 'scada_outage'
    destination.mkdir(exist_ok=True)
    outage.to_csv(destination / 'predictions.csv', index=False)
    write_json(destination / 'metrics.json', report)
    lines = ['# Проверка без свежей SCADA', '',
             'Использованы замороженные evaluation-модели и архивная погода исходной январской проверки. Переобучения и перекалибровки интервалов нет.', '',
             'История заморожена на 01.01.2026 00:00 UTC+05. Первый запуск имеет свежую декабрьскую историю; со второго дня все lag/rolling признаки отсутствуют. Январские actuals доступны только оценщику.', '',
             '| Турбина | MAE со свежей SCADA | MAE без обновлений | Изменение MAE | RMSE без обновлений | R² без обновлений | Покрытие интервалов | Средняя ширина |',
             '|---|---:|---:|---:|---:|---:|---:|---:|']
    for turbine, item in comparison.items():
        f, s = item['fresh'], item['outage']
        m = s['model']
        lines.append(f"| {turbine} | {f['model']['mae']:.6f} | {m['mae']:.6f} | {item['mae_change_percent']:+.2f}% | {m['rmse']:.6f} | {m['r2']:.6f} | {s['interval_coverage']:.2%} | {item['outage_mean_interval_width']:.6f} |")
    lines += ['', 'На каждую турбину: 1 464 оценённых пары и 744 уникальных часа. Сохранены также 24 неоцениваемых февральских часа на турбину.', '',
              'Контрольный прогноз заново рассчитан и совпадает с исходным с допуском 1e-12. Январские цели сверены с hourly SCADA. Метрики по горизонтам и baseline находятся в metrics.json.', '',
              'Baseline без обновлений фиксирует последнюю мощность декабря; его нельзя выдавать за baseline со свежей SCADA. Сравнение двух моделей использует одинаковые цели и погоду.', '',
              'Это симуляция одного месяца. Результат не доказывает февральское или live-качество и не измеряет покрытие интервалов deployment refit. Модели и исходные validation/backtest артефакты не изменяются.', '',
              'Повторить из корня: `.venv/bin/python scripts/check_scada_outage.py`. Сеть и OpenAI не требуются.', '']
    (destination / 'REPORT.md').write_text('\n'.join(lines))
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
