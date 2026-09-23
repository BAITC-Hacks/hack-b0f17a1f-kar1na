# Файлы технического ядра

Исходные CSV: `data/raw/turbine_1.csv`, `data/raw/turbine_2.csv`.
Почасовые данные: `data/processed/turbine_1_hourly.csv`, `data/processed/turbine_2_hourly.csv`.
Архивные и live ответы Open-Meteo: `data/weather/*.json` (реальные ответы, request URL, retrieved_at).

## Код, конфигурация, модели и отчёты

- `.env.example`
- `.gitignore`
- `README.md`
- `docs/frontend.md`
- `models/turbine_1.joblib`
- `models/turbine_1_evaluation.joblib`
- `models/turbine_2.joblib`
- `models/turbine_2_evaluation.joblib`
- `pytest.ini`
- `requirements.txt`
- `results/RESULTS.md`
- `results/api_smoke_checks.json`
- `results/backtest_metrics.json`
- `results/backtest_predictions.csv`
- `results/eda/correlations.png`
- `results/eda/distributions.png`
- `results/eda/power_curves.png`
- `results/eda/report.json`
- `results/eda/report.md`
- `results/eda/turbine_comparison.png`
- `results/example_live_turbine_1.json`
- `results/example_live_turbine_2.json`
- `results/example_replay_turbine_1.json`
- `results/example_replay_turbine_2.json`
- `results/metrics.json`
- `results/model_metadata.json`
- `results/validation_forecasts.png`
- `results/validation_metrics.json`
- `results/validation_predictions.csv`
- `scripts/_bootstrap.py`
- `scripts/analyze_data.py`
- `scripts/fetch_weather.py`
- `scripts/report_results.py`
- `scripts/run_backtest.py`
- `scripts/run_pipeline.py`
- `scripts/smoke_api.py`
- `scripts/train_models.py`
- `src/__init__.py`
- `src/agents/__init__.py`
- `src/agents/forecast_agent.py`
- `src/api/__init__.py`
- `src/api/main.py`
- `src/api/schemas.py`
- `src/config.py`
- `src/data/__init__.py`
- `src/data/features.py`
- `src/data/loader.py`
- `src/data/preprocessing.py`
- `src/models/__init__.py`
- `src/models/backtest.py`
- `src/models/evaluate.py`
- `src/models/predict.py`
- `src/models/train.py`
- `src/services/__init__.py`
- `src/services/weather_provider.py`
- `src/utils.py`
- `tests/test_pipeline.py`

Runtime JSON запусков агента: `results/forecasts/` (gitignored). Существующие `assets/` и параллельно разрабатываемый `3d/` этим backend-заданием не изменялись.