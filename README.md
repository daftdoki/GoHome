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

This is a shameless and less capable and imaginative spin on the
tailscale [golink](https://tailscale.com/blog/golink) open source
project.

## Table of Contents

- [Setup Guide (Tailscale)](#setup-guide)
- [Standalone Docker (without Tailscale)](#standalone-docker)
- [User Guide](#user-guide)
- [Configuration Reference](#configuration-reference)
- [Troubleshooting](#troubleshooting)
- [Developer Guide](#developer-guide)
- [Screenshots](#screenshots)

## Setup Guide

Deploy GoHome on your Tailscale network using Docker. By the end,
`go/` will work from every device on your tailnet. No build tools
are required — you will pull a prebuilt image from the GitHub
Container Registry.

**Prerequisites:**

- A [Tailscale account](https://login.tailscale.com/start) with
  [MagicDNS](https://tailscale.com/kb/1081/magicdns) enabled
  (on by default)
- [Docker](https://docs.docker.com/get-docker/) with Docker Compose
- A reusable Tailscale
  [auth key](https://login.tailscale.com/admin/settings/keys)

### Step 1: Create a Project Directory

```bash
mkdir -p gohome/config gohome/tailscale
cd gohome
```

### Step 2: Download the Docker Compose File

Download the Compose file or create it manually. This file runs two
containers: a Tailscale sidecar that joins your tailnet, and GoHome
itself.

```bash
curl -fLO https://raw.githubusercontent.com/DaftDoki/GoHome/main/docker-compose.yml
```

<details>
<summary>View file contents</summary>

```yaml
---
services:
  tailscale:
    image: tailscale/tailscale:latest
    env_file:
      - ./config/tailscale.env
    environment:
      TS_HOSTNAME: "go"
      TS_STATE_DIR: "/var/lib/tailscale"
      TS_SERVE_CONFIG: "/config/serve.json"
    volumes:
      - ts-state:/var/lib/tailscale
      - ./tailscale/serve.json:/config/serve.json:ro
    cap_add:
      - NET_ADMIN
      - NET_RAW
    restart: unless-stopped

  gohome:
    image: ghcr.io/daftdoki/gohome:latest
    network_mode: "service:tailscale"
    environment:
      GOHOME_HOST: "127.0.0.1"
    volumes:
      - ./config:/config:ro
    restart: unless-stopped

volumes:
  ts-state:
```

</details>

### Step 3: Download the Tailscale Serve Configuration

This tells Tailscale how to route incoming traffic to GoHome.

```bash
curl -fLo tailscale/serve.json \
  https://raw.githubusercontent.com/DaftDoki/GoHome/main/tailscale/serve.json
```

<details>
<summary>View file contents</summary>

```json
{
  "TCP": {
    "80": {
      "HTTP": true
    }
  },
  "Web": {
    "${TS_CERT_DOMAIN}:80": {
      "Handlers": {
        "/": {
          "Proxy": "http://127.0.0.1:8080"
        }
      }
    }
  }
}
```

</details>

### Step 4: Create Your Link Directory

Download the sample directory file and edit it with your own links.

```bash
curl -fLo config/directory.yml \
  https://raw.githubusercontent.com/DaftDoki/GoHome/main/sample_config/directory.yml
```

<details>
<summary>View file contents</summary>

```yaml
---
directory:
  - name: Google
    url: https://google.com
    description: The world's most popular search engine
    aliases:
      - search

  - name: Wikipedia
    url: https://wikipedia.org
    description: The free encyclopedia
    aliases:
      - wiki

  - name: Streaming
    description: A category for streaming services
    entries:
      - name: Netflix
        url: https://netflix.com
        description: Movies and TV shows on demand
      - name: YouTube
        url: https://youtube.com
        description: Free video sharing platform
        aliases:
          - yt

  - name: Kagi
    url: https://kagi.com
    description: A premium search engine focused on quality results

  - name: Development
    description: Tools and resources for software development
    entries:
      - name: GitHub
        url: https://github.com
        description: Code hosting and collaboration platform
        aliases:
          - gh
      - name: Stack Overflow
        url: https://stackoverflow.com
        description: Q&A for programmers
        aliases:
          - so
          - stackoverflow
```

</details>

Open `config/directory.yml` in a text editor and replace the sample
entries with your own links. Each entry needs a `name`. Add a `url`
to make it a link, or add `entries` to make it a category that groups
links together. The `description` and `aliases` fields are optional.

Use `aliases` to create shorthand URLs for a link — for example, the
sample config sets `search` as an alias for Google, so both
`go/google` and `go/search` reach the same destination. Aliases are
displayed in the web UI for discoverability.

A minimal file with just one link looks like this:

```yaml
---
directory:
  - name: My NAS
    url: http://nas.local:5000
    aliases:
      - nas
```

Names and aliases are automatically converted into URL-safe slugs —
**My NAS** becomes `go/my-nas`. See
[Slug normalization](#slug-normalization) for the full rules.

### Step 5: Set Up Your Tailscale Auth Key

Generate a reusable auth key in the
[Tailscale admin console](https://login.tailscale.com/admin/settings/keys)
under **Settings > Keys**. Enable **Reusable** so the container can
re-authenticate after restarts.

Create the environment file with your key:

```bash
curl -fLo config/tailscale.env \
  https://raw.githubusercontent.com/DaftDoki/GoHome/main/sample_config/tailscale.env.example
```

<details>
<summary>View file contents</summary>

```bash
# Paste your Tailscale auth key below.
# Generate one at: https://login.tailscale.com/admin/settings/keys
# Enable "Reusable" so the container can re-authenticate after
# restarts.
TS_AUTHKEY=tskey-auth-PASTE-YOUR-KEY-HERE
```

</details>

Open `config/tailscale.env` and replace
`tskey-auth-PASTE-YOUR-KEY-HERE` with your actual auth key.

**Keep `tailscale.env` private.** It grants access to your tailnet.

### Step 6: Start GoHome

```bash
docker compose up -d
```

Confirm a machine named **go** appears in the
[Tailscale admin console](https://login.tailscale.com/admin/machines),
then visit `go/` from any device on your tailnet. Try `go/google`
(or whatever you named your first link) to test a redirect.

If something is not working, see [Troubleshooting](#troubleshooting).

### Updating

Pull the latest image and restart:

```bash
docker compose pull
docker compose up -d
```

### Changing Your Links

Edit `config/directory.yml`, then restart GoHome for changes to
take effect:

```bash
docker compose restart gohome
```

## Standalone Docker

If you do not use Tailscale, you can run GoHome as a plain Docker
container accessible on port 8080.

**Prerequisites:** [Docker](https://docs.docker.com/get-docker/)
with Docker Compose.

### Step 1: Create a Project Directory

```bash
mkdir -p gohome/config
cd gohome
```

### Step 2: Download the Docker Compose File

```bash
curl -fLO https://raw.githubusercontent.com/DaftDoki/GoHome/main/docker-compose.standalone.yml
```

<details>
<summary>View file contents</summary>

```yaml
---
services:
  gohome:
    image: ghcr.io/daftdoki/gohome:latest
    ports:
      - "8080:8080"
    volumes:
      - ./config:/config:ro
```

</details>

### Step 3: Create Your Link Directory

```bash
curl -fLo config/directory.yml \
  https://raw.githubusercontent.com/DaftDoki/GoHome/main/sample_config/directory.yml
```

Open `config/directory.yml` and replace the sample entries with your
own links. See [Step 4 of the Setup Guide](#step-4-create-your-link-directory)
for the full format and a minimal example.

### Step 4: Start GoHome

```bash
docker compose -f docker-compose.standalone.yml up -d
```

Open `http://localhost:8080` in your browser. To access GoHome from
other devices on your network, use `http://<host-ip>:8080`.

To update, restart, or change links, follow the same commands in the
[Setup Guide](#updating) — just add `-f docker-compose.standalone.yml`
to your `docker compose` commands.

## User Guide

### Browsing the Directory

Visit `go/` (or `http://localhost:8080` for standalone) to see all
links and categories, displayed in the order defined in
`directory.yml`. Category sections are collapsible — click a category
heading to collapse or expand it. All categories are expanded by
default. The small arrow (↗) next to a category name links to that
category's dedicated page.

### Quick Redirects

Type `go/` followed by a link's [slug](#slug-normalization) to
redirect instantly:

| Display name | URL |
| --- | --- |
| Google | `go/google` |
| My Cool Site | `go/my-cool-site` |
| Bob's Links! | `go/bobs-links` |

Links inside categories work the same way — `go/netflix` redirects
even though Netflix is listed under Streaming. If a link has
[aliases](#aliases), those work too — `go/search` redirects to the
same place as `go/google`.

### Category Pages

Use a category's slug to see only that section — `go/streaming` shows
just the Streaming links, `go/dev-tools` shows Dev Tools.

### Themes and Modes

Use the footer controls to switch themes (dropdown) and set
light/dark/auto mode. Preferences are stored in cookies. Auto follows
the browser's `prefers-color-scheme` setting and is the default.

## Configuration Reference

### Configuration Directory

GoHome reads configuration from a single directory mounted at
`/config` inside the container. In the Docker Compose files above,
this is mapped to `./config` on your host:

```text
config/
├── config.yml           # Optional application settings
├── directory.yml        # Required link directory
├── tailscale.env        # Tailscale auth key (Tailscale setup only)
└── themes/              # Optional custom theme CSS files
    └── nord.css
```

### directory.yml

Every entry must have a `name`. Add a `url` to make it a link, or
add `entries` to make it a category:

```yaml
---
directory:
  - name: Google
    url: https://google.com
    description: The world's most popular search engine
    aliases:
      - search

  - name: Streaming
    description: Video streaming services
    entries:
      - name: Netflix
        url: https://netflix.com
```

**Rules:**

- Every entry must have a `name`
- Entries must have either `url` (link) or `entries` (category)
- If both `url` and `entries` are present, it is treated as a category
- Category `entries` must not be empty
- Names and aliases must be globally unique after slug normalization
- Only one level of nesting is supported
- The `description` and `aliases` fields are optional

If the configuration is invalid, GoHome will not start. Run
`docker compose logs gohome` to see the error message.

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

#### Aliases

Any entry can have an `aliases` list of alternative names that also
redirect to the same URL. Each alias is normalized and registered as
its own slug, so `go/search` and `go/google` can point to the same
destination. Aliases are displayed beneath the entry in the web UI
for discoverability. Alias slugs must be globally unique — they
cannot collide with any other name or alias.

```yaml
- name: Google
  url: https://google.com
  aliases:
    - search
    - gsearch
```

#### Restarting after changes

GoHome reads `directory.yml` once at startup. After editing your
links, restart for changes to take effect:

```bash
docker compose restart gohome
```

### config.yml

All settings are optional with sensible defaults:

```yaml
site_title: "GoHome"       # Browser tab and header title
host: "0.0.0.0"            # Bind address
port: 8080                  # Bind port
log_level: "info"           # debug, info, warning, error
default_theme: "default"    # Theme for first-time visitors
```

You can also download the sample file:

```bash
curl -fLo config/config.yml \
  https://raw.githubusercontent.com/DaftDoki/GoHome/main/sample_config/config.yml
```

Every setting can also be overridden with an environment variable —
see [Environment Variables](#environment-variables).

### Custom Themes

Place `.css` files in the `themes/` subdirectory of your config
directory. Each file becomes a selectable theme named after the file
(e.g., `themes/nord.css` creates theme "nord"). Themes must be fully
self-contained — they do not inherit from the default theme.

Use CSS custom properties for colors. Support light and dark modes via
`.light` and `.dark` body classes plus a `prefers-color-scheme` media
query fallback. See `src/gohome/static/default.css` for the full
reference.

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

## Troubleshooting

### "go" does not resolve

Confirm MagicDNS is enabled in the Tailscale admin console under
**DNS**. Verify the browsing device is on the same tailnet
(`tailscale status`), and check that the machine shows as **go**
in the admin console. Some browsers treat short hostnames as search
queries — try `http://go/` with the scheme explicitly included.

### Container fails to join the tailnet

Ensure `TS_AUTHKEY` in `config/tailscale.env` has not expired. Check
logs with `docker compose logs tailscale`. If using ACL tags, verify
the auth key is authorized for those tags.

### Hostname "go" is already taken

A previous container may have registered the hostname. Remove the
stale machine in the
[admin console](https://login.tailscale.com/admin/machines), delete
the local state volume (`docker volume rm gohome_ts-state`), and
restart the stack. See
[docs/troubleshooting.md](docs/troubleshooting.md) for detailed
steps.

### GoHome is not reachable

Verify both containers are running (`docker compose ps`), check
GoHome logs (`docker compose logs gohome`), and ensure
`network_mode: service:tailscale` is set in the Compose file.

### GoHome won't start

If GoHome exits immediately, your configuration likely has an error.
Check the logs:

```bash
docker compose logs gohome
```

Common causes: missing `directory.yml`, duplicate link names, or
empty category entries. Fix the issue and restart:

```bash
docker compose restart gohome
```

## Developer Guide

### AI Use

It's apparent that Claude Code was used to create this project. I
work in tech, and these tools are changing the game for all of us.
This project was a weekend-ish of work where the primary intent
wasn't creating this thing, it was trying out some approaches to one
shotting a greenfield app and seeing how much ambiguity I could get
away with and not end up with crappy slop. But in the end it's
useful, so I've polished it up and published it. If you work in
tech, you should be using these new tools to at least inform your
opinions about them, whether they are good or bad.

Check out the
[initial requirements doc](docs/Initial%20Requirements.md) if you're
interested in what the AI started with and maybe use that to play
with adapting and generating it with whatever stack and language you
prefer. Stay curious.

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) for dependency management
- [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2)
  for Markdown linting
- [yamllint](https://github.com/adrienverdelhan/yamllint) for YAML
  linting

### Setup

```bash
git clone https://github.com/DaftDoki/GoHome.git
cd GoHome
uv sync --all-extras
git config core.hooksPath .githooks
```

The `git config` command activates the shared pre-commit hook, which
runs all linters, formatters, and tests before each commit. This is
the same suite that CI runs.

### Running Locally

```bash
uv run python -m gohome sample_config/
# Server starts at http://localhost:8080
```

Or use the build-from-source Docker Compose files:

```bash
# With Tailscale:
docker compose -f docker-compose.build.yml up -d

# Without Tailscale (uses sample_config):
docker compose -f docker-compose.build.standalone.yml up -d
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
yamllint sample_config/ docker-compose*.yml
```

### Dependency Policy

To mitigate software supply chain compromises, dependency resolution
is configured with a two-week cooldown. The `[tool.uv]` section in
`pyproject.toml` sets `exclude-newer = "2 weeks"`, which tells uv to
ignore any package version published within the last two weeks. This
applies automatically to all `uv lock`, `uv sync`, and `uv add`
commands.

When updating dependencies, simply run:

```bash
uv lock --upgrade
```

Only versions at least two weeks old will be considered.

### Container Builds

Container images are published to GHCR
(`ghcr.io/daftdoki/gohome`) by the publish workflow.

**Release builds** happen automatically when a version tag is pushed:

```bash
git tag v0.2.0
git push origin v0.2.0
# Produces tags: 0.2.0, 0.2, latest, sha-<short>
```

**Dev builds** from the `dev` branch are opt-in. Add `[build]`
anywhere in the commit message to trigger a container build:

```bash
git commit -m "Add feature [build]"
git push origin dev
# Produces tags: dev, sha-<short>
```

Pushes to `dev` without `[build]` run CI only — no image is built.

You can also trigger a dev build manually without a new commit:

```bash
gh workflow run publish.yml --ref dev
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
