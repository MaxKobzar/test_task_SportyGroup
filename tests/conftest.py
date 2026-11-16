"""
Shared test suite fixtures.
Provides high-level cross-cutting test fixtures and preconditions for all test layers (API & UI).
"""

import pytest

from framework.api.client import BettingApiClient
from framework.api.models import ResetBalanceResponse
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
