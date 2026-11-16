"""
Shared test suite fixtures.
Provides high-level cross-cutting test fixtures and preconditions for all test layers (API & UI).
"""

from datetime import date

import pytest

from framework.api.client import BettingApiClient
from framework.api.models import Match, ResetBalanceResponse
from framework.core.logger import get_logger

logger = get_logger()


@pytest.fixture(autouse=True)
def log_test_lifecycle(request):
    """Log the start and finish of every test case."""
    logger.info(f"=== [START TEST] {request.node.name} ===")
    yield
    logger.info(f"=== [END TEST] {request.node.name} ===")


@pytest.fixture()
def reset_balance_precondition(api_client: BettingApiClient) -> ResetBalanceResponse:
    """Precondition: Ensure candidate user starts each test with a pristine baseline balance."""
    logger.info("Precondition: Resetting user balance via API...")
    return api_client.post_reset_balance()


@pytest.fixture()
def target_match(api_client: BettingApiClient) -> Match:
    """
    Precondition: Dynamically resolve an active upcoming match fixture from the live catalog.
    Prevents test flakiness from hardcoded fixture IDs or stale events.
    """
    matches = api_client.get_matches()
    for match in matches:
        if match.kickoff_date >= date.today():
            return match
    if not matches:
        raise RuntimeError("Live match catalog feed returned no fixtures.")
    return matches[0]
