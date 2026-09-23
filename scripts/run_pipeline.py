"""Reproducible complete pipeline (cached archived weather by default)."""
import _bootstrap
import subprocess
import sys
from src.config import ROOT

def main():
    for script in ['analyze_data.py','train_models.py','run_backtest.py','report_results.py']:
        subprocess.run([sys.executable,str(ROOT/'scripts'/script)],cwd=ROOT,check=True)
    subprocess.run([sys.executable,'-m','pytest','-q'],cwd=ROOT,check=True)

if __name__=='__main__': main()
