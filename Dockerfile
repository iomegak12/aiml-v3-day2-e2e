# syntax=docker/dockerfile:1
# NetCore TAC ETA API — slim, multi-stage, non-root image.
# Build context: day2/   Prerequisite: uv run python scripts/train_model.py

# ---------- builder: virtualenv with pinned runtime dependencies ----------
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.9.16 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    VIRTUAL_ENV=/opt/venv

WORKDIR /build

# The model is baked into the image: fail early with a clear message if it is missing
COPY models/ models/
RUN test -f models/eta_model.joblib && test -f models/eta_model.json || \
    { echo "ERROR: models/eta_model.joblib or models/eta_model.json not found." \
           "Run 'uv run python scripts/train_model.py' first, then rebuild." >&2; exit 1; }

RUN uv venv /opt/venv
COPY requirements.lock .
# Library test suites (pandas, scipy, scikit-learn, …) are never imported at runtime: drop them
RUN uv pip install --python /opt/venv/bin/python --no-cache -r requirements.lock && \
    find /opt/venv/lib -type d -name tests -prune -exec rm -rf {} +

COPY pyproject.toml README.md LICENSE ./
COPY src/ src/
RUN uv pip install --python /opt/venv/bin/python --no-cache --no-deps .

# ---------- runtime: only the venv, the source and the model ----------
FROM python:3.12-slim AS runtime

ARG APP_UID=10001
RUN groupadd --system --gid ${APP_UID} app && \
    useradd --system --uid ${APP_UID} --gid app --no-create-home --shell /usr/sbin/nologin app

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    LOG_LEVEL=info

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=root:root src/ src/
COPY --from=builder --chown=root:root /build/models/eta_model.joblib /build/models/eta_model.json models/

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --start-interval=2s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT', '8000'), timeout=3)"

# Single worker: the rate limiter counts per process. --no-proxy-headers: the app
# decides itself whether to trust X-Forwarded-For (TRUST_PROXY_HEADERS).
CMD ["sh", "-c", "exec uvicorn netcore_tac.api.main:app --host \"$HOST\" --port \"$PORT\" --log-level \"$LOG_LEVEL\" --workers 1 --no-proxy-headers"]
