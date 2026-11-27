"""Pytest compatibility configuration for the local Windows runner."""

import os

import pytest
import pytest_socket


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_fixture_setup():
    """Permit Windows' local event-loop socket pair without network access."""
    if os.name == "nt":
        pytest_socket.enable_socket()
        pytest_socket.socket_allow_hosts(["127.0.0.1"])

    yield
