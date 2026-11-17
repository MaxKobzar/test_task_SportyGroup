"""
Shared test suite fixtures.
Provides high-level cross-cutting test fixtures and preconditions for all test layers (API & UI).
"""

import logging
from datetime import datetime, timedelta, timezone

import pytest

from framework.api.client import BettingApiClient
from framework.api.models.models import Match, ResetBalanceResponse

logger = logging.getLogger(__name__)

# A match kicking off within this window could become "today" on the server (UTC) during the
# run, or already be today in another timezone; the margin keeps the event-status rule out.
KICKOFF_SAFETY_MARGIN = timedelta(days=1)


@pytest.fixture
def reset_balance_precondition(api_client: BettingApiClient) -> ResetBalanceResponse:
    """Precondition: Ensure candidate user starts each test with a pristine baseline balance."""
    logger.info("Precondition: resetting user balance via API")
    return api_client.reset_balance()


@pytest.fixture
def target_match(api_client: BettingApiClient) -> Match:
    """
    Precondition: Resolve an upcoming match from the live catalog.
    Kickoff must be after today (UTC) plus a safety margin, so a rejection can only come from
    the rule under test, never from the event-status rule (BUG-003). No hardcoded IDs: the
    catalog is static but the calendar is not.
    """
    cutoff = datetime.now(timezone.utc).date() + KICKOFF_SAFETY_MARGIN
    upcoming = [match for match in api_client.get_matches() if match.kickoff_date > cutoff]
    if not upcoming:
        raise RuntimeError(f"Match catalog has no fixture with kickoff after {cutoff}.")
    return upcoming[0]
