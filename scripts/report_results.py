import _bootstrap
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from src.config import RESULTS, TURBINES, LOCAL_TZ
from src.utils import write_json

def main():
    frame=pd.read_csv(RESULTS/'validation_predictions.csv')
    summary=json.loads((RESULTS/'metrics.json').read_text())
    plt.style.use('seaborn-v0_8-whitegrid')
    fig,axes=plt.subplots(2,1,figsize=(14,8),constrained_layout=True)
    for ax,turbine in zip(axes,TURBINES):
        data=frame[(frame.turbine_id==turbine)&(frame.horizon<=24)].copy()
        t=pd.to_datetime(data.target_timestamp,utc=True).dt.tz_convert(LOCAL_TZ)
        ax.fill_between(t,data.lower_power,data.upper_power,color='#216e8a',alpha=.15,label='Empirical 90% band')
        ax.plot(t,data.actual_power,color='#222222',linewidth=1.2,label='Actual')
        ax.plot(t,data.predicted_power,color='#216e8a',linewidth=1.2,label='ML')
        ax.plot(t,data.baseline_power,color='#ca823c',linewidth=.9,alpha=.6,label='Persistence')
        ax.set(title=f'{turbine}: January holdout, first 24 hours of each daily forecast',ylabel='Normalized power',ylim=(-.02,1.02))
        ax.legend(loc='upper right',ncol=4)
    fig.savefig(RESULTS/'validation_forecasts.png',dpi=160)
    plt.close(fig)
    lines=['# Measured results','',
        'Independent January 2026 evaluation. Forecasts use archived GFS weather, never future SCADA weather. All metrics below are computed from saved prediction rows.',
        '', '| Turbine | Persistence MAE | Model MAE | Model RMSE | Model R² | MAE improvement |',
        '|---|---:|---:|---:|---:|---:|']
    for t,r in summary['turbines'].items():
        m,b=r['model'],r['baseline']
        lines.append(f"| {t} | {b['mae']:.6f} | {m['mae']:.6f} | {m['rmse']:.6f} | {m['r2']:.6f} | {100*(1-m['mae']/b['mae']):.2f}% |")
        lines.extend([])
    lines += ['', 'Each turbine has 1,464 scored origin-target pairs and 744 unique January target hours. Overlapping forecasts are separate forecast decisions. The last 24 hours issued on January 31 fall in February and are excluded from January metrics.',
              '', '## Interval coverage', 'Intervals target nominal 90% coverage using December residuals. Time dependence and distribution shift mean this is not a coverage guarantee.']
    for t,r in summary['turbines'].items():
        lines.append(f"- {t}: observed January coverage {r['interval_coverage']:.2%}.")
    lines += ['', '## February replay', '2,688 forecast rows, 56 daily runs, 48 hours each. No February actual power exists in the supplied files. `actual_power` and `error` are empty; MAE/RMSE/R² are null. Of these rows, 48 target hours lie beyond the February scoring period. After February 1, history is increasingly stale, not replaced by invented observations.',
              '', '![January forecasts](validation_forecasts.png)', '',
              'Files: metrics.json, validation_predictions.csv, backtest_predictions.csv, backtest_metrics.json.']
    (RESULTS/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')

if __name__=='__main__': main()
