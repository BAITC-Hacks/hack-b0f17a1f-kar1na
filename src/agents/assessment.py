"""Evidence-based operator assessment; the LLM cannot alter these calculations."""
import numpy as np
import pandas as pd
from src.config import DISPLAY_TIMEZONE


def assess_forecast(result):
    frame = pd.DataFrame(result['forecast'])
    power = frame.predicted_power.to_numpy()
    widths = (frame.upper_power - frame.lower_power).to_numpy()
    ramps = np.abs(np.diff(power))
    issues = []
    if result['weather'].get('is_fallback'):
        issues.append({'code': 'weather_fallback', 'severity': 'high',
                       'message': 'Использована резервная погода; это не архивный метеопрогноз.'})
    age = result.get('history_age_hours')
    if age is None or age > 1:
        issues.append({'code': 'stale_scada', 'severity': 'warning',
                       'message': 'Нет свежей телеметрии. Лаги не подменяются старыми значениями.'})
    if widths.mean() > .5:
        issues.append({'code': 'wide_interval', 'severity': 'warning',
                       'message': 'Широкий прогнозный интервал: для планирования учитывайте весь диапазон.'})
    if len(ramps) and ramps.max() > .3:
        issues.append({'code': 'power_ramp', 'severity': 'warning',
                       'message': 'Есть часовой перепад мощности больше 0.30 нормализованной единицы.'})
    if result['mode'] == 'live':
        issues.append({'code': 'live_unvalidated', 'severity': 'warning',
                       'message': 'Точность на текущих погодных выпусках отдельно не проверена.'})
    peak = frame.iloc[int(np.argmax(power))]
    return {
        'status': 'degraded' if any(i['severity'] == 'high' for i in issues) else 'review' if issues else 'ready',
        'issues': issues, 'mean_power': float(power.mean()), 'peak_power': float(power.max()),
        'peak_time_astana': pd.Timestamp(peak.timestamp).tz_convert(DISPLAY_TIMEZONE).isoformat(),
        'max_hourly_ramp': float(ramps.max()) if len(ramps) else 0.,
        'mean_interval_width': float(widths.mean()),
        'interval_note': 'Эмпирический прогнозный интервал; покрытие 90% не гарантируется для нового режима.',
        'unit': 'normalized', 'energy_mwh': None,
        'energy_note': 'Для расчёта МВт·ч нужны номинальные мощности и определение нормализации.',
    }


def compare_forecasts(previous, current):
    if previous is None:
        return {'previous_run_id': None, 'overlap_hours': 0, 'mean_absolute_change': None}
    old = {p['timestamp']: p['predicted_power'] for p in previous['forecast']}
    deltas = [abs(p['predicted_power'] - old[p['timestamp']]) for p in current['forecast'] if p['timestamp'] in old]
    return {'previous_run_id': previous['run_id'], 'overlap_hours': len(deltas),
            'mean_absolute_change': float(np.mean(deltas)) if deltas else None,
            'max_absolute_change': float(max(deltas)) if deltas else None,
            'weather_changed': previous['weather']['input_sha256'] != current['weather']['input_sha256']}
