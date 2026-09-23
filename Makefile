.PHONY: install build serve test verify reproduce agent check-scada

install:
	python3 -m venv .venv
	.venv/bin/python -m pip install -r requirements.txt
	cd web && npm ci

build:
	cd web && npm run build

serve:
	.venv/bin/python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000

test:
	WEATHER_OFFLINE=true AGENT_MONITOR_ENABLED=false .venv/bin/python -m pytest -q

verify:
	.venv/bin/python scripts/verify_submission.py

reproduce:
	WEATHER_OFFLINE=true .venv/bin/python scripts/run_pipeline.py
	.venv/bin/python scripts/verify_submission.py

agent:
	.venv/bin/python scripts/run_agent.py

check-scada:
	WEATHER_OFFLINE=true .venv/bin/python scripts/check_scada_outage.py
