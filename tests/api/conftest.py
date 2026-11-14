"""
API Test Fixtures.
Provides isolated preconditions for REST API test cases.
"""

import pytest

from framework.api.client import BettingApiClient
from framework.core.logger import get_logger

logger = get_logger("APIConftest")


@pytest.fixture(autouse=True)
def reset_api_state(api_client: BettingApiClient):
    """Ensure baseline user state is restored before every API test execution."""
    logger.info("Resetting backend user state prior to API test...")
    resp = api_client.reset_balance()
    assert resp.status_code == 200, f"API Reset failed: {resp.text}"
    return
