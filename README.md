# GoHome

[![CI](https://github.com/daftdoki/gohome/actions/workflows/ci.yml/badge.svg)](https://github.com/daftdoki/gohome/actions/workflows/ci.yml)

A self-hosted go-links service for your
[Tailscale](https://tailscale.com/) tailnet. Do you find yourself trying
to remember what port that weird device's web UI was on three months
after you set it up? Does typing a long hostname really inconvenience
you? If you're bothered by trivial things and would rather just remember
to type `go/nas` or `go/arr` into your web browser then this project is
here to free you from these trivial shackles.

Define links and categories in YAML, deploy with Docker, and access
them from any device on your tailnet via short URLs like
`go/link-name`. Browse the full directory at
`go/`, or filter by category at `go/category-name`. See
[Screenshots](#screenshots) for examples of the directory view.

## Setup Guide

Deploy GoHome on your Tailscale network using Docker. By the end,
`go/` will work from every device on your tailnet.

**Prerequisites:** A [Tailscale account](https://login.tailscale.com/start),
[Docker](https://docs.docker.com/get-docker/) with Docker Compose, and
[Git](https://git-scm.com/downloads).

### Clone the Repository

```bash
git clone https://github.com/DaftDoki/GoHome.git
cd GoHome
```

All remaining commands assume you are in the `GoHome` directory.

### Create Your Configuration

```bash
mkdir config
cp sample_config/directory.yml config/directory.yml
cp sample_config/config.yml config/config.yml
```

Edit `config/directory.yml` to define your links:

```yaml
---
directory:
  - name: Google
    url: https://google.com
    description: The world's most popular search engine

  - name: Streaming
    description: Video streaming services
    entries:
      - name: Netflix
        url: https://netflix.com
      - name: YouTube
        url: https://youtube.com
```

Each entry needs a `name`. Add a `url` to make it a link, or add
`entries` to make it a category. The `description` field is optional.

> **Note:** GoHome reads `directory.yml` at startup. Restart the
> application after editing for changes to take effect.

Names are converted into URL-safe slugs for redirects (e.g., **My Cool
Site** becomes `go/my-cool-site`). See
[Slug normalization](#slug-normalization) for full rules.

The `config.yml` file is optional — defaults work out of the box. See
[config.yml](#configyml) to customize settings like the site title or
default theme.

### Set Up Tailscale

GoHome uses a Tailscale sidecar container to join your tailnet with the
hostname `go`. Generate a reusable auth key in the Tailscale admin
console under **Settings > Keys** and save it:

```bash
# config/tailscale.env
TS_AUTHKEY=tskey-auth-YOUR-KEY-HERE
```

**Keep `tailscale.env` private.** Do not commit it to version control.

### Start GoHome

```bash
cp docker-compose.tailscale.yml docker-compose.yml
docker compose up -d
```

Confirm a machine named **go** appears in the
[Tailscale admin console](https://login.tailscale.com/admin/machines),
then visit `go/` from any device on your tailnet.

If something is not working, see
[Tailscale Troubleshooting](#tailscale-troubleshooting).

## User Guide

### Browsing the Directory

Visit `go/` to see all links and categories, displayed in the order
defined by the administrator.

### Quick Redirects

Type `go/` followed by a link's [slug](#slug-normalization) to
redirect instantly:

| Display name | URL |
| --- | --- |
| Google | `go/google` |
| My Cool Site | `go/my-cool-site` |
| Bob's Links! | `go/bobs-links` |

Links inside categories work the same way — `go/netflix` redirects
even though Netflix is listed under Streaming.

### Category Pages

Use a category's slug to see only that section — `go/streaming` shows
just the Streaming links, `go/dev-tools` shows Dev Tools.

### Themes and Modes

Use the footer controls to switch themes (dropdown) and set
light/dark/auto mode. Preferences are stored in cookies. Auto follows
the browser's `prefers-color-scheme` setting and is the default.

## Configuration Guide

### Configuration Directory

GoHome reads configuration from a single directory:

```text
config_dir/
├── config.yml           # Optional application settings
├── directory.yml        # Required link directory
├── tailscale.env        # Tailscale auth key (for Tailscale deployment)
└── themes/              # Optional custom theme CSS files
    └── nord.css
```

### directory.yml

See the [Setup Guide](#create-your-configuration) for the basic format
and an example.

**Rules:**

- Every entry must have a `name`
- Entries must have either `url` (link) or `entries` (category)
- If both `url` and `entries` are present, it is treated as a category
- Category `entries` must not be empty
- Names must be globally unique after slug normalization
- Only one level of nesting is supported (nested categories are skipped)
- The `description` field is optional for both links and categories

#### Slug normalization

Each name is converted into a URL-safe slug. The rules, applied in
order:

1. Lowercase the name
2. Replace spaces with hyphens
3. Remove all characters except letters, digits, and hyphens
4. Collapse consecutive hyphens into one
5. Strip leading and trailing hyphens

Because slugs must be unique, two entries whose names normalize to the
same slug (e.g., "My Link" and "my-link") cause a validation error at
startup.

#### Restarting after changes

GoHome reads `directory.yml` once at startup. After making changes:

- **Docker Compose:** `docker compose restart`
- **Standalone Docker:** `docker restart <container>`
- **Python:** stop and restart the process

### config.yml

All settings are optional with sensible defaults:

```yaml
site_title: "GoHome"       # Browser tab and header title
host: "0.0.0.0"            # Bind address
port: 8080                  # Bind port
log_level: "info"           # debug, info, warning, error
default_theme: "default"    # Theme for first-time visitors
```

Every setting can also be overridden with an environment variable — see
[Environment Variables](#environment-variables).

### Custom Themes

Place `.css` files in the `themes/` subdirectory. Each file becomes a
selectable theme named after the file (e.g., `themes/nord.css` creates
theme "nord"). Themes must be fully self-contained — they do not
inherit from the default theme.

Use CSS custom properties for colors. Support light and dark modes via
`.light` and `.dark` body classes plus a `prefers-color-scheme` media
query fallback. See `src/gohome/static/default.css` for the full
reference.

### Deploying on Tailscale

The recommended deployment method. A Tailscale sidecar container joins
your tailnet with hostname `go` and proxies traffic to GoHome. The
Compose file runs two containers sharing a network namespace:
**tailscale** (networking) and **gohome** (application). Tailscale
encrypts all traffic between nodes, so plain HTTP on port 80 is
sufficient.

**Prerequisites:** A [Tailscale account](https://login.tailscale.com/start)
with [MagicDNS](https://tailscale.com/kb/1081/magicdns) enabled,
Docker with Docker Compose, and a reusable
[auth key](https://login.tailscale.com/admin/settings/keys).

See the [Setup Guide](#set-up-tailscale) for step-by-step instructions.

### Tailscale Troubleshooting

**"go" does not resolve:**
Confirm MagicDNS is enabled, verify the browsing device is on the same
tailnet (`tailscale status`), and check that the machine shows as **go**
in the admin console. Some browsers treat short hostnames as search
queries — try `http://go/` explicitly.

**Container fails to join the tailnet:**
Ensure `TS_AUTHKEY` in `tailscale.env` has not expired. Check logs with
`docker compose logs tailscale`. If using ACL tags, verify the auth key
is authorized for those tags.

**Hostname "go" is already taken:**
A previous container may have registered the hostname. Remove the stale
machine in the admin console, delete the local state volume
(`docker volume rm gohome_ts-state`), and restart the stack. See
[docs/troubleshooting.md](docs/troubleshooting.md) for detailed steps.

**GoHome is not reachable:**
Verify both containers are running (`docker compose ps`), check GoHome
logs (`docker compose logs gohome`), and ensure
`network_mode: service:tailscale` is set in the Compose file.

### Standalone Docker (without Tailscale)

**Quick preview with sample data:**

```bash
docker compose -f docker-compose.example.yml up -d
# Open http://localhost:8080
```

**Custom config without Tailscale:**

```yaml
# docker-compose.yml
services:
  gohome:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./config:/config:ro
```

### Running Directly with Python

No Docker required. Requires Python 3.14+ and
[uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run python -m gohome sample_config/
# Open http://localhost:8080
```

Pass your own config directory instead of `sample_config/` to use
custom links. See the [Developer Guide](#developer-guide) for the full
development setup.

### Environment Variables

Environment variables override `config.yml` values (priority:
env vars > config.yml > built-in defaults):

| Variable | Overrides | Default |
| --- | --- | --- |
| `GOHOME_SITE_TITLE` | `site_title` | `GoHome` |
| `GOHOME_HOST` | `host` | `0.0.0.0` |
| `GOHOME_PORT` | `port` | `8080` |
| `GOHOME_LOG_LEVEL` | `log_level` | `info` |
| `GOHOME_DEFAULT_THEME` | `default_theme` | `default` |

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

### Running Locally

```bash
uv run python -m gohome sample_config/
# Server starts at http://localhost:8080
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
yamllint sample_config/ docker-compose.example.yml docker-compose.tailscale.yml
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

## Screenshots

| Theme | Light | Dark |
| --- | --- | --- |
| Default | ![Default light](docs/screenshots/default-light.png) | ![Default dark](docs/screenshots/default-dark.png) |
| Retro Green | ![Retro green light](docs/screenshots/retro-green-light.png) | ![Retro green dark](docs/screenshots/retro-green-dark.png) |
| Retro Amber | ![Retro amber light](docs/screenshots/retro-amber-light.png) | ![Retro amber dark](docs/screenshots/retro-amber-dark.png) |
| Retro ANSI | ![Retro ANSI light](docs/screenshots/retro-ansi-light.png) | ![Retro ANSI dark](docs/screenshots/retro-ansi-dark.png) |
