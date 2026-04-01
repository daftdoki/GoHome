"""Configuration loading and validation for GoHome.

Reads ``config.yml`` (optional) and ``directory.yml`` (required) from a
configuration directory, validates them strictly, and returns
:class:`~gohome.models.AppConfig` and :class:`~gohome.models.Directory`
instances.  Fatal validation errors cause :func:`sys.exit` so the service
never starts with a broken configuration.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from types import MappingProxyType
from typing import Any

import yaml

from gohome.models import AppConfig, CategoryEntry, Directory, DirectoryItem, LinkEntry
from gohome.normalize import normalize_name

logger = logging.getLogger(__name__)

_ENV_VAR_MAP: dict[str, str] = {
    "site_title": "GOHOME_SITE_TITLE",
    "host": "GOHOME_HOST",
    "port": "GOHOME_PORT",
    "log_level": "GOHOME_LOG_LEVEL",
    "default_theme": "GOHOME_DEFAULT_THEME",
}
"""Mapping from ``config.yml`` keys to their environment variable overrides."""

_KNOWN_CONFIG_KEYS: frozenset[str] = frozenset(_ENV_VAR_MAP)


def load_app_config(config_dir: str) -> AppConfig:
    """Load application settings from ``config.yml`` with env var overrides.

    Resolution priority (highest wins):
        ``GOHOME_*`` environment variables > ``config.yml`` > built-in defaults

    If the config file is missing the service starts with defaults (which
    may still be overridden by environment variables).  Unknown keys trigger
    a warning but do not prevent startup.

    Supported environment variables: ``GOHOME_SITE_TITLE``, ``GOHOME_HOST``,
    ``GOHOME_PORT``, ``GOHOME_LOG_LEVEL``, ``GOHOME_DEFAULT_THEME``.

    Args:
        config_dir: Path to the directory containing ``config.yml``.

    Returns:
        A populated :class:`AppConfig` instance.
    """
    config_path = Path(config_dir) / "config.yml"
    raw: dict[str, Any] = {}

    if not config_path.exists():
        logger.info("No config.yml found — using defaults")
    else:
        try:
            parsed: Any = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            logger.error("Malformed config.yml: %s", exc)
            sys.exit(1)

        if isinstance(parsed, dict):
            raw = parsed
            for key in raw:
                if key not in _KNOWN_CONFIG_KEYS:
                    logger.warning("Unknown config key: %r", key)
        else:
            logger.info("config.yml is empty or not a mapping — using defaults")

    # Build kwargs from config.yml values, then overlay env var overrides.
    # Unspecified keys are omitted so AppConfig dataclass defaults apply.
    kwargs: dict[str, Any] = {}
    for config_key, env_var in _ENV_VAR_MAP.items():
        env_value = os.environ.get(env_var)
        if env_value is not None:
            kwargs[config_key] = env_value
        elif config_key in raw:
            kwargs[config_key] = raw[config_key]

    # Port must be an integer
    if "port" in kwargs:
        try:
            kwargs["port"] = int(kwargs["port"])
        except (ValueError, TypeError):  # fmt: skip
            logger.error("Invalid port value: %r", kwargs["port"])
            sys.exit(1)

    return AppConfig(config_dir=str(Path(config_dir).resolve()), **kwargs)


def load_directory(config_dir: str) -> Directory:
    """Load and validate the link directory from ``directory.yml``.

    The function validates every entry and builds a flat slug map for O(1)
    path resolution.  Any validation failure calls :func:`sys.exit`.

    Args:
        config_dir: Path to the directory containing ``directory.yml``.

    Returns:
        A fully validated :class:`Directory` instance.
    """
    dir_path = Path(config_dir) / "directory.yml"
    if not dir_path.exists():
        logger.error("Missing directory.yml in %s", config_dir)
        sys.exit(1)

    try:
        raw: Any = yaml.safe_load(dir_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        logger.error("Malformed directory.yml: %s", exc)
        sys.exit(1)

    if not isinstance(raw, dict) or "directory" not in raw:
        logger.error("directory.yml must contain a 'directory' key")
        sys.exit(1)

    entries_raw = raw["directory"]
    if not isinstance(entries_raw, list) or len(entries_raw) == 0:
        logger.error("directory.yml 'directory' list must not be empty")
        sys.exit(1)

    items: list[DirectoryItem] = []
    slug_map: dict[str, DirectoryItem] = {}

    for entry in entries_raw:
        _process_entry(entry, items, slug_map, nested=False)

    return Directory(
        items=tuple(items),
        slug_map=MappingProxyType(slug_map),
    )


def _register_slug(
    slug: str,
    name: str,
    item: DirectoryItem,
    slug_map: dict[str, DirectoryItem],
) -> None:
    """Add a slug to the map, exiting on collision.

    Args:
        slug: The normalized slug to register.
        name: The original display name (for error messages).
        item: The directory item to register.
        slug_map: The slug-to-item mapping being built.
    """
    if not slug:
        logger.error("Name %r normalizes to an empty slug", name)
        sys.exit(1)

    if slug in slug_map:
        existing = slug_map[slug]
        logger.error(
            "Name collision: %r and %r both normalize to %r",
            existing.name,
            name,
            slug,
        )
        sys.exit(1)

    slug_map[slug] = item


def _process_entry(
    entry: Any,
    items: list[DirectoryItem],
    slug_map: dict[str, DirectoryItem],
    *,
    nested: bool,
) -> None:
    """Validate and process a single directory entry.

    Args:
        entry: The raw parsed YAML entry.
        items: The list of top-level items being built.
        slug_map: The slug-to-item mapping being built.
        nested: Whether this entry is inside a category.
    """
    if not isinstance(entry, dict):
        logger.error("Directory entry must be a mapping, got: %r", type(entry).__name__)
        sys.exit(1)

    name = entry.get("name")
    if not name:
        logger.error("Directory entry is missing required 'name' key")
        sys.exit(1)

    has_url = "url" in entry
    has_entries = "entries" in entry

    if not has_url and not has_entries:
        logger.error("Entry %r must have either 'url' or 'entries'", name)
        sys.exit(1)

    slug = normalize_name(str(name))

    # Category (entries key present — url is ignored if both exist)
    if has_entries:
        if nested:
            child_count = (
                len(entry["entries"]) if isinstance(entry["entries"], list) else 0
            )
            logger.warning(
                "Nested category %r skipped (%d entries discarded)", name, child_count
            )
            return

        raw_children = entry["entries"]
        if not isinstance(raw_children, list) or len(raw_children) == 0:
            logger.error("Category %r has an empty entries list", name)
            sys.exit(1)

        child_items: list[DirectoryItem] = []
        cat = CategoryEntry(
            name=str(name),
            slug=slug,
            description=str(entry.get("description", "")),
        )
        _register_slug(slug, str(name), cat, slug_map)

        for child_entry in raw_children:
            _process_entry(child_entry, child_items, slug_map, nested=True)

        # Rebuild the category with its children now populated
        cat = CategoryEntry(
            name=cat.name,
            slug=cat.slug,
            description=cat.description,
            entries=tuple(item for item in child_items if isinstance(item, LinkEntry)),
        )
        # Update slug_map to point to the fully-built category
        slug_map[slug] = cat
        items.append(cat)
    else:
        # Link entry
        link = LinkEntry(
            name=str(name),
            slug=slug,
            url=str(entry["url"]),
            description=str(entry.get("description", "")),
        )
        _register_slug(slug, str(name), link, slug_map)
        items.append(link)
