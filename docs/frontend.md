# Интеграция 3D dashboard

Base URL: `http://127.0.0.1:8000`. Turbine IDs: `turbine_1`, `turbine_2`. Не храните в frontend прогнозы из README: получайте реальные JSON из API.

```javascript
const API = 'http://127.0.0.1:8000';

async function onTurbineClick(id, mode = 'replay') {
  const response = await fetch(`${API}/api/turbines/${id}/details?hours=48&mode=${mode}`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail ?? 'Forecast request failed');
  }
  const details = await response.json();
  // details.forecast: timestamp, predicted_power, wind_speed, temperature,
  // lower_power, upper_power. Plot UTC or explicitly convert to UTC+05.
  // details.current is latest known SCADA, NOT live telemetry.
  // Display details.mode, current.timestamp/age_hours and details.warnings.
  // A normalized value 0.74 can be displayed as 74%; it is not 0.74 MW.
  return details;
}

const statusTimer = setInterval(async () => {
  const response = await fetch(`${API}/api/agent/status`);
  if (response.ok) {
    const { agents } = await response.json();
    // agents[id].status and agents[id].steps are actual backend state.
    // Each step contains timestamp/state/message. No synthetic progress percentage.
    console.debug(agents);
  }
}, 500);
// On component unmount: clearInterval(statusTimer).

async function recalculate(id) {
  const response = await fetch(`${API}/api/forecast/recalculate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ turbine_id: id, hours: 48, mode: 'live' }),
  });
  if (!response.ok) throw new Error((await response.json()).detail);
  return response.json();
}
```

Для актуального прогноза используйте mode=live. Для воспроизводимой защиты перед жюри mode=replay соответствует origin 2026-02-01 00:00 UTC+05. `generated_at` — реальное время вычисления, `forecast_origin` — моделируемый момент выпуска; это разные понятия.

Объект `model` содержит метрики **January evaluation model**, причём deployment weights переобучены после января. Для February summary используйте `/api/backtest/metrics`; показывайте «Нет фактических данных», если `status=unscored_missing_actuals`. Не превращайте null метрики в нули.

`forecast_summary.next_24h_average` и `.next_24h_peak` относятся к первым 24 часам; `.peak_time` и `.horizon_peak` — к полному горизонту. Интервалы nominal 90% эмпирические; предупреждения о stale history и fallback должны оставаться видимыми.

При 409 дождитесь завершения текущего run_id, при 503 покажите detail; retry должен быть ограниченным. API в MVP запускается одним worker. CORS-origin настраивается через `.env`.
