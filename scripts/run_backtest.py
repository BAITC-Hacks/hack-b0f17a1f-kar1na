import _bootstrap
import argparse
import json
from src.models.backtest import run_backtest

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--start',default='2026-02-01')
    p.add_argument('--end',default='2026-03-01',help='exclusive local date')
    p.add_argument('--hours',type=int,choices=[24,48],default=48)
    p.add_argument('--evaluation',action='store_true',help='Use frozen evaluation weights')
    args=p.parse_args()
    summary=run_backtest(args.start,args.end,args.evaluation,args.hours)
    print(json.dumps({t:r['status'] for t,r in summary['turbines'].items()},indent=2))

if __name__=='__main__': main()
