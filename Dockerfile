FROM node:22-bookworm-slim AS frontend
WORKDIR /app/web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY scripts ./scripts
COPY data ./data
COPY models ./models
COPY results ./results
COPY 3d/models ./3d/models
COPY --from=frontend /app/web/dist ./web/dist
ENV FORECAST_MODE=replay WEATHER_ALLOW_FALLBACK=false AGENT_MONITOR_ENABLED=true
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
