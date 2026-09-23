"""Application-owned periodic recalculation; no LLM calls or background token spend."""
import copy
import os
import threading
import pandas as pd
from src.config import TURBINES, RESULTS
from src.utils import write_json


class ForecastMonitor:
    def __init__(self, agent, result_dir=None):
        self.agent = agent
        self.result_dir = result_dir or RESULTS / 'monitor'
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._tick_lock = threading.Lock()
        self._thread = None
        self._state = {'enabled': False, 'status': 'stopped', 'last_check': None, 'turbines': {}}

    def status(self):
        with self._lock:
            return copy.deepcopy(self._state)

    def tick(self):
        if not self._tick_lock.acquire(blocking=False):
            return self.status()
        try:
            mode = os.getenv('FORECAST_MODE', 'replay')
            for turbine in TURBINES:
                try:
                    result = self.agent.run(turbine, 48, mode)
                    item = {'status': 'unchanged' if result.get('unchanged') else 'updated',
                            'run_id': result['run_id'], 'forecast_origin': result['forecast_origin'],
                            'assessment': result['assessment']['status']}
                except Exception as exc:
                    item = {'status': 'failed', 'error_type': type(exc).__name__,
                            'message': 'Forecast unavailable; previous saved version retained.'}
                with self._lock:
                    self._state['turbines'][turbine] = item
            with self._lock:
                self._state['last_check'] = pd.Timestamp.now(tz='UTC').isoformat()
                self._state['status'] = 'degraded' if any(v['status']=='failed' for v in self._state['turbines'].values()) else 'watching'
            write_json(self.result_dir / 'status.json', self.status())
            return self.status()
        finally:
            self._tick_lock.release()

    def start(self):
        if os.getenv('AGENT_MONITOR_ENABLED', 'false').lower() != 'true':
            return
        interval = max(60, int(os.getenv('AGENT_MONITOR_INTERVAL_SECONDS', '1800')))
        with self._lock:
            self._state.update(enabled=True, status='watching', interval_seconds=interval)
        self._stop.clear()
        def loop():
            # The UI obtains the initial forecast. First background refresh after interval.
            while not self._stop.wait(interval):
                self.tick()
        self._thread = threading.Thread(target=loop, name='windai-monitor', daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
        with self._lock:
            self._state.update(enabled=False, status='stopped')
