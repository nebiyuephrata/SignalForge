FROM node:20-bookworm-slim AS frontend-build
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


FROM python:3.12-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/ ./agent/
COPY backend/ ./backend/
COPY data/ ./data/
COPY eval/ ./eval/
COPY logs/ ./logs/
COPY outputs/ ./outputs/
COPY probes/ ./probes/
COPY frontend/package.json ./frontend/package.json
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
