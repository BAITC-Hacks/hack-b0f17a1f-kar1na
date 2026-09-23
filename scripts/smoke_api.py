"""Verify a real running uvicorn process, including optional live weather calls."""
import _bootstrap
import argparse
import json
import httpx
from src.config import RESULTS
from src.api.schemas import ForecastResponse
from src.utils import write_json

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--base-url',default='http://127.0.0.1:8000')
    parser.add_argument('--live',action='store_true')
    args=parser.parse_args()
    checks=[]
    with httpx.Client(base_url=args.base_url,timeout=150) as client:
        paths=['/api/health','/api/turbines','/api/turbines/turbine_1',
            '/api/forecast/turbine_1?hours=48','/api/forecast/turbine_2?hours=24',
            '/api/forecast/all?hours=48','/api/turbines/turbine_1/details?hours=48',
            '/api/turbines/turbine_2/details?hours=24','/api/backtest/metrics',
            '/api/backtest/turbine_1?limit=5','/api/backtest/turbine_2?limit=5',
            '/api/validation/metrics','/api/agent/status','/openapi.json']
        if args.live: paths += ['/api/forecast/turbine_1?hours=48&mode=live','/api/forecast/turbine_2?hours=48&mode=live']
        for path in paths:
            response=client.get(path)
            response.raise_for_status()
            body=response.json()
            if path.startswith('/api/forecast/') and not path.startswith('/api/forecast/all'):
                ForecastResponse.model_validate(body)
                if 'mode=live' in path:
                    assert body['weather']['source']=='open_meteo_live', 'Live test must not silently pass on fallback'
                name='live' if 'mode=live' in path else 'replay'
                write_json(RESULTS/f'example_{name}_{body["turbine_id"]}.json',body)
            if path=='/api/health': assert body['ready']
            checks.append({'method':'GET','path':path,'status':response.status_code})
        response=client.post('/api/forecast/recalculate',json={'turbine_id':'turbine_1','hours':48,'mode':'replay'})
        response.raise_for_status(); ForecastResponse.model_validate(response.json())
        checks.append({'method':'POST','path':'/api/forecast/recalculate','status':response.status_code})
    write_json(RESULTS/'api_smoke_checks.json',checks)
    print(json.dumps(checks,indent=2))

if __name__=='__main__': main()
