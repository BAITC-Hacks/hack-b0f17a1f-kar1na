
# AlemWind — Agentic AI для прогнозирования ВЭС

Объединённый сайт WindAI: дизайн, прогнозы API, история SCADA и интерактивная 3D-модель. Запуск и описание интеграции: [web/README.md](web/README.md).

Рабочее ML/backend-ядро HackAlem AI: прогноз нормализованной мощности двух турбин на **24 или 48 часов**, агент с наблюдаемыми состояниями и JSON API для 3D dashboard.

**Критическое ограничение исходных данных:** предоставленные файлы называются «11.03.2023–28.02.2026», но оба фактически заканчиваются **31.01.2026 23:50 UTC+05:00**. Поэтому февральские прогнозы рассчитаны, а февральские MAE/RMSE/R² **не выдуманы и равны `null`**. Измеренное качество ниже относится к независимому январскому holdout. Frontend включён в репозиторий и обслуживается тем же FastAPI после сборки.


## Быстрый запуск и проверка

Требуются Python 3.11 и Node.js 22. Готовые модели и архив погоды уже включены.

```bash
make install
make build
make serve
```

Открыть `http://127.0.0.1:8000/#agent`. В поле задачи нажать **«Запустить ИИ-агента»**.
Численный прогноз можно проверить без OpenAI: `make test` и `make verify`.
Полное повторное обучение и replay из локального архива: `make reproduce`.
На Overview справа от 3D-модели находится контекстный ИИ-агент. Выбор Generator / Gearbox / Shaft / Rotor или раскрытие гондолы автоматически обновляет пояснение. Можно запросить прогноз, оценку рисков или задать вопрос. Ответ привязан к выбранной турбине и режиму, одинаковые пояснения кэшируются; старый ответ не заменяет новый при быстром переключении. Датчиков температуры генератора, вибрации и состояния узлов в SCADA нет, поэтому диагностика не выдумывается.

Командный агент: `make agent` (использует платный API только при наличии локального ключа).

- [Сценарий защиты и соответствие критериям](docs/DEFENSE.md)
- [Проверяемые результаты и SHA-256 артефактов](results/submission_evidence.json)
- [Интерактивная схема API](http://127.0.0.1:8000/docs)

Дополнительные маршруты:

| Метод | Маршрут | Назначение |
|---|---|---|
| POST | `/api/agent/run` | OpenAI → реальные инструменты → прогноз и объяснение |
| POST | `/api/agent/inspect` | Пояснение выбранной турбины или её узла по фактическому контексту |
| POST | `/api/agent/check-updates` | Проверка обновлений двух турбин без LLM |
| GET | `/api/agent/status` | Этапы прогнозирования и состояние монитора |
| GET | `/api/export/turbine_1?hours=48&mode=replay` | CSV: UTC, время Астаны, интервалы и происхождение |

`POST /api/agent/run` принимает `turbine_id`, `hours`, `mode`, необязательный `forecast_origin`
со смещением и `message` до 1500 символов. Ключ никогда не принимается от браузера и не возвращается в API.
Локальные журналы находятся в игнорируемых `results/agent_runs`, `results/forecasts`, `results/monitor`.

Docker-альтернатива (ключ передаётся при запуске, не во время сборки):

```bash
docker build -t windai .
docker run --rm -p 127.0.0.1:8000:8000 --env-file .env windai
```

Локальное приложение предназначено для доверенного пользователя. Для публичного сервера потребуются
аутентификация, ограничение частоты запросов и постоянное хранилище. Dockerfile и CI добавлены;
фактическую проверку Docker нужно проводить при работающем Docker daemon.

## Problem

Диспетчеру нужен почасовой прогноз выработки каждой турбины на следующие сутки/двое. В реальной работе будущая фактическая погода неизвестна. Решение должно использовать доступные на момент расчёта метеопрогнозы, учитывать недоступность телеметрии и давать проверяемый результат.

Мощность в CSV нормализована в диапазоне [0, 1]. Это **не кВт и не МВт·ч**. Номинальная мощность и высота ступицы не предоставлены; `rated_power_kw` и `hub_height_m` возвращаются как `null`.

## Solution

- Реальные CSV → аудит → почасовые средние с контролем покрытия.
- Архив **операционных прогнозов GFS** Open-Meteo Previous Runs → прогноз погоды на каждый целевой час.
- Отдельная HistGradientBoosting-модель для каждой турбины → прямой прогноз всех 48 часов, без рекурсивной подстановки будущих actuals.
- Агент получает конфигурацию и погоду, проверяет данные, запускает модель, проверяет результат, сохраняет JSON и состояние.
- FastAPI отдаёт прогнозы, неопределённость, последние известные наблюдения, метрики и этапы выполнения.

По умолчанию API работает в **replay** на 01.02.2026. Для реального текущего прогноза используйте `?mode=live` или `FORECAST_MODE=live`. Ответ всегда содержит `mode`, `forecast_origin` и источник погоды.

## Architecture

```text
Weather API (GFS archive / live)
            |
            v
Weather Agent (retry, cache, explicit fallback)
            |
            v
Data Processor (UTC, coverage, origin-only history)
            |
            v
Forecast Model (direct multi-horizon HistGradientBoosting)
            |
            v
Validation Agent (bounds, NaN, timestamps, ramps)
            |
            v
FastAPI (JSON + agent status)
            |
            v
3D Dashboard + OpenAI operator interface
```

Численный цикл реализован в `ForecastAgent`. Над ним работает `Copilot`: OpenAI Responses API выбирает реальные инструменты проверки данных, расчёта, оценки рисков и сравнения результатов. Модель мощности работает без ключа; ключ нужен для языкового агента.

```text
src/
  config.py                 # координаты, timezone, пути
  utils.py                  # JSON без NaN, атомарная запись
  data/
    loader.py               # проверка схемы и фактического CSV
    preprocessing.py        # 10-minute → hourly, audit
    features.py             # календарь, лаги, rolling, horizon
  models/
    train.py                # chronological train/calibration, joblib
    predict.py              # проверка cutoff, prediction intervals
    evaluate.py             # MAE, RMSE, R², coverage
    backtest.py             # daily rolling origins
  services/weather_provider.py
  agents/forecast_agent.py
  api/main.py
  api/schemas.py
scripts/
  analyze_data.py
  fetch_weather.py
  train_models.py
  run_backtest.py
  report_results.py
  run_pipeline.py
  smoke_api.py
models/                     # deployment + evaluation joblib для каждой турбины
results/                    # метрики, прогнозы, EDA, примеры JSON
  eda/
data/
  raw/                      # точные копии исходных CSV
  processed/                # часовые ряды
  weather/                  # реальные ответы Open-Meteo и URL/время загрузки
tests/                      # тесты pipeline, leakage и API
```

## Dataset

Копии оригинальных CSV находятся в `data/raw/turbine_1.csv` и `data/raw/turbine_2.csv`. Исходные файлы в Downloads не изменялись. SHA-256, полный audit и статистики сохранены в `results/eda/report.json`.

Формат проверен на содержимом файлов: **UTF-8 без BOM**, разделитель **запятая**, переводы строк CRLF. Колонки:

| Исходная колонка                                                | Тип / использование                      |
| ------------------------------------------------------------------------------ | -------------------------------------------------------- |
| `ID`                                                                         | integer, идентификатор; не признак |
| `Статистическое время`                                    | timestamp,`%Y-%m-%d %H:%M:%S`                          |
| `Средняя скорость ветра(m/s)`                            | float →`wind_speed`, м/с                            |
| `Нормализованная активная мощность`           | float →`power`, target                                |
| `Средняя температура окружающей среды(°C)` | float →`temperature`, °C                             |

**Время проекта — Астана, UTC+05:00.** Внутри pipeline и в транспортных timestamp — aware UTC. Суточные границы, CSV-экспорт и календарные признаки используют UTC+05:00; OpenAI получает уже переведённые локальные даты. Для даты прогноза 2026 года IANA-зона — `Asia/Almaty`. Исторические исходные CSV без смещения интерпретируются как фиксированный UTC+05 для совместимости с предоставленным рядом и сохранёнными моделями. Историческую смену официального часового пояса нельзя автоматически применить к SCADA без подтверждения формата выгрузки; при иной трактовке нужно заново подготовить данные и переобучить модели.

| Показатель                                                      |        Turbine 1 |        Turbine 2 |
| ------------------------------------------------------------------------- | ---------------: | ---------------: |
| Исходных строк                                               |          142 360 |          149 499 |
| Начало, локальное время                               | 2023-03-11 00:00 | 2023-03-11 00:00 |
| Конец, локальное время                                 | 2026-01-31 23:50 | 2026-01-31 23:50 |
| Явных null / duplicate timestamps                                    |            0 / 0 |            0 / 0 |
| Пропущенных 10-минутных timestamps                     |            9 992 |            2 853 |
| Часов в регулярной сетке                             |           25 392 |           25 392 |
| Часов без допустимого target                           |            1 664 |              473 |
| Скорость ветра, min…max, м/с                              |         0…22,97 |      0,11…21,43 |
| Нормализованная мощность                           |             0…1 |             0…1 |
| Температура, min…max, °C                                     |   −19,26…43,48 |   −19,08…43,97 |
| Максимальный интервал между записями, ч |              999 |             57,5 |

Координаты извлечены из Google Maps redirect ссылок в PDF кейса:

- Turbine 1: **43.645150, 78.535604** — https://maps.app.goo.gl/iN6svMt69D5qRpFU9
- Turbine 2: **43.643198, 78.538828** — https://maps.app.goo.gl/8UQMwsYavY6nLvFY8

## Data preprocessing

1. Проверка encoding, separator, обязательных колонок и числовых преобразований.
2. Строгий timestamp parse → фиксированный UTC+05 → UTC → сортировка.
3. Проверка шага и сетки 10 минут. Если появятся дубликаты, измерения одного timestamp усредняются **до** агрегации, чтобы не завышать покрытие часа.
4. Невозможные значения заменяются на missing с подсчётом в audit: power вне [0,1], wind вне [0,75] м/с, temperature вне [−80,60] °C. В предоставленных данных таких значений не найдено.
5. Почасовая арифметическая средняя по равным 10-минутным интервалам. Час требует минимум **4 из 6** измерений для каждой переменной. `*_samples` сохраняют фактическое покрытие.
6. Недостаточно покрытые часы остаются missing. **Target не интерполируется, не forward-fill и не backfill.** Неизвестный target исключается из обучения/метрик, а не превращается в ноль.
7. Низкая мощность при сильном ветре сохраняется: возможны остановы, ограничения или неисправность. Причина без SCADA-флагов неизвестна.

Timestamp часа — начало интервала `[t, t+1h)`. Его средняя считается доступной только на `t+1h`. Дополнительная задержка SCADA в MVP не моделируется.

EDA для жюри: [results/eda/report.md](results/eda/report.md), распределения target/ветра/температуры, power curves, корреляции, сравнение турбин. Месячные средние с покрытием ниже 80% скрываются на графике сравнения, а покрытие показано отдельно.

## Feature engineering

Прямой прогноз: одна строка признаков = `(forecast_origin, target_timestamp, horizon)`.

- Календарь целевого часа: `hour`, `day_of_week`, `month`, `day_of_year`.
- Циклические пары sin/cos для hour, month, day_of_year.
- **Прогнозные**, а не фактические будущие `wind_speed`, `temperature`.
- `power_lag_1/3/6/12/24`, `wind_lag_1/3/6/24` относительно **origin**.
- Rolling mean/std по wind и power за 3/6/12/24 часа **перед origin**. Требуется минимум половина окна и не менее двух наблюдений.
- `horizon` = 1…48.

Для горизонта 48 lag_1 всё ещё означает последний завершённый час до origin, а не фактическую мощность на 47-м часе будущего. Все 48 значений рассчитываются напрямую. Отсутствующие лаги обрабатывает HistGradientBoosting. Для устойчивости к пропавшей телеметрии добавляются копии каждой четвёртой training-строки с masked history features; targets и weather не синтезируются.

## Model

Две отдельные `HistGradientBoostingRegressor`: `max_iter=180`, `max_leaf_nodes=15`, `learning_rate=0.06`, `l2_regularization=8`, `min_samples_leaf=40`, `random_state=42`. Random early stopping отключён. Достаточно CPU; XGBoost/LightGBM не требуются.

Данные показывают разные объёмы пропусков, остановы и небольшие различия power curves. Раздельные модели позволяют учесть их и независимо сохранять/калибровать турбины. Утверждения, что этот вариант лучше общей модели, без эксперимента нет.

Модель обучается на **архивных прогнозах** погоды с января 2024; 2023 используется в EDA и остаётся доступен в истории, но не подменяется фактической погодой для training. Строки без archived forecast исключаются явно. Число использованных строк: `results/model_metadata.json`.

Два набора артефактов:

- `models/turbine_*_evaluation.joblib`: веса обучены до **01.12.2025**, декабрь — только калибровка интервалов; январь — holdout.
- `models/turbine_*.joblib`: после оценки веса переобучены на данных до **01.02.2026** для февраля/live. **Январские метрики относятся к evaluation-модели**, не к этому refit.

Интервалы `lower_power`, `upper_power` используют декабрьские квантили абсолютной ошибки отдельно для lead 1–24 и 25–48. Номинальное покрытие 90%; это эмпирические интервалы, **не гарантия 90%** при временной зависимости или сдвиге данных. Радиусы перенесены на deployment refit; его покрытие ещё не проверено на новых actuals.

## Baseline

Persistence повторяет последнее фактически известное значение мощности перед origin на весь горизонт. Никакие будущие actuals baseline не получает. Для февраля сохраняется `history_age_hours`, поскольку новых наблюдений нет. MAE, RMSE и R² считаются на том же наборе origin-target пар, что и ML. Normalized MAE совпадает с MAE, поскольку диапазон мощности равен единице.

## Backtesting methodology

**Январь:** origin ежедневно в 00:00 UTC+05:00, прогноз первых 48 часов начиная с origin. Это граница закрытия предыдущего дня: выпуск для 1 февраля соответствует закрытию 31 января. При origin `2026-02-01T00:00:00+05:00` первый target имеет UTC timestamp `2026-01-31T19:00:00Z` и `horizon=1`.

Каждый origin использует только завершённые исторические часы. Веса в течение оцениваемого месяца фиксированы: это rolling-origin backtest с обновлением доступной истории, без ежедневного retrain. January holdout: 1–31 января; 744 уникальных target-часа и 1 464 оцениваемые origin-target пары на турбину. Перекрывающиеся горизонты учитываются отдельно. Предсказания за границей оцениваемого месяца сохраняются, но не включаются в метрики.

**Февраль:** 28 origin × 48 часов × 2 турбины = **2 688 строк** `results/backtest_predictions.csv`. 48 строк относятся к target-часам 1 марта, вне февральского scoring window. Остальные 2 640 также не имеют фактических меток, потому что February SCADA не предоставлена. Значения `actual_power` и `error` пустые; статус — `unscored_missing_actuals`. После первого дня missing history остаётся missing, прогнозная мощность не выдаётся за наблюдение.

### Защита от data leakage

1. Никаких random train/test split. Train до декабря, calibration в декабре, test в январе.
2. Training rows с target за cutoff удаляются, включая конец 48-часового горизонта. Пересечения target между train/calibration/test нет.
3. `history.index < origin` до формирования lag/rolling. Среднее текущего незавершённого часа использовать нельзя.
4. Никакой интерполяции назад, full-dataset scaling или mean imputation по test.
5. В training и backtest weather — archived forecast, не future SCADA/reanalysis.
6. Predictor отвергает artifact, чьи training **или calibration** cutoffs позже origin.
7. Тест изменяет/добавляет будущую фактическую мощность и погоду на невозможные значения и проверяет, что features и prediction не меняются.
8. Production refit после января никогда не используется для январских метрик.

### Источник и доступность погоды

`services/weather_provider.py` реализует единый контракт `get_forecast(latitude, longitude, forecast_origin, horizon_hours)`.

В backtest применяется **Open-Meteo Previous Runs API**, `models=gfs_global`, `wind_speed_80m_previous_day3`, `temperature_2m_previous_day3`, `wind_speed_unit=ms`, `timezone=UTC`. Данные получены реальными HTTP-запросами, закэшированы по месяцу/координатам с URL и `retrieved_at`.

`previous_day3` — прогноз за 72 часа до target согласно документации провайдера. Для target от origin до origin+47h последнее референсное время не позднее origin−25h. Добавляем консервативный запас 12 часов на публикацию: `target−72h+12h <= origin`. Это намеренно более старый прогноз, чем самый свежий доступный запуск.

**Ограничение provenance:** API fixed-lead не возвращает точный run ID и фактический журнал публикации. Сохранена консервативная граница доступности по документированной семантике; точные исторические publication timestamps независимо не доказаны. Это не reanalysis и не seamless historical observations.

Исследован и Single Runs API. Его архив большинства моделей начинается после февраля 2026, а ранний ECMWF описан как hindcasts. Поэтому февральский результат не основан на таком hindcast. Для production нужен архив отдельных операционных запусков с issue/publication timestamps.

Источники:

- [Previous Runs API](https://open-meteo.com/en/docs/previous-runs-api)
- [Single Runs API и ограничения архивов](https://open-meteo.com/en/docs/single-runs-api)
- [Live Forecast API](https://open-meteo.com/en/docs)
- [Open-Meteo attribution/licence](https://open-meteo.com/en/licence), weather model: NOAA GFS, data delivery: Open-Meteo.

Live-режим получает текущий GFS forecast с теми же переменными и единицами, кэширует его на 30 минут. Архивный кэш не обновляется автоматически, чтобы повторные запуски были воспроизводимыми. Кэш live не делает его архивом для произвольных прошлых origin.

## Agentic AI architecture

`src/agents/forecast_agent.py` — детерминированный domain agent. После запроса цели «турбина + 24/48 часов» он сам вызывает инструменты и принимает решения по состоянию данных:

1. Загружает конфигурацию и выбирает replay/live provider.
2. Получает погоду с максимум тремя попытками и cache.
3. При недоступности NWP может выбрать **явно помеченный** persistence weather fallback; он разрешён только при наблюдениях не старше 24 часов. Иначе возвращается 503.
4. Проверяет timestamp coverage, физические пределы и свежесть истории; missing telemetry ведёт к weather/calendar-only inference, а не к выдуманным наблюдениям.
5. Создаёт features, загружает модель, проверяет training cutoff.
6. Прогнозирует, отвергает NaN/Inf, ограничивает нормализованную мощность [0,1], логирует коррекции и jumps >0.6. Jumps отмечаются, но не сглаживаются произвольно.
7. Проверяет response schema, сохраняет результат атомарно и возвращает JSON.
8. По POST с обновлённой погодой повторяет расчёт; SHA-256 входной погоды и `run_id` позволяют отличить версии.

Состояния: `IDLE → FETCHING_WEATHER → VALIDATING_DATA → PREPARING_FEATURES → RUNNING_MODEL → VALIDATING_FORECAST → COMPLETED`; при ошибке — `FAILED`. Каждый шаг имеет timestamp и сообщение. `GET /api/agent/status` можно опрашивать из frontend во время расчёта; sync handlers FastAPI выполняются в thread pool, status-запрос не ждёт завершения прогноза. Для одной турбины конкурентный расчёт получает 409.

OpenAI-агент в `src/agents/copilot.py` вызывает инструменты через Responses API, ограничен 7 обращениями и 10 вызовами tools. Численные результаты, временные ограничения и область действия устанавливает сервер. При сбое API возвращается явный `deterministic_recovery`, а не ложное подтверждение работы LLM.

`ForecastMonitor` внутри lifecycle FastAPI проверяет обе турбины каждые 30 минут. SHA-256 погоды, последних 24 часов истории, модели и параметров задаёт версию результата. Неизменные входы не создают новую опубликованную версию. Изменённые входы дают новую версию с отличиями по совпадающим целевым часам. Live cache истекает через 30 минут; архивный cache остаётся неизменным для воспроизводимости. Монитор не вызывает OpenAI и не расходует LLM-токены. Сервис рассчитан на **один uvicorn worker**, пока процесс запущен; JSON сохраняются на диске.

## API

Swagger UI: http://127.0.0.1:8000/docs. Схема: `/openapi.json`.

| Метод | Endpoint                                  | Назначение                                                            |
| ---------- | ----------------------------------------- | ------------------------------------------------------------------------------- |
| GET        | `/api/health`                           | liveness и`ready` для моделей/processed data                       |
| GET        | `/api/turbines`                         | конфигурации двух турбин                                  |
| GET        | `/api/turbines/{id}`                    | одна конфигурация                                               |
| GET        | `/api/forecast/{id}?hours=48`           | прогноз 24/48h                                                           |
| GET        | `/api/forecast/all?hours=48`            | прогнозы обеих турбин                                        |
| GET        | `/api/turbines/{id}/details?hours=48`   | полный JSON для клика по 3D-турбине                      |
| GET        | `/api/backtest/metrics`                 | февральский summary, включая null metrics                     |
| GET        | `/api/backtest/{id}?limit=200&offset=0` | пагинация прогнозов февраля                            |
| GET        | `/api/validation/metrics`               | реальные январские метрики                              |
| GET        | `/api/agent/status`                     | состояние и шаги обеих турбин                          |
| POST       | `/api/forecast/recalculate`             | повторный расчёт, опционально новая погода |

`id`: `turbine_1` или `turbine_2`. Query `mode=replay|live` доступен на forecast/details. Неизвестный id → 404, неверный horizon/тип → 422, конфликт выполнения → 409, отсутствующий artifact/недоступная погода → 503. Ошибки с custom forecast, обнаруженные weather validation, также возвращают 503; Pydantic-ошибки тела запроса — 422.

`details.current` означает **latest known SCADA**, не текущий live sensor. Содержит timestamp, `is_live=false`, `age_hours`. В `details.model` приведены январские метрики и явно назван evaluation artifact. Не выдавайте их пользователю как измеренное качество текущего live-прогноза.

`forecast_summary.peak_time` относится ко всему запрошенному горизонту; `next_24h_average` и `next_24h_peak` — только к первым 24 часам. Все JSON numbers конечны; missing результаты передаются как `null`.

Полный пример фронтенд-интеграции: [docs/frontend.md](docs/frontend.md). Реальные примеры ответов после smoke test: `results/example_replay_turbine_1.json`, `results/example_live_turbine_1.json` (содержат фактическое время проверки, не обновляются сами).

## Installation

Проверено на macOS arm64 / Python 3.9.6. Рекомендуется Python 3.9–3.12 с закреплёнными версиями зависимостей; другие версии и ОС в этой сессии не проверялись. Выполняйте команды из корня репозитория.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
test -f .env || cp .env.example .env
```

Для численного прогноза секреты не требуются. Для OpenAI укажите `OPENAI_API_KEY` в локальном `.env`; `.env` исключён из Git и Docker build context. Не перезаписывайте существующий `.env` командой копирования. Оригинальные данные, модели, processed данные и weather cache включены в проект для воспроизводимого запуска. Если их убрали из своей копии, верните CSV с исходной русской схемой в `data/raw/turbine_1.csv` и `data/raw/turbine_2.csv`.

## Running

Полный pipeline: EDA → обучение → January validation → February replay → графики → tests:

```bash
source .venv/bin/activate
python scripts/run_pipeline.py
```

С сохранённым weather cache полный расчёт не требует сети:

```bash
WEATHER_OFFLINE=true python scripts/run_pipeline.py
```

Отдельные команды:

```bash
python scripts/analyze_data.py
python scripts/fetch_weather.py --start 2024-01-01 --end 2026-03-03
python scripts/train_models.py
python scripts/run_backtest.py
python scripts/report_results.py
python -m pytest -q
```

`fetch_weather.py` необязателен: training/backtest сами получат отсутствующие cached месяцы. API start не запускает обучение скрыто.

Запуск backend:

```bash
uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

В другом терминале:

```bash
source .venv/bin/activate
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/turbines
curl 'http://127.0.0.1:8000/api/forecast/turbine_1?hours=48'
curl 'http://127.0.0.1:8000/api/forecast/turbine_2?hours=24'
curl 'http://127.0.0.1:8000/api/turbines/turbine_1/details?hours=48'
python scripts/smoke_api.py --live
```

Текущая погода и прогноз:

```bash
curl 'http://127.0.0.1:8000/api/forecast/turbine_1?hours=48&mode=live'
```

Пересчёт стандартной погоды:

```bash
curl -X POST http://127.0.0.1:8000/api/forecast/recalculate \
  -H 'Content-Type: application/json' \
  -d '{"turbine_id":"turbine_1","hours":48,"mode":"replay"}'
```

Пользовательскую новую погоду можно передать массивом `weather` (24/48 строк с aware timestamp, wind_speed, temperature), `weather_issued_at` и `forecast_origin`. Issue time обязан быть не позже origin. Это заявление вызывающей стороны; подлинность произвольного пользовательского прогноза независимо не проверяется.

CORS по умолчанию: localhost:3000, localhost:5173, 127.0.0.1:5173. Настройка — `CORS_ORIGINS` в `.env`.

## Results

**Фактический независимый период: январь 2026.** Веса обучены до декабря, интервалы откалиброваны на декабре. Горизонт 1–48h, одинаковые 1 464 пары на турбину:

| Turbine   | Baseline MAE | Model MAE |     RMSE |      R² |
| --------- | -----------: | --------: | -------: | -------: |
| Turbine 1 |     0.335164 |  0.246388 | 0.309170 | 0.156847 |
| Turbine 2 |     0.332802 |  0.255451 | 0.320662 | 0.094980 |

Снижение MAE относительно persistence: **26,49%** и **23,24%**. Это улучшение baseline, но абсолютная ошибка остаётся значительной; результат не следует трактовать как промышленную точность.

Файлы с реальными результатами:

- [results/RESULTS.md](results/RESULTS.md): summary и наблюдаемое покрытие prediction intervals.
- `results/metrics.json`, `results/validation_metrics.json`: metrics overall / 1–24h / 25–48h / каждый lead.
- `results/validation_predictions.csv`: сравнение с настоящими January actuals.
- `results/backtest_predictions.csv`: February forecasts, `actual_power`/`error` пустые.
- `results/backtest_metrics.json`: `unscored_missing_actuals`, n=0, metrics=null.
- `results/validation_forecasts.png`: actual/model/baseline и интервалы.
- `results/api_smoke_checks.json`: фактические HTTP-проверки.

## Tests

```bash
python -m pytest -q
```

Тесты используют реальные CSV, модели и cached погодные ответы, без сети. Проверяются CSV/schema, почасовое покрытие и anomalies, lag/rolling, будущие actuals, purge на cutoff, stale history, временная доступность прогнозов, полный horizon, finite/bounds, prediction schema, state/failure/lock, пересчёт при новой погоде, FastAPI/CORS, параметры и отсутствие выдуманных February actuals.

Для настоящего HTTP-процесса отдельно запустите uvicorn и `python scripts/smoke_api.py --live`. Это проверяет и текущий внешний weather API; если он недоступен, smoke test честно завершится ошибкой, а не засчитает fallback как live.

## Limitations

1. **February SCADA отсутствует.** Февральское качество и полноценное ежедневное обновление телеметрии проверить нельзя. Добавление новых данных должно сохранять evaluation cutoffs; не переобучайте модель на февральских labels перед February replay.
2. Fixed-lead weather archive даёт документированную границу доступности, не exact publication audit. Используется заведомо старый 72h прогноз; оптимальный свежий NWP run пока не выбирается.
3. Неизвестны hub height и rated power. GFS wind 80m — внешняя метеопеременная, не измеренная скорость на роторе. GFS grid coarse; две близкие турбины могут получить один grid cell. Это ограничивает качество.
4. Live forecasts имеют другое распределение lead-time, чем training; свежих SCADA observations после января нет. Live работает с missing-history режимом; его качество и интервалы не валидированы.
5. Prediction intervals приближённые. Refit, fallback, отсутствие истории и shift могут изменить покрытие.
6. Не моделируются curtailment, availability/fault flags, направление ветра, wake effects и задержки доставки SCADA. Частично покрытые часы (4/6+) могут давать смещение в target.
7. Агент — rule-based workflow, не LLM. Нет фонового расписания, распределённой очереди, базы состояний, auth и production observability. Рекомендуется один worker, локальный demo deployment. Нагрузочные и multi-worker проверки не выполнялись.
8. 3D frontend, облачная публикация, Docker и GitHub push не входят в выполненное backend-ядро.

## Future improvements

- Получить настоящие February actuals, SCADA availability и turbine metadata; повторно оценить frozen forecasts.
- Подключить архив конкретных operational NWP runs с publication times и обучить weather calibration на свежих lead-time.
- Добавить wind direction, NWP ensemble, availability/curtailment, измерения на hub height и probabilistic models.
- Проверить общую модель с turbine ID, сезонный walk-forward и несколько независимых test-периодов.
- Подключить live SCADA ingest, durable task queue, event stream для frontend и плановый пересчёт при новом NWP run.
