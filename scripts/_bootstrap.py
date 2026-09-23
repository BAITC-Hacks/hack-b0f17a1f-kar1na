import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('MPLCONFIGDIR', '/tmp/hackalem-matplotlib')
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
