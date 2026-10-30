"""Tests for the name normalization module."""

from gohome.normalize import normalize_name


class TestNormalizeName:
    """Verify slug generation from display names."""

    def test_lowercase(self) -> None:
        """Upper-case letters are converted to lower-case."""
        assert normalize_name("Google") == "google"

    def test_spaces_to_hyphens(self) -> None:
        """Spaces become hyphens."""
        assert normalize_name("My Cool Link") == "my-cool-link"

    def test_strip_special_characters(self) -> None:
        """Non-alphanumeric, non-hyphen characters are removed."""
        assert normalize_name("My Cool Link!") == "my-cool-link"

    def test_collapse_multiple_hyphens(self) -> None:
        """Consecutive hyphens are collapsed into one."""
        assert normalize_name("a - - b") == "a-b"

    def test_strip_leading_trailing_hyphens(self) -> None:
        """Leading and trailing hyphens are removed."""
        assert normalize_name("-hello-") == "hello"

    def test_accents_folded(self) -> None:
        """Accented letters fold to their ASCII base letter."""
        assert normalize_name("Café") == "cafe"
        assert normalize_name("Ñandú") == "nandu"

    def test_unicode_without_ascii_form_stripped(self) -> None:
        """Characters with no ASCII decomposition are removed."""
        assert normalize_name("日本語") == ""
        assert normalize_name("日本 Café") == "cafe"

    def test_all_special_returns_empty(self) -> None:
        """A name with no ASCII alphanumeric characters normalizes to empty."""
        assert normalize_name("!!!") == ""

    def test_empty_string(self) -> None:
        """An empty input returns an empty slug."""
        assert normalize_name("") == ""

    def test_numeric_name(self) -> None:
        """Purely numeric names are preserved."""
        assert normalize_name("404") == "404"

    def test_mixed_case_and_symbols(self) -> None:
        """Mixed case with symbols normalizes predictably."""
        assert normalize_name("HBO Max") == "hbo-max"

    def test_tabs_and_multiple_spaces(self) -> None:
        """Tabs are stripped (not spaces); multiple spaces collapse."""
        assert normalize_name("a  b") == "a-b"
        assert normalize_name("a\tb") == "ab"

    def test_hyphenated_input(self) -> None:
        """Existing hyphens are preserved."""
        assert normalize_name("already-slugged") == "already-slugged"
