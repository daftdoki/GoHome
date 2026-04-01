# GoHome

[![CI](https://github.com/daftdoki/gohome/actions/workflows/ci.yml/badge.svg)](https://github.com/daftdoki/gohome/actions/workflows/ci.yml)

A self-hosted go-links service for your [Tailscale](https://tailscale.com/)
network. Define your links and categories in YAML, deploy with Docker,
and access them instantly from any device on your tailnet via short URLs
like `go/link-name`, or browse the directory by going to `go/`. Categories
are supported, which you can navigate to by name via `go/category-name` to
browse just that category. Links and categories are defined in
`directory.yml`. The UI also supports visual themes.

## Table of Contents

- [Setup Guide](#setup-guide)
  - [Clone the Repository](#clone-the-repository)
  - [Create Your Configuration](#create-your-configuration)
  - [Set Up Tailscale](#set-up-tailscale)
  - [Start GoHome](#start-gohome)
- [User Guide](#user-guide)
  - [Browsing the Directory](#browsing-the-directory)
  - [Quick Redirects](#quick-redirects)
  - [Category Pages](#category-pages)
  - [Themes and Modes](#themes-and-modes)
- [Configuration Guide](#configuration-guide)
  - [Configuration Directory](#configuration-directory)
  - [directory.yml](#directoryyml)
  - [config.yml](#configyml)
  - [Custom Themes](#custom-themes)
  - [Deploying on Tailscale](#deploying-on-tailscale)
  - [Tailscale Troubleshooting](#tailscale-troubleshooting)
  - [Standalone Docker (without Tailscale)](#standalone-docker-without-tailscale)
  - [Running Directly with Python](#running-directly-with-python)
  - [Environment Variables](#environment-variables)
- [Developer Guide](#developer-guide)
  - [Development Prerequisites](#development-prerequisites)
  - [Development Setup](#development-setup)
  - [Running Locally](#running-locally)
  - [Testing](#testing)
  - [Linting and Formatting](#linting-and-formatting)
  - [Project Structure](#project-structure)
- [Screenshots](#screenshots)

## Setup Guide

This guide walks you through deploying GoHome on your Tailscale network
using Docker. By the end, `go/` will work from every device on your
tailnet.

**Prerequisites:** A [Tailscale account](https://login.tailscale.com/start),
[Docker](https://docs.docker.com/get-docker/) with Docker Compose, and
[Git](https://git-scm.com/downloads).

### Clone the Repository

Clone the GoHome repository to the machine where you will run the Docker
container. This downloads the project files to your machine:

```bash
git clone https://github.com/DaftDoki/GoHome.git
cd GoHome
```

All remaining commands in this guide assume you are in the `GoHome`
directory.

### Create Your Configuration

Create a `config` directory and copy the sample configuration files into
it:

```bash
mkdir config
cp sample_config/directory.yml config/directory.yml
cp sample_config/config.yml config/config.yml
```

Edit `config/directory.yml` to define your links. Here is a minimal
example with one link and one category:

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
`entries` to make it a category that groups links together. The
`description` field is optional.

> **Note:** GoHome reads `directory.yml` at startup. After editing this
> file, restart the application for changes to take effect — restart the
> Docker Compose stack (`docker compose restart`), the Docker container,
> or the Python process depending on how you are running it.

Names are automatically converted into URL-safe slugs for redirects:
the name is lowercased, spaces become hyphens, and special characters
are removed. A link named **My Cool Site** becomes `go/my-cool-site`.
See [directory.yml](#directoryyml) in the Configuration Guide for the
complete format and rules.

The `config.yml` file is optional — the defaults work out of the box.
See [config.yml](#configyml) in the Configuration Guide if you want to
customize settings like the site title or default theme.

### Set Up Tailscale

GoHome uses a Tailscale sidecar container to join your tailnet with the
hostname `go`. The container needs a Tailscale auth key to authenticate.

Generate a reusable auth key in the Tailscale admin console under
**Settings > Keys**. The key starts with `tskey-auth-`. See
[Deploying on Tailscale](#deploying-on-tailscale) in the Administrator
Guide for detailed instructions on creating the key.

Create a file at `config/tailscale.env` with your auth key:

```bash
TS_AUTHKEY=tskey-auth-YOUR-KEY-HERE
```

**Keep `tailscale.env` private.** The auth key grants access to your
tailnet. Do not commit it to version control or share it.

### Start GoHome

Copy the Tailscale Docker Compose file to `docker-compose.yml`. This
gives you a working copy you can customize without affecting the
original:

```bash
cp docker-compose.tailscale.yml docker-compose.yml
```

Start the service:

```bash
docker compose up -d
```

Open the
[Tailscale admin console](https://login.tailscale.com/admin/machines)
and confirm a machine named **go** has appeared. Then visit `go/` from
any device on your tailnet. Type `go/google` to test a redirect.

If something is not working, see
[Tailscale Troubleshooting](#tailscale-troubleshooting) in the
Administrator Guide.

## User Guide

### Browsing the Directory

Visit `go/` to see all links and categories. Links are displayed in the
order defined by the administrator. Categories group related links under
a heading.

### Quick Redirects

Type `go/` followed by a link's **slug** to redirect instantly. A slug
is the URL-friendly version of the name you see on the directory page —
lowercased, with spaces replaced by hyphens and special characters
removed. For example:

| Display name on page | Slug (what you type) |
| --- | --- |
| Google | `go/google` |
| Netflix | `go/netflix` |
| My Cool Site | `go/my-cool-site` |
| Bob's Links! | `go/bobs-links` |

Links inside categories work the same way — `go/netflix` redirects
even though Netflix is listed under Streaming.

### Category Pages

Append a category's slug to see only that section:

- `go/streaming` shows just the Streaming links
- A category called **Dev Tools** is reachable at `go/dev-tools`

### Themes and Modes

Use the footer controls to:

- **Switch themes** via the dropdown (persisted in a cookie)
- **Set light/dark/auto mode** via the Mode dropdown (persisted in a
  cookie); Auto follows the browser's `prefers-color-scheme` setting and
  is the default for all themes

## Configuration Guide

Detailed reference for configuring and deploying GoHome.

### Configuration Directory

GoHome reads configuration from a single directory containing:

```text
config_dir/
├── config.yml           # Optional application settings
├── directory.yml        # Required link directory
├── tailscale.env        # Tailscale auth key (for Tailscale deployment)
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

GoHome reads this file once at startup. After making changes, restart
the application for them to take effect:

- **Docker Compose:**
  `docker compose restart` (or `docker compose up -d` to recreate)
- **Standalone Docker:**
  `docker restart <container>` or stop and start the container
- **Python:** stop the running process and start it again

**Rules:**

- Every entry must have a `name`
- Entries must have either `url` (link) or `entries` (category)
- If both `url` and `entries` are present, it is treated as a category
- Category `entries` must not be empty
- Names must be globally unique after normalization (see below)
- Only one level of nesting is supported (nested categories are skipped)
- The `description` field is optional for both links and categories

**Slug normalization:** Each name is converted into a URL-safe slug
used for redirects and category pages. The rules are applied in order:

1. Lowercase the name
2. Replace spaces with hyphens
3. Remove all characters except letters, digits, and hyphens
4. Collapse consecutive hyphens into one
5. Strip leading and trailing hyphens

For example, `My Cool Site!` becomes `my-cool-site`, and users reach
it at `go/my-cool-site`. Because slugs must be unique, two entries
whose names normalize to the same slug (e.g. "My Link" and
"my-link") will cause a validation error at startup.

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

Themes use CSS custom properties for colors. Support light and dark
modes via `.light` and `.dark` body classes plus a
`prefers-color-scheme` media query fallback. See
`src/gohome/static/default.css` for the full reference.

### Deploying on Tailscale

The recommended way to run GoHome. A Tailscale sidecar container joins
your tailnet with hostname `go` and proxies traffic to GoHome, so
`go/link-name` works from every device on your network.

#### Prerequisites

- A [Tailscale account](https://login.tailscale.com/start) with
  [MagicDNS](https://tailscale.com/kb/1081/magicdns) enabled (on by
  default)
- Docker and Docker Compose
- A reusable
  [Tailscale auth key](https://login.tailscale.com/admin/settings/keys)

#### Setup

Generate an auth key in the Tailscale admin console under
**Settings > Keys**. Enable **Reusable** so the container can
re-authenticate after restarts. Optionally add a tag (e.g.,
`tag:gohome`).

Save the key in your config directory:

```bash
# config/tailscale.env
TS_AUTHKEY=tskey-auth-...
```

Start the stack:

```bash
docker compose -f docker-compose.tailscale.yml up -d
```

Confirm the machine appears as **go** in the
[admin console](https://login.tailscale.com/admin/machines), then visit
`go/` from any device on your tailnet.

#### How it works

```text
Browser on tailnet
  → go/link-name
  → Tailscale MagicDNS resolves "go" to the node IP
  → tailscale serve proxies port 80 → 127.0.0.1:8080
  → GoHome handles the request
```

The Compose file runs two containers sharing a network namespace:
**tailscale** (handles networking) and **gohome** (the application).
Tailscale encrypts all traffic between nodes, so plain HTTP on port 80
is sufficient.

### Tailscale Troubleshooting

**"go" does not resolve:**

- Confirm MagicDNS is enabled in the admin console under **DNS**
- Verify the device you are browsing from is connected to the same
  tailnet (`tailscale status`)
- Check that the GoHome machine shows as **go** in the admin console
- Some browsers treat short hostnames as search queries — try
  `http://go/` with the scheme explicitly included

**Container fails to join the tailnet:**

- Ensure `TS_AUTHKEY` is set in `tailscale.env` and has not expired
- Check logs:
  `docker compose -f docker-compose.tailscale.yml logs tailscale`
- If using ACL tags, verify the auth key is authorized for those tags

**Hostname "go" is already taken on the tailnet:**

This happens when a previous container or machine already registered
the `go` hostname — for example after moving to a new host or
recreating the stack without preserving the `ts-state` volume.
Tailscale treats the new container as a different node, so it gets a
suffix like `go-1`. To fix this:

1. Stop the current stack:
   `docker compose -f docker-compose.tailscale.yml down`
2. Open the
   [Tailscale admin console](https://login.tailscale.com/admin/machines)
3. Find the **stale** `go` machine (it will usually show as offline)
   and remove it via **...** > **Remove**
4. Delete the local Tailscale state so the container re-registers
   cleanly:
   `docker volume rm gohome_ts-state`
   (the volume name may differ — check with `docker volume ls`)
5. Restart the stack:
   `docker compose -f docker-compose.tailscale.yml up -d`
6. Confirm the machine appears as **go** in the admin console

If you anticipate moving the deployment between hosts, consider using a
reusable auth key with a tag so that re-registration is seamless.

**GoHome is not reachable:**

- Verify both containers are running:
  `docker compose -f docker-compose.tailscale.yml ps`
- Check GoHome logs:
  `docker compose -f docker-compose.tailscale.yml logs gohome`
- Ensure `network_mode: service:tailscale` is set — GoHome must share
  the Tailscale container's network

### Standalone Docker (without Tailscale)

If you do not use Tailscale, you can run GoHome as a plain Docker
container.

**Quick preview with sample data** — the included
`docker-compose.example.yml` is preconfigured to use the bundled sample
directory, so you can see the app immediately with zero configuration:

```bash
docker compose -f docker-compose.example.yml up -d
```

Open `http://localhost:8080` to see the sample directory.

**Custom config without Tailscale** — if you have your own
`config/directory.yml`, use a compose file like:

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

```bash
docker compose up -d
```

The directory is available at `http://<host>:8080`.

### Running Directly with Python

For the quickest possible preview, you can run GoHome directly with
Python using the bundled sample configuration. No Docker required.

**Prerequisites:** Python 3.14+ and
[uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run python -m gohome sample_config/
```

Open `http://localhost:8080`. This uses the sample links in
`sample_config/directory.yml`.

To use your own configuration, pass the path to your config directory
instead:

```bash
uv run python -m gohome config/
```

See the [Developer Guide](#developer-guide) for the full development
setup including testing and linting.

### Environment Variables

Environment variables override `config.yml` values. This is especially
useful when running in Docker containers where you may not want to mount
a config file.

| Variable | Overrides | Default |
| --- | --- | --- |
| `GOHOME_SITE_TITLE` | `site_title` | `GoHome` |
| `GOHOME_HOST` | `host` | `0.0.0.0` |
| `GOHOME_PORT` | `port` | `8080` |
| `GOHOME_LOG_LEVEL` | `log_level` | `info` |
| `GOHOME_DEFAULT_THEME` | `default_theme` | `default` |

Priority: environment variables > config.yml > built-in defaults.

For example, to override the site title and default theme in a Docker
Compose file:

```yaml
services:
  gohome:
    build: .
    environment:
      GOHOME_SITE_TITLE: "My Links"
      GOHOME_DEFAULT_THEME: "retro-green"
    volumes:
      - ./config:/config:ro
```

## Developer Guide

### Development Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) for dependency management
- [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2)
  for Markdown linting
- [yamllint](https://github.com/adrienverdelhan/yamllint) for YAML
  linting

### Development Setup

```bash
uv sync --all-extras
```

### Running Locally

Start a local development server to preview changes while editing your
`directory.yml` or working on the codebase:

```bash
uv run python -m gohome sample_config/
```

The server starts at `http://localhost:8080`.

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
