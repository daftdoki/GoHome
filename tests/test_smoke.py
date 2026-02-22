"""Smoke test to verify the package is importable."""


def test_import_gohome() -> None:
    """Importing gohome should succeed without errors."""
    import gohome

    assert gohome.__doc__ is not None
