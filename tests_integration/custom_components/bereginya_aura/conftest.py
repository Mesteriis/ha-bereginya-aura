"""Pytest helpers for live Beregynya AURA runtime tests."""

from __future__ import annotations

import pytest
import pytest_socket


@pytest.fixture
def live_socket_enabled():
    """Fully remove pytest socket restrictions for real upstream e2e calls."""
    pytest_socket._remove_restrictions()
    yield
    pytest_socket._remove_restrictions()
