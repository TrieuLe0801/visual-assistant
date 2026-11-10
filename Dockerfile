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

FROM python:3.11-slim-trixie AS app-build

COPY --from=ghcr.io/astral-sh/uv:0.12.19 /uv /uvx /bin/
ENV UV_PYTHON_DOWNLOADS=0 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

FROM python:3.11-slim-trixie AS app

RUN apt-get update && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && /usr/local/bin/python -m pip uninstall -y setuptools wheel \
    && /usr/local/bin/python -m pip uninstall -y pip
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src
WORKDIR /app
COPY --from=app-build /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY src/ ./src/

RUN useradd --system --uid 10001 --create-home studio \
    && mkdir -p /data \
    && chown studio:studio /data
USER studio

EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "image_studio.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
