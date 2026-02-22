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

EXPOSE 8080

CMD ["uv", "run", "python", "-m", "gohome", "/config"]
