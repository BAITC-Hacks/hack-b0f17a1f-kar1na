import _bootstrap
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from src.config import TURBINES, RESULTS, LOCAL_TZ
from src.data.preprocessing import prepare_turbine
from src.data.loader import load_turbine, NUMERIC
from src.utils import write_json


def main():
    out = RESULTS / 'eda'
    out.mkdir(parents=True, exist_ok=True)
    reports, frames = {}, {}
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), constrained_layout=True)
    for row, turbine in enumerate(TURBINES):
        hourly, report = prepare_turbine(turbine)
        reports[turbine], frames[turbine] = report, hourly
        raw, _ = load_turbine(turbine)
        for col, field in enumerate(NUMERIC):
            axes[row, col].hist(raw[field].dropna(), bins=50, color=['#216e8a','#e38c3d'][row], alpha=.85)
            axes[row,col].set(title=f'{turbine} | {field}', xlabel={'power':'Normalized power','wind_speed':'Wind (m/s)','temperature':'Temperature (C)'}[field], ylabel='10-minute samples')
    fig.savefig(out / 'distributions.png', dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    for ax, (turbine, hourly) in zip(axes, frames.items()):
        valid = hourly.dropna(subset=['power','wind_speed'])
        hb = ax.hexbin(valid.wind_speed, valid.power, gridsize=55, mincnt=1, bins='log', cmap='viridis')
        ax.set(title=f'{turbine} | empirical power curve', xlabel='Wind (m/s)', ylabel='Normalized hourly power')
        fig.colorbar(hb, ax=ax, label='Hourly samples (log scale)')
    fig.savefig(out / 'power_curves.png', dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(3, 1, figsize=(13, 9), constrained_layout=True)
    for field, ax in zip(NUMERIC, axes):
        for turbine, hourly in frames.items():
            hourly[field].resample('MS').mean().plot(ax=ax, label=turbine)
        ax.set(ylabel=field, xlabel='Month (UTC)', title=f'Monthly mean {field} (gaps retained)')
        ax.legend()
    fig.savefig(out / 'turbine_comparison.png', dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1,2,figsize=(10,4),constrained_layout=True)
    for ax, (turbine, hourly) in zip(axes, frames.items()):
        corr = hourly[NUMERIC].corr()
        im = ax.imshow(corr, vmin=-1,vmax=1,cmap='RdBu_r')
        ax.set(xticks=range(3), yticks=range(3), xticklabels=NUMERIC, yticklabels=NUMERIC,title=turbine)
        for i in range(3):
            for j in range(3):
                ax.text(j,i,f'{corr.iloc[i,j]:.2f}',ha='center',va='center',color='white' if abs(corr.iloc[i,j])>.6 else 'black')
    fig.colorbar(im,ax=axes,label='Pearson correlation')
    fig.savefig(out/'correlations.png',dpi=160)
    plt.close(fig)
    paired = pd.concat({k: v.power for k,v in frames.items()},axis=1)
    reports['comparison'] = {'power_correlation': paired.corr().to_dict(), 'paired_hours': int(paired.dropna().shape[0])}
    write_json(out / 'report.json', reports)
    lines = ['# Dataset audit', '', 'Timezone: fixed UTC+05:00 (confirmed by user). Files end **2026-01-31**, not February.',
             'Hourly timestamps label interval starts; values become available at the end of the hour.', '',
             '| Turbine | Raw rows | First / last local timestamp | Missing 10-min timestamps | Missing power hours |',
             '|---|---:|---|---:|---:|']
    for name in TURBINES:
        r=reports[name]; p=r['preprocessing']
        lines.append(f"| {name} | {r['rows']} | {r['date_start'].tz_convert(LOCAL_TZ)} / {r['date_end'].tz_convert(LOCAL_TZ)} | {p['missing_10min_timestamps']} | {p['hourly_missing']['power']} |")
    lines += ['', '## Cleaning decisions',
        'UTF-8, comma separator, five original columns. ID is an identifier, not a feature. No duplicate timestamps or explicit nulls in the supplied files.',
        'Missing timestamps are real gaps, not zero production. Hourly means require at least four distinct valid 10-minute readings. Targets remain missing when coverage is insufficient; no interpolation, backfill or fabricated labels.',
        'Invalid cells (power outside [0,1], wind outside [0,75], temperature outside [-80,60]) become missing and are counted in report.json. Low production in strong wind may mean downtime/curtailment and is retained. Duplicates, if added later, are averaged per timestamp before resampling.',
        'All origin lag/rolling features use only complete past hours. HistGradientBoosting handles missing feature values. Missing training targets are excluded explicitly.',
        '', '## Figures', '![Distributions](distributions.png)', '![Power curve](power_curves.png)', '![Comparison](turbine_comparison.png)', '![Correlations](correlations.png)',
        '', 'Full ranges, quantiles, correlations, step counts, anomaly counts and SHA-256 fingerprints: [report.json](report.json).']
    (out / 'report.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({k:reports[k]['preprocessing'] for k in TURBINES},indent=2))

if __name__ == '__main__':
    main()
