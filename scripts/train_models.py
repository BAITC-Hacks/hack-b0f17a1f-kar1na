import _bootstrap
import json
from src.config import TURBINES, RESULTS
from src.models.train import fit_turbine
from src.models.backtest import run_backtest
from src.services.weather_provider import OpenMeteoProvider
from src.utils import write_json

def main():
    provider=OpenMeteoProvider()
    metadata={t:fit_turbine(t,provider) for t in TURBINES}
    write_json(RESULTS/'model_metadata.json',metadata)
    summary=run_backtest('2026-01-01','2026-02-01',evaluation=True)
    write_json(RESULTS/'metrics.json',summary)
    print(json.dumps({t:{k:v for k,v in r.items() if k in ('model','baseline','status')} for t,r in summary['turbines'].items()},indent=2))

if __name__=='__main__': main()
