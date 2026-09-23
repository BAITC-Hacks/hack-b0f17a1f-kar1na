"""Run the same bounded agent as the dashboard, without a browser."""
import _bootstrap
import argparse
import json
from src.agents.copilot import Copilot
from src.agents.forecast_agent import ForecastAgent


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--turbine',choices=['turbine_1','turbine_2'],default='turbine_1')
    parser.add_argument('--hours',type=int,choices=[24,48],default=48)
    parser.add_argument('--mode',choices=['replay','live'],default='replay')
    parser.add_argument('--origin',help='Timezone-aware ISO time, e.g. 2026-02-01T00:00:00+05:00')
    parser.add_argument('--message',default='Построй прогноз, оцени риски и сравни качество с базовым прогнозом.')
    args=parser.parse_args()
    r=Copilot(ForecastAgent()).run(args.turbine,args.hours,args.mode,args.origin,args.message)
    print(json.dumps({k:r[k] for k in ('status','engine','answer','llm_error','usage')},ensure_ascii=False,indent=2))
    print('Tools:', ', '.join(t['tool']+':'+t['status'] for t in r['tools']))
    if r['status']=='failed':
        raise SystemExit(1)


if __name__=='__main__': main()
