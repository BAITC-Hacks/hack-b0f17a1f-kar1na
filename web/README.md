# WindAI unified site

WindAI landing page + ML dashboard + original Three.js GLB and disassembly controls.

From the repository root:

```sh
npm ci --prefix web
npm run build --prefix web
.venv/bin/python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8001
```

Open http://127.0.0.1:8001/ (dashboard: /#overview). Install Python dependencies from requirements.txt first if needed. Build before starting FastAPI: it mounts web/dist at startup. The GLB is served at /models/wind_farm.glb.

For frontend development, run the backend on port 8000 and `npm run dev --prefix web`. Vite proxies /api and /models to that backend.

The site uses `/api/turbines/{id}/details`, `/api/history/{id}`, `/api/agent/status`, and POST `/api/forecast/recalculate`. Default replay starts 1 February 2026; Live requests current weather. All observation cards remain explicitly archived SCADA. The forecast slider feeds forecast wind speed to the selected turbine's existing controller; animation is illustrative, not measured RPM. Disassembly pauses that rotor until reassembled. Daily history hides days with fewer than 20 valid hourly samples per variable and preserves gaps. Power and metrics are normalized, never kW or kWh.

Failures show an error and a retry button; no synthetic forecast fallback is supplied by the frontend. Backend weather fallbacks and limitations are shown in the warning banner. Model inspection works even if the API is unavailable.

Verification: `python -m pytest -q`, `npm test --prefix 3d/web`, `npm run build --prefix web`.
