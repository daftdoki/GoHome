# CLAUDE.md — GoHome Developer Guide

## Project Overview

GoHome is a self-hosted link directory and redirector service built with
Flask. See `docs/Initial Requirements.md` for full requirements.

## Setup

```bash
uv sync --all-extras
```

## Running

```bash
uv run python -m gohome [config_dir]
# Example with sample config:
uv run python -m gohome sample_config/
```

## Testing

```bash
uv run pytest
```

### Integration Tests

Integration tests in `tests/test_integration.py` use the sample config
to verify the three core scenarios:

1. Root URL returns the directory page with all entries
2. Link name path returns a 302 redirect to the configured URL
3. Category name path returns that category's link listing

Run only integration tests:

```bash
uv run pytest tests/test_integration.py -v
```

## Linting and Formatting

All of these must pass before committing:

```bash
uv run ruff format src/ tests/
uv run ruff check --fix src/ tests/
uv run mypy src/
uv run pytest
markdownlint-cli2 "**/*.md"
yamllint sample_config/ docker-compose.example.yml
```

## Project Structure

- `src/gohome/` — Main application package (src layout)
  - `__init__.py` — App factory (`create_app`)
  - `__main__.py` — CLI entry point
  - `config.py` — Config loading and validation
  - `models.py` — Frozen dataclasses (`LinkEntry`, `CategoryEntry`, etc.)
  - `normalize.py` — Name-to-slug normalization
  - `routes.py` — Flask route handlers
  - `themes.py` — Theme discovery
  - `templates/base.html` — Single Jinja2 template
  - `static/` — Bundled CSS (`default.css`, `retro-green.css`,
    `retro-amber.css`, `retro-ansi.css`), JS, favicon
- `tests/` — Test suite (pytest)
- `docs/` — Documentation and requirements
- `sample_config/` — Example configuration files

## Architecture Notes

- **Slug lookup**: `Directory` pre-builds a flat `dict[str, DirectoryItem]`
  for O(1) path resolution
- **Validation**: Config errors call `sys.exit(1)` — test with
  `pytest.raises(SystemExit)`
- **Themes**: Bundled themes (`BUNDLED_THEMES` in `themes.py`) are served
  via Flask static as `<name>.css`; custom themes are served via
  `/themes/<name>.css` reading from the config dir. The template uses
  `bundled_themes` (a `frozenset`) to decide which URL to generate.
  Custom themes cannot shadow bundled theme names.
- **Adding a bundled theme**: copy the CSS to `src/gohome/static/` and
  add the name to `BUNDLED_THEMES` in `themes.py`
- **Cookies**: Server reads but never sets cookies; JS handles writes

## Coding Conventions

### Python

- **Python version**: 3.14 (currently 3.14.3)
- **Type annotations**: Required on all functions, methods, and module-level
  variables. Enforce with `mypy --strict` — no errors or warnings permitted.
- **Docstrings**: Every module, class, and function must have a docstring.
  Use Google-style docstrings. Explain what it does and how to use it —
  neither terse nor verbose.
- **Formatting**: `ruff format` (default settings)
- **Linting**: `ruff check --fix` — all issues must be resolved
- **Immutability**: Use frozen dataclasses for data models
- **Dependency management**: `uv` exclusively. Never use pip, poetry, or
  pipenv. Declare deps in `pyproject.toml`, lock in `uv.lock`.

### Test Suite

- **Framework**: pytest
- **Focus**: Test interfaces and behavior, not implementation details.
  Aim for meaningful coverage, not just line coverage.
- **Config errors**: Use `pytest.raises(SystemExit)` when testing startup
  validation failures.
- **Frontend JS**: Not directly tested. Server-side integration tests verify
  the server-side contract (correct HTML attributes and classes rendered
  based on cookie values). Flask's test client does not execute JS — this
  is accepted.
- **Integration tests**: Must cover (1) root directory page, (2) link
  redirect, (3) category listing. Live in `tests/test_integration.py`.

### HTML / CSS / JavaScript

- No external JS or CSS libraries or frameworks.
- All CSS is hand-written or provided via themes.
- JS is limited to theme toggling, mode switching, and cookie management.
- A single Jinja2 base template (`templates/base.html`) renders all pages.
- Themes are self-contained single CSS files — custom themes do not inherit
  from the default theme.

### Markdown

- Linted with `markdownlint-cli2` — all issues must be resolved before
  committing.

### YAML

- Linted with `yamllint` — all issues must be resolved before committing.

## Commit Rules

- Every commit must be a single atomic unit that leaves all tests passing
  and the service functioning.
- Run the full lint/format/type-check/test suite before every commit.
- Use `--author="Claude Code <noreply@anthropic.com>"` for all commits
  made by Claude.
- No commit may introduce linting, formatting, or type-check warnings or
  errors.

## Keeping CLAUDE.md Current

CLAUDE.md must be kept accurate and up to date as the project evolves.
When making changes that affect architecture, conventions, project structure,
commands, or any other information recorded here, update CLAUDE.md in the
same commit. An outdated CLAUDE.md is worse than none.

## README.md

`README.md` in the repository root is the primary human-facing documentation.
It must be kept up to date and must contain (or link to) documentation for:

- **Users** — how to use the web interface
- **Administrators** — how to configure and deploy the service
- **Developers** — how to set up a build environment, run tests, and
  contribute

## Troubleshooting

When Claude diagnoses and fixes a problem, record the problem, solution,
and diagnostic steps in `docs/troubleshooting.md`.
