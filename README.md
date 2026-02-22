# GoHome

A self-hosted link directory and redirector service. Configure your
links and categories in YAML, deploy with Docker, and access them
instantly via short URLs like `go/link-name`.

## Quick Start

### With Docker Compose

```bash
cp docker-compose.example.yml docker-compose.yml
docker compose up
```

Open <http://localhost:8080> to see the sample directory.

### Without Docker

Requires Python 3.14+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-extras
uv run python -m gohome sample_config/
```

## Screenshots

### Default Theme

| Light | Dark |
| --- | --- |
| ![Default theme, light mode](docs/screenshots/default-light.png) | ![Default theme, dark mode](docs/screenshots/default-dark.png) |

### Retro Green Theme

| Light | Dark |
| --- | --- |
| ![Retro green phosphor theme, light mode](docs/screenshots/retro-green-light.png) | ![Retro green phosphor theme, dark mode](docs/screenshots/retro-green-dark.png) |

### Retro Amber Theme

| Light | Dark |
| --- | --- |
| ![Retro amber phosphor theme, light mode](docs/screenshots/retro-amber-light.png) | ![Retro amber phosphor theme, dark mode](docs/screenshots/retro-amber-dark.png) |

### Retro ANSI Theme

| Light | Dark |
| --- | --- |
| ![Retro ANSI terminal theme, light mode](docs/screenshots/retro-ansi-light.png) | ![Retro ANSI terminal theme, dark mode](docs/screenshots/retro-ansi-dark.png) |

## User Guide

### Browsing the Directory

Visit the root URL to see all links and categories. Links are displayed
in the order defined by the administrator. Categories group related
links under a heading.

### Quick Redirects

Append a link name to the URL to redirect instantly:

- `go.example.com/google` redirects to Google
- `go.example.com/netflix` redirects to Netflix (even if nested in a
  category)

URL lookup is case-insensitive. Spaces in names become hyphens
(`My Link` becomes `my-link`).

### Category Pages

Append a category name to see only that section:

- `go.example.com/streaming` shows just the Streaming links

### Themes and Modes

Use the footer controls to:

- **Switch themes** via the dropdown (persisted in a cookie)
- **Set light/dark/auto mode** via the Mode dropdown (persisted in a
  cookie); Auto follows the browser's `prefers-color-scheme` setting and
  is the default for all themes

## Administrator Guide

### Configuration Directory

GoHome reads configuration from a single directory containing:

```text
config_dir/
├── config.yml           # Optional application settings
├── directory.yml        # Required link directory
└── themes/              # Optional custom theme CSS files
    ├── nord.css
    └── dracula.css
```

### directory.yml

The directory file defines all links and categories:

```yaml
directory:
  - name: Google
    url: https://google.com
    description: The world's most popular search engine

  - name: Streaming
    description: Video streaming services
    entries:
      - name: Netflix
        url: https://netflix.com
        description: Movies and TV shows

  - name: Kagi
    url: https://kagi.com
```

**Rules:**

- Every entry must have a `name`
- Entries must have either `url` (link) or `entries` (category)
- If both `url` and `entries` are present, it is treated as a category
- Category `entries` must not be empty
- Names must be globally unique after normalization
- Only one level of nesting is supported (nested categories are skipped)
- The `description` field is optional for both links and categories

### config.yml

All settings are optional with sensible defaults:

```yaml
site_title: "GoHome"       # Browser tab and header title
host: "0.0.0.0"            # Bind address
port: 8080                  # Bind port
log_level: "info"           # debug, info, warning, error
default_theme: "default"    # Theme for first-time visitors
```

### Custom Themes

Place `.css` files in the `themes/` subdirectory. Each file becomes a
selectable theme named after the file (e.g., `themes/nord.css` creates
theme "nord"). Themes must be fully self-contained — they do not
inherit from the default theme.

Themes use CSS custom properties for colors. Support light and dark
modes via `.light` and `.dark` body classes plus a
`prefers-color-scheme` media query fallback. See
`src/gohome/static/default.css` for the full reference.

### Docker Deployment

```yaml
# docker-compose.yml
services:
  gohome:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./my_config:/config:ro
```

### Environment Variables

Environment variables override `config.yml` values:

| Variable | Overrides | Default |
| --- | --- | --- |
| `GOHOME_HOST` | `host` | `0.0.0.0` |
| `GOHOME_PORT` | `port` | `8080` |

Priority: environment variables > config.yml > built-in defaults.

## Developer Guide

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) for dependency management
- [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2)
  for Markdown linting
- [yamllint](https://github.com/adrienverdelhan/yamllint) for YAML
  linting

### Setup

```bash
uv sync --all-extras
```

### Running

```bash
uv run python -m gohome sample_config/
```

### Testing

```bash
uv run pytest              # Full test suite
uv run pytest -v           # Verbose output
uv run pytest tests/test_integration.py -v  # Integration tests only
```

### Linting and Formatting

All checks must pass before committing:

```bash
uv run ruff format src/ tests/ scripts/
uv run ruff check --fix src/ tests/ scripts/
uv run mypy src/
uv run pytest
markdownlint-cli2 "**/*.md"
yamllint sample_config/ docker-compose.example.yml
```

### Project Structure

```text
src/gohome/
├── __init__.py      # App factory (create_app)
├── __main__.py      # CLI entry point
├── config.py        # Config loading and validation
├── models.py        # Frozen dataclasses
├── normalize.py     # Name-to-slug normalization
├── routes.py        # Flask route handlers
├── themes.py        # Theme discovery
├── templates/
│   └── base.html    # Single Jinja2 template
└── static/
    ├── default.css      # Bundled default theme
    ├── retro-green.css  # Bundled retro green phosphor theme
    ├── retro-amber.css  # Bundled retro amber phosphor theme
    ├── retro-ansi.css   # Bundled retro ANSI/arcade theme
    ├── favicon.ico      # Favicon
    └── gohome.js        # Client-side theme/mode JS
```
