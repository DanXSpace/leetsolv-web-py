# Build the React SPA, then run FastAPI serving both the API and the SPA.
# The API and frontend must share an origin (httponly session cookie).

# ---- frontend build ----
FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- runtime ----
FROM python:3.12-slim
WORKDIR /app

# Install the backend package (deps + `app`, including the bundled metadata JSON).
COPY backend/ ./backend/
RUN pip install --no-cache-dir ./backend && rm -rf ./backend

COPY --from=frontend /app/frontend/dist ./frontend/dist

ENV LEETSOLV_DIST_DIR=/app/frontend/dist \
    LEETSOLV_DATABASE_URL=sqlite:////data/leetsolv.db \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# Listen on Railway's $PORT when present, else 8000.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
