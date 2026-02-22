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

## Name normalization: tabs vs spaces

**Problem:** Tab characters in names are not treated the same as spaces.

**Explanation:** The normalization spec says "replace spaces with
hyphens." Tabs are not spaces — they are stripped by the
non-alphanumeric filter rather than converted to hyphens. This is by
design. Input `"a\tb"` normalizes to `"ab"`, not `"a-b"`.
