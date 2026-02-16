# GoHome Implementation Plan

## Context

GoHome is a self-hosted link directory and redirector service. The project
is greenfield — only `docs/Initial Requirements.md` exists. This plan
breaks implementation into 11 atomic phases, each producing a working
commit with tests. The phases are strictly linear since each builds on the
previous one.

---

## Phase 0: Update Requirements Document

**Goal**: Remove `static_assets_path` feature from the spec, move it to
Future TODOs.

**Changes to `docs/Initial Requirements.md`**:

- Remove `static_assets_path` from the `config.yml` example block
- Remove the "Static Assets" section (lines 344-352), replace with a
  simpler note that the app bundles a default favicon and meta tags
- Remove the "Absolute `static_assets_path`" validation bullet
- Add `static_assets_path` / static asset override to Future TODOs
- Remove mention of `static_assets_path` from the administrator stories

**Commit**: `Remove static_assets_path feature from requirements, defer to future TODO`

---

## Phase 1: Project Scaffolding

**Goal**: Establish the project skeleton, tooling, and developer docs.

**Files created**:

- `pyproject.toml` — hatchling build backend, Flask + PyYAML deps, dev deps
  (pytest, mypy, ruff, types-Flask, types-PyYAML), ruff/mypy config
- `.python-version` — pins `3.13`
- `.gitignore` — Python/uv/IDE ignores
- `src/gohome/__init__.py` — empty package init
- `src/gohome/py.typed` — PEP 561 typed marker
- `tests/__init__.py` — empty
- `tests/conftest.py` — minimal
- `tests/test_smoke.py` — import smoke test
- `CLAUDE.md` — developer setup, build, test, lint instructions
- `uv.lock` — generated

**Tests**: 1 smoke test (import `gohome`).

**Commit**: `Add project scaffolding with pyproject.toml, src layout, and tooling config`

---

## Phase 2: Data Models and Name Normalization

**Goal**: Define data types and the slug normalization function. Pure
Python, no Flask dependency.

**Files created**:

- `src/gohome/models.py` — frozen dataclasses: `LinkEntry`, `CategoryEntry`,
  `Directory` (with slug lookup maps), `AppConfig`
- `src/gohome/normalize.py` — `normalize_name()`: lowercase, spaces to
  hyphens, strip non-ASCII, collapse hyphens, strip leading/trailing hyphens
- `tests/test_normalize.py` — ~12 tests
- `tests/test_models.py` — basic construction tests

**Tests**: ~15 total covering normalization edge cases and model construction.

**Commit**: `Add data models and name normalization with tests`

---

## Phase 3: Config Loading and Validation

**Goal**: Load and strictly validate `config.yml` and `directory.yml`.
Raises `SystemExit` on validation errors per the spec.

**Files created**:

- `src/gohome/config.py` — `load_config()`, `load_directory()`, validation
  helpers
- `tests/test_config.py` — ~20-25 tests using `tmp_path`
- `tests/conftest.py` — updated with `sample_config_dir` fixture

**Validation rules tested**:

- Missing `directory.yml` → exit
- Empty directory list → exit
- Malformed YAML → exit
- Missing `name` key → exit
- Neither `url` nor `entries` → exit
- Empty `entries` list → exit
- Name collisions → exit
- Empty normalized slug → exit
- Unknown config keys → warning (continue)
- Nested categories → warning (discarded with count)
- Entry with both `url` and `entries` → treated as category

**Commit**: `Add config loading and validation with strict error checking`

---

## Phase 4: Flask App Factory and Routing

**Goal**: Create the app factory with core routing. Root page returns
placeholder HTML; link paths redirect; category paths return placeholder;
unknown paths redirect to root.

**Files created**:

- `src/gohome/__init__.py` — `create_app(config_dir)` app factory
- `src/gohome/routes.py` — `index()`, `handle_path(path)` handlers
- `src/gohome/__main__.py` — `python -m gohome` entry point
- `tests/test_routes.py` — ~12-15 route tests
- `tests/conftest.py` — `client` and `empty_client` fixtures

**Key design**:

- `Directory` and `AppConfig` stored on `app.config`
- Catch-all route `/<path:path>` normalizes incoming path, looks up in
  `directory.all_slugs`
- `after_request` hook adds `Cache-Control: no-cache` to HTML responses

**Tests**: Root returns 200, link redirects 302 to correct URL,
case-insensitive lookup, category returns 200, unknown path redirects to
root, multi-segment path redirects to root.

**Commit**: `Add Flask app factory with routing, redirects, and path resolution`

---

## Phase 5: Templates and Default Theme

**Goal**: Replace placeholder HTML with a single Jinja2 template (per the
spec: "A single base HTML template will be used"). Bundle a clean default
theme.

**Files created**:

- `src/gohome/templates/base.html` — single template: layout with meta
  tags, title, breadcrumbs, directory listing, footer. Route handlers
  pass different context (items, title, breadcrumbs) for root vs category
- `src/gohome/static/themes/default.css` — CSS custom properties with
  `.light`/`.dark` classes, `prefers-color-scheme` media query
- `src/gohome/static/favicon.ico` — simple bundled favicon
- `src/gohome/themes.py` — `discover_themes()`
- `tests/test_templates.py` — ~15-18 tests

**Tests**: Link names/URLs rendered, category headings, descriptions,
title tag format (`site_title` on root, `SiteTitle — Category` on
sub-pages), breadcrumbs (`Home` on root, `Home > Category` with link on
sub-pages), meta tags present.

**Commit**: `Add Jinja2 template, base layout, directory rendering, and default theme`

---

## Phase 6: Theme Selection and Cookie Handling

**Goal**: Full theming: custom theme discovery, footer dropdown, light/dark
toggle, cookie read (server) and write (client JS).

**Files created/modified**:

- `src/gohome/themes.py` — updated: discovers custom themes from config
  `themes/` dir, resolves theme/mode from cookies with fallback
- `src/gohome/static/js/theme.js` — dropdown change + mode toggle handlers,
  sets cookies (path `/`, 1-year expiry) only on user action
- `src/gohome/templates/base.html` — updated: footer `<select>`, mode
  toggle, data attributes for JS
- `src/gohome/routes.py` — reads cookies, passes resolved theme/mode to
  templates
- `tests/test_themes.py` — ~12-15 tests

**Key design**: Server never sets `Set-Cookie`. Body has no `.light`/`.dark`
class when no mode cookie — `prefers-color-scheme` handles it. Removed
theme cookie falls back to admin's `default_theme`.

**Commit**: `Add theme discovery, selection cookies, light/dark mode toggle`

---

## Phase 7: Docker Setup

**Goal**: Dockerfile, `.dockerignore`, and env var override for host/port.

**Files created**:

- `Dockerfile` — `python:3.13-slim`, copies uv from official image, sets
  `GOHOME_HOST`/`GOHOME_PORT` env vars
- `.dockerignore`
- `src/gohome/__main__.py` — updated: env var priority over config

**Tests**: ~4-5 tests for env var override logic (using `monkeypatch`).

**Commit**: `Add Dockerfile and environment variable overrides for host/port`

---

## Phase 8: Sample Config and docker-compose

**Goal**: Working example configs so users can try the app immediately.

**Files created**:

- `sample_config/directory.yml` — example links and categories
- `sample_config/config.yml` — commented example
- `docker-compose.example.yml` — builds container, maps `sample_config/`

**Tests**: ~2-3 tests validating sample configs load correctly.

**Commit**: `Add sample configuration and docker-compose.example.yml`

---

## Phase 9: README Documentation

**Goal**: User, admin, and developer documentation.

**Files created**:

- `README.md` — overview, quick start, config reference, theming guide,
  Docker deployment, dev setup, contributing
- `docs/troubleshooting.md` — initial stub
- `CLAUDE.md` — updated

**Tests**: None (docs only). Lint with `markdownlint-cli2`.

**Commit**: `Add README.md with user, admin, and developer documentation`

---

## Phase 10: Polish and Edge Cases

**Goal**: Handle remaining edge cases, fix any linter/type issues.

**Tests**: ~5-8 additional tests: directory with only categories, only
links, single-entry category, numeric names, URLs with query strings
preserved in redirects, content-type verification.

**Commit**: `Add edge case tests and final polish`

---

## Phase 11: Integration Tests

**Goal**: Verify the three integration scenarios from the requirements,
document in CLAUDE.md.

**Files created**:

- `tests/test_integration.py` — ~5-6 tests using sample config
- `CLAUDE.md` — updated with integration test instructions

**Tests**: Root returns directory page, link path returns 302, category
path returns listing, theme CSS returns 200, unknown path redirects.

**Commit**: `Add integration tests and update CLAUDE.md with test instructions`

---

## Estimated Test Count

| Phase | Tests |
|-------|-------|
| 1. Scaffolding | 1 |
| 2. Models/Normalization | ~15 |
| 3. Config/Validation | ~20 |
| 4. Routing | ~13 |
| 5. Templates | ~16 |
| 6. Themes/Cookies | ~13 |
| 7. Docker/Env Vars | ~5 |
| 8. Sample Config | ~3 |
| 9. Docs | 0 |
| 10. Edge Cases | ~7 |
| 11. Integration | ~6 |
| **Total** | **~99** |

---

## Key Architectural Decisions

1. **Separate modules**: models, normalize, config, routes, themes —
   each independently testable
2. **Slug lookup map**: `Directory` pre-builds `dict[str, DirectoryItem]`
   for O(1) path resolution
3. **No server-side cookie setting**: cookies managed entirely by
   client-side JS on user interaction
4. **Empty mode = browser decides**: no `.light`/`.dark` class when no
   cookie, `prefers-color-scheme` media query handles default
5. **Validation exits process**: `sys.exit(1)` after logging, tested via
   `SystemExit` assertion
6. **Custom theme CSS served via route**: custom themes from config
   `themes/` directory served through a dedicated route, bundled static
   assets served by Flask's default static handler

## Verification

After each phase, run:

```bash
uv run ruff format src/ tests/
uv run ruff check --fix src/ tests/
uv run mypy src/
uv run pytest
markdownlint-cli2 "**/*.md"
yamllint sample_config/  # (phases 9+)
```

All must pass before committing.
