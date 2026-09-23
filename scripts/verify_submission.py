"""Recompute submission evidence; fail on leakage, missing horizons or leaked secrets."""
import _bootstrap
import hashlib
import json
import re
import subprocess
import pandas as pd
from src.config import ROOT, RESULTS, MODELS, TURBINES, local_date
from src.models.evaluate import summarize
from src.utils import write_json


def main():
    predictions=pd.read_csv(RESULTS/'backtest_predictions.csv')
    origins=pd.to_datetime(predictions.forecast_origin,utc=True)
    targets=pd.to_datetime(predictions.target_timestamp,utc=True)
    assert len(predictions)==2*28*48, 'February must have 56 complete 48h runs'
    assert set(predictions.turbine_id)==set(TURBINES)
    assert not predictions.duplicated(['turbine_id','forecast_origin','horizon']).any()
    assert (predictions.groupby(['turbine_id','forecast_origin']).size()==48).all()
    assert (targets==origins+pd.to_timedelta(predictions.horizon-1,unit='h')).all()
    assert origins.min()==local_date('2026-02-01')
    assert origins.max()==local_date('2026-02-28')
    assert (pd.to_datetime(predictions.weather_availability_bound,utc=True)<=origins).all()
    assert (pd.to_datetime(predictions.model_trained_until,utc=True)<=origins).all()
    assert predictions.predicted_power.between(0,1).all()
    assert (predictions.lower_power<=predictions.predicted_power).all()
    assert (predictions.predicted_power<=predictions.upper_power).all()
    assert predictions.actual_power.isna().all() and predictions.error.isna().all()
    validation=pd.read_csv(RESULTS/'validation_predictions.csv')
    measured=summarize(validation[validation.in_evaluation_period])
    saved=json.loads((RESULTS/'metrics.json').read_text())['turbines']
    for t in TURBINES:
        for metric in ('mae','rmse','r2'):
            assert abs(measured[t]['model'][metric]-saved[t]['model'][metric])<1e-10
    files=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).decode().split('\0')
    bad=[]
    for name in filter(None,files):
        path=ROOT/name
        if path.is_file() and path.stat().st_size<5_000_000:
            if re.search(rb'sk-(?:proj-)?[A-Za-z0-9_-]{32,}',path.read_bytes()):
                bad.append(name)
    assert not bad, f'Secret-like content in publishable files: {bad}'
    ignored=subprocess.run(['git','check-ignore','-q','.env'],cwd=ROOT).returncode==0
    assert ignored, '.env must be ignored'
    evidence={'timezone':'Астана UTC+05:00','february_runs':56,'forecast_rows':len(predictions),
        'february_actuals_available':False,'causality_checks':'passed','secrets_check':'passed',
        'january':{t:{'model':measured[t]['model'],'baseline':measured[t]['baseline'],
            'mae_reduction_percent':100*(1-measured[t]['model']['mae']/measured[t]['baseline']['mae']),
            'interval_coverage':measured[t]['interval_coverage']} for t in TURBINES},
        'artifact_sha256':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [RESULTS/'backtest_predictions.csv',RESULTS/'validation_predictions.csv',
                         *[MODELS/f'{t}.joblib' for t in TURBINES]]},
        'limitations':['No February labels; no February skill claim.',
                       'Fixed 72h weather lead with 12h publication allowance; exact release time is not supplied.',
                       'Normalized power; no rated capacities for conversion to MWh.',
                       'Local service, single worker; external production hosting needs access controls.']}
    write_json(RESULTS/'submission_evidence.json',evidence)
    print(json.dumps(evidence,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
