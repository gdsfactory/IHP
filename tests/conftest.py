"""Shared pytest fixtures for IHP PDK tests."""

from __future__ import annotations

import pytest

from ihp import PDK


@pytest.fixture(autouse=True)
def activate_pdk() -> None:
    """Activate IHP PDK before each test."""
    PDK.activate()
