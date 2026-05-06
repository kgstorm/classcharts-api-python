"""Pytest configuration and fixtures for optional live ClassCharts tests."""

from __future__ import annotations

import datetime as dt
import getpass

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command line flag to explicitly enable live API tests."""
    parser.addoption(
        "--live-classcharts",
        action="store_true",
        default=False,
        help="Run live tests that authenticate against the real ClassCharts API",
    )


@pytest.fixture(scope="session")
def live_mode(pytestconfig: pytest.Config) -> bool:
    """Return whether live ClassCharts tests are enabled."""
    return bool(pytestconfig.getoption("--live-classcharts"))


@pytest.fixture(scope="session")
def live_creds(live_mode: bool) -> tuple[str, str]:
    """Prompt for ClassCharts parent credentials when live mode is enabled."""
    if not live_mode:
        pytest.skip("Live test skipped: pass --live-classcharts to run live API tests")

    email = input("ClassCharts parent email: ").strip()
    password = getpass.getpass("ClassCharts parent password: ").strip()

    if not email or not password:
        pytest.skip("Live test skipped: missing credentials")

    return email, password


@pytest.fixture
def last_31_days() -> tuple[str, str]:
    """Return ISO date window from 31 days ago through today."""
    to_date = dt.date.today()
    from_date = to_date - dt.timedelta(days=31)
    return from_date.isoformat(), to_date.isoformat()


@pytest.fixture
def last_14_days() -> tuple[str, str]:
    """Return ISO date window from 14 days ago through today.

    Used for homework to-do checks — matches the approximate recency
    window the ClassCharts app uses when displaying the to-do list.
    """
    to_date = dt.date.today()
    from_date = to_date - dt.timedelta(days=14)
    return from_date.isoformat(), to_date.isoformat()
