# Build from the repository root: docker build -f deploy/Dockerfile .
# Secrets are runtime-only. Never add secret ARGs or copy an environment file.
FROM node:22-bookworm-slim AS frontend
WORKDIR /build/frontend
RUN npm install --global pnpm@10.20.0
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build

FROM python:3.12-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000 \
    EASY_STREET_DEMO_DATA_DIR=/var/lib/easy-street
WORKDIR /app
COPY backend/requirements-lock.txt /tmp/requirements-lock.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements-lock.txt \
    && groupadd --gid 10001 easy-street \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin easy-street \
    && mkdir -p /var/lib/easy-street \
    && chown 10001:10001 /var/lib/easy-street
COPY --chown=10001:10001 backend/ ./backend/
COPY --chown=10001:10001 scripts/demo_healthcheck.py ./scripts/demo_healthcheck.py
COPY --chown=10001:10001 LICENSE THIRD_PARTY_NOTICES.txt ./
COPY --from=frontend --chown=10001:10001 /build/frontend/dist ./frontend/dist
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=15s --start-period=30s --retries=3 \
    CMD ["python", "scripts/demo_healthcheck.py", "--url", "http://127.0.0.1:8000"]
CMD ["sh", "-c", "exec python -m uvicorn backend.judging_app:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --no-access-log --log-level warning"]
