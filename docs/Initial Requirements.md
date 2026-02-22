
# GoHome

GoHome is a small self-hosted link directory web site and redirector
service that is simple to configure and host. The target end user is a
nerdy sort that enjoys self-hosting and wants a simple way to access
links to their self-hosted or commonly used services. If the user
configures their clients properly they may be able to use this site via
the `go` short name in their web browser address bar (e.g., go/link-name)
for quick access to links.

The service is configured via two YAML configuration files: one for
software configuration (config.yml, optional) and one for the link
directory (directory.yml, required). It is intended to be hosted at a
user owned domain name like go.example.com. When the user points
their web browser at the root of the site, they are shown a directory
of links to choose from. The directory can contain optional sub
sections to organize the links under. It will also be redirector
service, meaning that each link will have a name that can also be
referenced via URL path (e.g., go.example.com/link-name) that will
instantly redirect the users browser to the configured URL of the
link. The user can also point their web browser at a sub-section name
and get a rendered listing of links in that sub-section. The interface
is responsive and work well on mobile and desktop browsers. It is
themeable with support for light and dark modes which are automatically
chosen if the users browser supports it.

## Stories

We will consider three different personas in our stories. These personas are:

1. *User* - This is the end user who is visiting the web site and using
   the link redirection service.
2. *Administrator* - This is the end user running and hosting the website
   and link redirection service. Although the User and Administrator can be
   the same person, they are separate roles.
3. *Programmer* - This is the individual creating this software. They are
   concerned with the features, technical architecture, and creation of the
   software and how it works.

### As A User

- when I go to the root of the website I want to see a directory of links
  displayed in the order they appear in the directory.yml file. The
  hierarchy should be organized like a tree with links indented underneath
  the sub-section heading. The administrator controls the display order by
  arranging entries in the YAML file.
- I want to specify an optional path in the URL and either have my browser
  redirect to the URL of the named link, or if the name is for a sub-section,
  see that sub section rendered in my browser in the same fashion as the root.
  (e.g. go.example.com/my-cool-link redirects the browser to the URL specified
  for that link name, or go.example.com/my-cool-section-name renderes the
  directory in the UI from that point in the tree.)
- I want the website to automatically select a dark or light mode theme
  based on the current setting on my device.
- I want to see a common header and footer on each rendered page.
  - The header should show me navigation crumbs that I can use to go back
    up a sub-section or return to the main page. The format uses `>` as
    the separator (e.g., "Home > Streaming"). On the root page, only
    "Home" is displayed as plain text (no link). On sub-section pages,
    "Home" links to the root page and the current section name is plain
    text (not a link).
  - The browser tab title (`<title>` tag) shows the `site_title` on the
    root page. On sub-section pages it uses the format
    `"SiteTitle — SectionName"` (e.g., `"GoHome — Streaming"`).
  - The footer should allow me to select a theme and toggle light and dark
    modes. The theme selector is rendered as a `<select>` dropdown and is
    always visible, even if only the bundled default theme is available.
    If the user's cookie references a theme that has been removed, the
    application falls back to the admin's configured `default_theme`.
    My chosen preferences should be stored in my browser using cookies
    named `gohome_theme` and `gohome_mode` with
    path `/` and a 1-year expiry. The `gohome_theme` cookie stores the
    theme name (e.g., "default", "nord") and `gohome_mode` stores "light"
    or "dark".

### As An Administrator

- I want the web interface to be easily themable so that I can customize
  the look of the interface.
  - My custom theme should be in separate files that I can make available
    to others for their use if I choose.
  - My custom theme should allow for a dark and light mode version of my
    theme.
- I want to be able to set the default theme that my users see when they
  visit the page.
- I want to be able to easily deploy this service via docker and give the
  container a single directory bind mount that contains my configuration
  files and any theme files required.
- I do not want the service to write a log to a file at this time. This
  will be a future feature.
- I do want the service to log to the terminal for debugging and
  troubleshooting as a docker container.
- I want to specify a name, url, and short description for each link in
  the directory. Categories also support an optional description that is
  displayed beneath the category heading when present.
- I want a sample configuration directory (e.g., `sample_config/`) included
  in the repository with a working `directory.yml` (and optionally a
  `config.yml`) so that I can immediately try out the application without
  writing configuration from scratch.
- I want a `docker-compose.example.yml` file in the repository that builds
  the docker container and uses the sample configuration directory. Users
  can copy this to `docker-compose.yml` and run `docker compose up` to
  quickly try out the application with the example configuration.

### As The Programmer

- I want the server side to be written in Python
  - All written python code must use type annotations
  - It will use Flask as the web framework. Flask is chosen for its
    simplicity, maturity, and built-in Jinja2 templating support.
  - The web interface will use Jinja2 templates (Flask's built-in
    templating engine). A single base HTML template will be used, with the
    link directory rendered inside of it.
- The web UI will be simple HTML and javascript. No external javascript or
  CSS libraries or frameworks should be used. All CSS is hand-written or
  provided via themes. JavaScript is limited to theme toggling, mode
  switching, and cookie management — no other client-side behavior.
- All code will:
  - Be well commented. Each function, class, module, or otherwise should
    be documented idiomatically for the language so that code documentation
    can be generated from it. It should explain to the human reader what it
    does and how to use it. It shouldn't be overly verbose, but also not so
    succint that it isn't useful.
  - be appropriately tested with a robust test suite using pytest as the test framework.
  - Focus on thoroughly testing interfaces, not just on code coverage.
  - Frontend JavaScript will not have its own test suite. JS behavior (theme
    toggling, cookie management) will be verified through server-side
    integration tests using Flask's test client. Note: Flask's test client
    does not execute JavaScript, so tests verify the server-side contract
    (correct CSS classes and attributes rendered based on cookie values,
    correct JS served) but cannot verify client-side JS execution. This is
    a known and accepted limitation.
  - Be linted and formatted idiomatically based on the language
  - Enforce strict type checking (mypy --strict) on all Python code. All
    type check errors must be resolved — no ignoring or suppressing without
    justification.
  - All linting, formatting, and type check issues MUST be fixed before
    committing. No warnings or errors may be left unresolved.
  - Not be created or modified without creating or updating tests, running
    the linter, formatter, AND type checker, and fixing all issues found
  - Markdown files must be linted using markdownlint-cli2 and all issues
    must be resolved before committing. This applies to all markdown files
    in the repository including documentation.
  - YAML files must be linted using yamllint and all issues must be
    resolved before committing. This applies to all sample configuration
    files and any other YAML files in the repository.
- Python dependency management will use `uv` exclusively. Dependencies are
  declared in `pyproject.toml` and locked in `uv.lock`. Use `uv sync` to
  install dependencies and `uv run` to execute commands in the managed
  environment. Do not use pip, pipenv, poetry, or any other package manager.
- The service will be configured by a yaml file called config.yml
- The directory of links will be defined in a yaml file called
  directory.yml (See: Example directory.yml)
- A `README.md` in the repository root must be maintained as the primary
  human-facing documentation. It must contain or link to documentation for
  users (how to use the web interface), administrators (how to configure and
  deploy the service), and developers (how to set up a build environment,
  contribute, build, and test). It must be kept up to date as the project
  evolves and should include examples where appropriate.
- Claude Code will be used to assist in development. A CLAUDE.md file
  should be maintained in the root of the repository with information
  necessary for Claude when working on this repository. CLAUDE.md must
  be kept accurate and up to date as the project evolves — update it
  in the same commit as any change that affects its content.
- When Claude troubleshoots and fixes problems, it will update a file in
  docs/troubleshooting.md that records the problem, its solution, and the
  troubleshooting steps used to diagnose and fix the problem.
- An integration test must be performed to verify the app server starts and
  returns expected responses. At minimum, test that: (1) the root URL
  returns the directory page, and (2) accessing a link name path returns a
  redirect, and (3) accessing a category name path returns the category
  listing. How to run these integration tests should be documented in the
  CLAUDE.md file.
- A git commit should be a single atomic commit that leaves the service
  functioning. This does not mean feature complete, but any features that
  already exist must be proven to work. A good commit size is a single
  feature, a single bug fix, or a single enhancement. Tests must be updated
  and passing, and a linter and formatting tool must be run with all issues
  addressed before any commits.
- When Claude Code creates commits, it must use
  `--author="Claude Code <noreply@anthropic.com>"` to attribute commits to
  Claude rather than the repository owner. This allows the owner to review
  PRs as themselves and provide feedback that Claude can address.  

### Example directory.yml

```yaml
directory:
  # A regular link entry. The value of the name is case insensitive and
  # spaces are replaced by hyphens `-` when the name is used as the URL path
  # for a quick redirect. Required.
  - name: Google
    # The URL that the entry will link to on the UI or redirect to when
    # referenced as the URL path. Required.
    url: https://google.com
    # A short text description that is used in the UI to add context. This is
    # optional.
    description: This is google. You know what it is. 
  - name: Yahoo
    url: https://yahoo.com
    description: You're surprised that this still exists
  # A category entry that is identified by the presence of the 'entries' key.
  # Any `url` key is ignored if 'entries is present'
  - name: Streaming
    description: A category for streaming services
    entries:
      # A regular link entry like all others. But a member of the category
      # instead of top-level.
      - name: Netflix 
        description: The trashiest of streaming services.
        url: https://netflix.com
      - name: HBO Max
        description: Is that what it is still called?
        url: https://hbomax.com
  - name: Kagi # A link entry without the optional description
    url: https://kagi.com
```

For a directory item entry there are only four possible key values: `name`,
`url`, `description`, and `entries`. All others are ignored. The `name` key
is always mandatory. An entry must have either a `url` or a `entries` key.
The `description` key is always optional.

The directory yaml is a list called `directory` that contains entries for
either a category when the `entries` key is present, or a link when the
`url` key is present. If both `entries` and `url` are present, `url` is
ignored and the entry is assumed to be a category. The `entries` key
contains a list of links for the category. Only one level of category is
supported and any categories defined inside of a category are ignored.
All entries inside a nested category (including regular links) are also
discarded. The service logs a warning at startup identifying any nested
categories that were skipped, including a count of discarded entries.

### config.yml

The `config.yml` file and `directory.yml` file must always live in the
same directory. When deployed via Docker, this directory is the single bind
mount. The `config.yml` file supports the following settings:

```yaml
# The site title displayed in the header and browser tab
site_title: "GoHome"

# The address and port the service listens on
host: "0.0.0.0"
port: 8080

# Log level for terminal output (debug, info, warning, error)
log_level: "info"

# The default theme for users who haven't set a preference.
# Optional — if not set, the bundled "default" theme is used.
default_theme: "default"

```

The `config.yml` file uses a flat structure with no top-level wrapping
key (unlike `directory.yml` which uses a `directory:` key). All settings
have sensible defaults and the file is optional. If `config.yml` is not
present, the service runs with default values.

Both `config.yml` and `directory.yml` are read and validated once at
startup. Changes to either file require restarting the service to take
effect.

### Theming

A theme is a single CSS file that uses CSS custom properties (variables) to
define colors, fonts, and spacing. Light and dark mode variants are handled
within the same file using CSS custom properties that are swapped via a
class on the `<body>` element (e.g., `.light` / `.dark`). The browser's
`prefers-color-scheme` media query is used to select the default mode when
no user preference is stored.

Multiple themes may be installed and available to users. The admin can
optionally set the default theme via `default_theme` in `config.yml`; if
not specified, the bundled "default" theme is used. Users can select a
different theme and toggle light/dark mode from the footer. The user's
selected theme and mode preference are stored in cookies. Cookies are
only set when the user explicitly changes a setting via the footer
controls — on first visit with no cookies, the admin's `default_theme`
and the browser's `prefers-color-scheme` are used without setting any
cookies.

Each theme CSS file must be fully self-contained — custom themes do not
inherit from or layer on top of the bundled default theme. Theme authors
are responsible for defining all necessary CSS custom properties and styles.

A clean, simple default theme is bundled with the application so the service
looks good and works out of the box with zero configuration. Custom themes
are placed in a `themes/` subdirectory within the configuration directory.
Each custom theme is a single `.css` file named after the theme (e.g.,
`themes/nord.css` creates a theme called "nord"). The application
automatically discovers all `.css` files in the `themes/` directory and
makes them available alongside the bundled default theme.

### URL Routing and Name Resolution

All link and category names must be globally unique across the entire
directory, regardless of nesting. All names — both links and categories
at any level — share a single global namespace. This means `go/Netflix`
works as a direct redirect even if Netflix is defined inside a Streaming
category. Category names can also be used as paths (e.g., `go/Streaming`)
to render that sub-section.

URL path lookup is case-insensitive. The incoming path is normalized
using the same rules as entry names, so `go/Netflix`, `go/NETFLIX`,
and `go/netflix` all resolve to the same entry.

Only flat, single-segment paths are supported. Nested paths like
`go/streaming/netflix` are not valid and are treated the same as any
unknown path. There is no hierarchical path routing.

If any two entries (whether links, categories, or a mix) normalize to the
same slug, this is treated as a configuration error. The service logs an
error at startup identifying the original names and their shared
normalized slug, and exits.

If a user visits a path that does not match any known link or category
name, the service responds with an HTTP 302 redirect to the root
directory page.

### Docker

The application targets Python 3.14 (currently 3.14.3) and uses
`python:3.14-slim` as the Docker base image. The Docker container runs
Flask's built-in development server. The host and port the application
binds to are resolved using the following priority order: environment
variables (`GOHOME_HOST` /
`GOHOME_PORT`) take precedence over `config.yml` values, which take
precedence over built-in defaults (`0.0.0.0` / `8080`). The Dockerfile
sets `GOHOME_HOST=0.0.0.0` and `GOHOME_PORT=8080` so that the container
binds correctly regardless of what `config.yml` contains. External port
mapping is handled entirely by docker-compose.

A single bind mount directory is mapped into the container containing all
user-provided files:

```text
/config/                  # Bind mount root
├── config.yml           # Optional application configuration
├── directory.yml        # Required link directory
└── themes/               # Optional custom themes
    ├── nord.css
    └── dracula.css
```

### Static Assets

The application bundles a simple default favicon and includes standard HTML
meta tags (viewport, charset, description) for a polished out-of-the-box
experience.

### Caching

HTML pages are served with `Cache-Control: no-cache` headers to ensure
directory changes are immediately reflected. Static assets (CSS, favicon,
etc.) use Flask's default caching behavior.

### Configuration Validation

The service validates its configuration at startup and refuses to start
if critical errors are found:

- **Missing `directory.yml`**: The service logs an error and exits. The
  directory file is required.
- **Empty directory**: If `directory.yml` exists and is valid YAML but
  the `directory` list is empty (`directory: []`), the service logs an
  error and exits. An empty directory serves no purpose.
- **Malformed YAML**: If `directory.yml` (or `config.yml` if present)
  contains invalid YAML, the service logs a parse error and exits.
- **Invalid entries**: If any entry is missing the required `name` key,
  or has neither a `url` nor an `entries` key, the service logs an error
  identifying the problematic entry and exits. All entries must be valid
  for the service to start.
- **Empty entries list**: If a category has an `entries` key with an
  empty list (`entries: []`), the service logs an error identifying the
  category and exits. Categories must contain at least one entry.
- **Empty normalized slug**: If a name normalizes to an empty string
  (e.g., `name: "!!!"`) after applying the normalization rules, the
  service logs an error identifying the entry and exits.
- **Name collisions**: If two or more entries normalize to the same slug,
  the service logs an error with the original names and shared slug, and
  exits.
- **Unknown config keys**: If `config.yml` contains keys that are not
  recognized, the service logs a warning for each unknown key but
  continues to start. This helps administrators catch typos without
  being overly strict.

This strict validation ensures the administrator is immediately aware of
configuration problems rather than discovering them at runtime through
unexpected behavior.

### Redirects

When a user visits a URL path that matches a link name, the service responds
with an HTTP 302 (temporary) redirect to the configured URL. This ensures
that if the admin changes a link's destination, users immediately get the
updated URL without browser caching issues.

### Name Normalization

Link and category names are normalized to URL-safe slugs using the following
rules:

- Convert to lowercase
- Replace spaces with hyphens (`-`)
- Strip all characters that are not ASCII letters, ASCII digits, or hyphens
  (non-ASCII characters like accented letters are removed)
- Collapse consecutive hyphens into a single hyphen

For example: `My Cool Link!` becomes `my-cool-link`. Name uniqueness is
enforced after normalization — if two entries normalize to the same slug,
this is a configuration error logged at startup. The log message must
include the original names and the resulting slug (e.g., `Name collision:
"My Cool Link" and "my-cool-link!" both normalize to "my-cool-link"`).

### Future TODOs

The following items are out of scope for the initial version but should be
considered for future development:

- **Production WSGI server**: Evaluate whether to replace Flask's built-in
  development server with a production WSGI server (e.g., gunicorn or
  waitress) for the Docker deployment.
- **Client-side search/filter**: Add a simple search or filter box to the
  directory page for quickly finding links.
- **`base_url` support**: Add support for hosting behind a reverse proxy at
  a subpath (e.g., `/go`).
- **Flash messages for unknown paths**: Display a notification on the
  redirected page when a user visits an unknown path, indicating the
  requested link was not found.
- **Dynamic configuration reload**: Reload `config.yml` and
  `directory.yml` without requiring a service restart, either via
  file-watching or a reload signal.
- **`static_assets_path` support**: Add a `static_assets_path` config
  option allowing admins to override bundled static files (e.g., favicon)
  with custom assets from a directory relative to the config directory.
