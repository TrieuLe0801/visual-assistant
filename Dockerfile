FROM node:24-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM nginx:stable-alpine AS frontend

COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-build /app/frontend/dist/ /usr/share/nginx/html/
EXPOSE 80

FROM python:3.10-slim-bookworm AS app

COPY --from=ghcr.io/astral-sh/uv:0.12.19 /uv /uvx /bin/
ENV UV_PYTHON_DOWNLOADS=0 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
ENV PATH="/app/.venv/bin:$PATH"
COPY src/ ./src/

RUN useradd --system --uid 10001 --create-home studio \
    && mkdir -p /data \
    && chown studio:studio /data
USER studio

EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "image_studio.app:app", "--host", "0.0.0.0", "--port", "8000"]
