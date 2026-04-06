"""Immutable data models for the GoHome link directory.

All models are frozen dataclasses, making them hashable and safe to share
across request contexts.  The central :class:`Directory` holds a
pre-built slug map for O(1) path resolution.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class LinkEntry:
    """A single link that redirects to an external URL.

    Attributes:
        name: The human-readable display name.
        slug: The URL-safe normalized slug.
        url: The target URL for redirection.
        description: An optional short description shown in the UI.
        aliases: Alternative names that also resolve to this link.
    """

    name: str
    slug: str
    url: str
    description: str = ""
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class CategoryEntry:
    """A named group of links displayed as a sub-section.

    Attributes:
        name: The human-readable display name.
        slug: The URL-safe normalized slug.
        description: An optional short description shown beneath the heading.
        aliases: Alternative names that also resolve to this category.
        entries: The links belonging to this category.
    """

    name: str
    slug: str
    description: str = ""
    aliases: tuple[str, ...] = ()
    entries: tuple[LinkEntry, ...] = ()


DirectoryItem = LinkEntry | CategoryEntry
"""A union type for any item that can appear in the directory."""


@dataclass(frozen=True)
class Directory:
    """The complete link directory with O(1) slug lookup.

    ``slug_map`` is a read-only mapping from normalized slugs to directory
    items.  Links nested inside categories are also registered at the top
    level so that ``go/<slug>`` resolves them directly.

    Attributes:
        items: All top-level directory items in display order.
        slug_map: Flat lookup table mapping slugs to items.
    """

    items: tuple[DirectoryItem, ...]
    slug_map: MappingProxyType[str, DirectoryItem]


@dataclass(frozen=True)
class AppConfig:
    """Application-level configuration loaded from ``config.yml``.

    All fields have sensible defaults so the config file is optional.

    Attributes:
        site_title: The title shown in the header and browser tab.
        host: The address the server listens on.
        port: The port the server listens on.
        log_level: Python logging level name.
        default_theme: The theme used when no user preference is set.
        config_dir: Absolute path to the configuration directory.
    """

    site_title: str = "GoHome"
    host: str = "0.0.0.0"
    port: int = 8080
    log_level: str = "info"
    default_theme: str = "default"
    config_dir: str = "."

    @property
    def is_localhost(self) -> bool:
        """Whether the server listens only on a loopback address.

        Returns True when ``host`` is ``127.0.0.1``, ``::1``, or
        ``localhost``, meaning connections can only arrive from the
        local machine (e.g. via a Tailscale serve proxy).
        """
        return self.host in ("127.0.0.1", "::1", "localhost")
