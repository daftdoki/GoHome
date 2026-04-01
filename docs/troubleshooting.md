# GoHome Troubleshooting

This file records problems encountered during development, their
solutions, and the diagnostic steps used to identify and fix them.

---

## mypy: Incompatible return type for redirect()

**Problem:** `flask.redirect()` returns `werkzeug.wrappers.Response`,
which is not compatible with `flask.wrappers.Response` in strict mypy.

**Solution:** Annotate view functions returning redirects with
`werkzeug.wrappers.Response | str` instead of
`flask.wrappers.Response | str`.

**Diagnostic steps:**

1. Ran `uv run mypy src/` — saw return-value errors on redirect calls
2. Checked `flask.redirect` return type — it returns
   `werkzeug.wrappers.Response`
3. Updated import to `import werkzeug` and annotated with
   `werkzeug.wrappers.Response | str`

## markdownlint-cli2: Errors in .venv files

**Problem:** `markdownlint-cli2 "**/*.md"` picks up Markdown files
inside `.venv/` (e.g., from installed packages).

**Solution:** Create `.markdownlint-cli2.jsonc` with globs that exclude
`.venv/`:

```json
{
  "globs": [
    "**/*.md",
    "!.venv/**",
    "!node_modules/**"
  ]
}
```

Then run `markdownlint-cli2` without arguments (it reads the config
file automatically).

## Tailscale: Hostname "go" is already taken

**Problem:** After moving to a new host or recreating the Docker stack
without preserving the `ts-state` volume, Tailscale treats the new
container as a different node and assigns a suffixed hostname like
`go-1`.

**Solution:**

1. Stop the current stack:
   `docker compose -f docker-compose.tailscale.yml down`
2. Open the
   [Tailscale admin console](https://login.tailscale.com/admin/machines)
3. Find the stale `go` machine (usually shown as offline) and remove it
   via **...** > **Remove**
4. Delete the local Tailscale state so the container re-registers
   cleanly:
   `docker volume rm gohome_ts-state`
   (the volume name may differ — check with `docker volume ls`)
5. Restart the stack:
   `docker compose -f docker-compose.tailscale.yml up -d`
6. Confirm the machine appears as **go** in the admin console

**Prevention:** Use a reusable auth key with a tag so that
re-registration is seamless when moving between hosts.

## Name normalization: tabs vs spaces

**Problem:** Tab characters in names are not treated the same as spaces.

**Explanation:** The normalization spec says "replace spaces with
hyphens." Tabs are not spaces — they are stripped by the
non-alphanumeric filter rather than converted to hyphens. This is by
design. Input `"a\tb"` normalizes to `"ab"`, not `"a-b"`.
