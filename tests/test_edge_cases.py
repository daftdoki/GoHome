"""Edge case tests for unusual but valid configurations."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from gohome import create_app
from gohome.config import load_directory

if TYPE_CHECKING:
    pass


def _write_yaml(tmp_path: Path, filename: str, content: str) -> None:
    """Write a YAML string to a file in *tmp_path*."""
    (tmp_path / filename).write_text(content, encoding="utf-8")


class TestLinksOnly:
    """Verify a directory with only links (no categories)."""

    def test_links_only_renders(self, tmp_path: Path) -> None:
        """A directory of only links renders the root page successfully."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            (
                "directory:\n"
                "  - name: Alpha\n"
                "    url: https://alpha.com\n"
                "  - name: Bravo\n"
                "    url: https://bravo.com\n"
            ),
        )
        app = create_app(str(tmp_path))
        app.config["TESTING"] = True
        with app.test_client() as c:
            response = c.get("/")
            assert response.status_code == 200
            html = response.get_data(as_text=True)
            assert "Alpha" in html
            assert "Bravo" in html


class TestCategoriesOnly:
    """Verify a directory with only categories (no top-level links)."""

    def test_categories_only_renders(self, tmp_path: Path) -> None:
        """A directory of only categories renders the root page."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            (
                "directory:\n"
                "  - name: Group A\n"
                "    entries:\n"
                "      - name: Link1\n"
                "        url: https://link1.com\n"
                "  - name: Group B\n"
                "    entries:\n"
                "      - name: Link2\n"
                "        url: https://link2.com\n"
            ),
        )
        app = create_app(str(tmp_path))
        app.config["TESTING"] = True
        with app.test_client() as c:
            response = c.get("/")
            assert response.status_code == 200
            html = response.get_data(as_text=True)
            assert "Group A" in html
            assert "Group B" in html


class TestSingleEntryCategory:
    """Verify a category with exactly one link."""

    def test_single_entry_category(self, tmp_path: Path) -> None:
        """A category with one link loads and renders correctly."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            (
                "directory:\n"
                "  - name: Solo\n"
                "    entries:\n"
                "      - name: OnlyChild\n"
                "        url: https://only.com\n"
            ),
        )
        directory = load_directory(str(tmp_path))
        assert "onlychild" in directory.slug_map


class TestNumericName:
    """Verify that purely numeric names work correctly."""

    def test_numeric_name_redirect(self, tmp_path: Path) -> None:
        """A link with a numeric name redirects correctly."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            "directory:\n  - name: '404'\n    url: https://http.cat/404\n",
        )
        app = create_app(str(tmp_path))
        app.config["TESTING"] = True
        with app.test_client() as c:
            response = c.get("/404")
            assert response.status_code == 302
            assert response.headers["Location"] == "https://http.cat/404"


class TestURLWithQueryString:
    """Verify that link URLs with query strings are preserved."""

    def test_query_string_preserved(self, tmp_path: Path) -> None:
        """The redirect preserves the full URL including query parameters."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            (
                "directory:\n"
                "  - name: Search\n"
                "    url: https://google.com/search?q=hello&lang=en\n"
            ),
        )
        app = create_app(str(tmp_path))
        app.config["TESTING"] = True
        with app.test_client() as c:
            response = c.get("/search")
            assert response.status_code == 302
            assert (
                response.headers["Location"]
                == "https://google.com/search?q=hello&lang=en"
            )


class TestContentType:
    """Verify Content-Type headers on different response types."""

    def test_root_html_content_type(self, tmp_path: Path) -> None:
        """The root page is served with text/html content type."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            "directory:\n  - name: X\n    url: https://x.com\n",
        )
        app = create_app(str(tmp_path))
        app.config["TESTING"] = True
        with app.test_client() as c:
            response = c.get("/")
            assert "text/html" in response.content_type

    def test_static_css_content_type(self, tmp_path: Path) -> None:
        """Static CSS is served with text/css content type."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            "directory:\n  - name: X\n    url: https://x.com\n",
        )
        app = create_app(str(tmp_path))
        app.config["TESTING"] = True
        with app.test_client() as c:
            response = c.get("/static/default.css")
            assert "text/css" in response.content_type
