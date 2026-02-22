"""Name-to-slug normalization for GoHome directory entries.

Converts human-readable names into URL-safe slugs using a deterministic
set of rules so that ``go/My Cool Link`` resolves to the same entry as
``go/my-cool-link``.
"""

import re

_NON_ALNUM_HYPHEN: re.Pattern[str] = re.compile(r"[^a-z0-9-]")
_MULTI_HYPHEN: re.Pattern[str] = re.compile(r"-{2,}")


def normalize_name(name: str) -> str:
    """Convert a display name to a URL-safe slug.

    The normalization rules are applied in order:

    1. Convert to lowercase.
    2. Replace spaces with hyphens.
    3. Strip all characters that are not ASCII letters, digits, or hyphens.
    4. Collapse consecutive hyphens into a single hyphen.
    5. Strip leading and trailing hyphens.

    Args:
        name: The human-readable entry name (e.g. ``"My Cool Link!"``).

    Returns:
        The normalized slug (e.g. ``"my-cool-link"``).  May be empty if
        the name contains no ASCII alphanumeric characters.
    """
    slug = name.lower()
    slug = slug.replace(" ", "-")
    slug = _NON_ALNUM_HYPHEN.sub("", slug)
    slug = _MULTI_HYPHEN.sub("-", slug)
    slug = slug.strip("-")
    return slug
