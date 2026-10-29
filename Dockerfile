FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies first (layer caching)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application source
COPY src/ src/

# Install the project itself
RUN uv sync --frozen --no-dev

# Set default bind address for container environments
ENV GOHOME_HOST=0.0.0.0
ENV GOHOME_PORT=8080

# Run as an unprivileged user. It only needs read access to /app and the
# read-only /config mount, so nothing is chowned.
RUN groupadd --system --gid 10001 gohome \
    && useradd --system --uid 10001 --gid gohome --no-create-home \
        --shell /usr/sbin/nologin gohome
USER gohome

EXPOSE 8080

# Healthcheck: the slim image has no curl or wget, so use python's urllib.
# Shell form so ${GOHOME_PORT} expands at run time. urlopen raises on
# connection errors, timeouts, and non-2xx responses, so python exits 1.
# --interval=30s   one request every 30s is cheap for this app
# --timeout=5s     the app answers in milliseconds; 5s means it is hung
# --start-period=10s  startup failures in this window do not count
# --start-interval=2s  probe every 2s during the start period, so the
#                      container turns healthy within seconds of starting
# --retries=3      three straight failures (about 90s) mark it unhealthy
# The probe always targets 127.0.0.1, so GOHOME_HOST must be 0.0.0.0 or
# 127.0.0.1 inside the container.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    --start-interval=2s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${GOHOME_PORT}/', timeout=4)"

# Call the venv interpreter directly so uv does not re-sync at startup.
CMD ["/app/.venv/bin/python", "-m", "gohome", "/config"]
