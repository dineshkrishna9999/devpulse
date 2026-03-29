"""Placeholder tests to verify the testing setup works."""

from devpulse import __version__


def test_version() -> None:
    """Verify the package version is set."""
    assert __version__ == "0.1.0"


def test_import() -> None:
    """Verify the package can be imported."""
    import devpulse

    assert devpulse is not None
