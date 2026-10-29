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

# Call the venv interpreter directly so uv does not re-sync at startup.
CMD ["/app/.venv/bin/python", "-m", "gohome", "/config"]
