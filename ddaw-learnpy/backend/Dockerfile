# ---------- Stage 1: builder ----------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /build
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# ---------- Stage 2: runtime ----------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/usr/local/bin:$PATH \
    DEBIAN_FRONTEND=noninteractive

# Install only minimal runtime libs needed by psycopg2-binary
RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd -r learnpy && useradd -r -g learnpy learnpy

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app
RUN chown learnpy:learnpy /app
COPY --chown=learnpy:learnpy pytest.ini .
COPY --chown=learnpy:learnpy app ./app

USER learnpy

EXPOSE 8000

# Use uvicorn directly. For prod-ish setup we run a single worker;
# scale horizontally by running multiple containers behind a reverse proxy.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
