"""Test the version."""

import warehouse.version as ver


def test_version() -> None:
    """Test the version."""
    assert list.__len__(str.split(ver.__version__, ".")) == 3
