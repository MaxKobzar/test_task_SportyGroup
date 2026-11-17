"""
API Test Cases: TC-BET-002 (API layer) and TC-BET-003 rows S3/S9, a rejected stake never changes
the user's balance.

Why: ledger integrity is the top risk (RSK-01, score 9) with two Critical bugs confirmed
(BUG-001 overdraft, BUG-004 negative stake adds money), and only the API can enforce it:
any client that skips the UI bypasses the UI's checks.
"""

from collections.abc import Callable
from decimal import Decimal

import allure
import pytest
from assertpy import assert_that, soft_assertions

from framework.api import ApiException, ApiUnprocessableEntityError, Match
from framework.data import BetMother
from framework.screenplay import Actor
from framework.screenplay.questions import ApiBalance
from framework.screenplay.tasks import PlaceBetViaApi

# (stake derived from the drained balance, expected typed API exception, expected error code).
# Status classes follow Spec §5.3: every illegal stake is a semantic validation failure (422).
# The spec defines no error code for insufficient balance, so that case checks the status and
# the Error422 contract only (expected code None); stake codes are the documented 422 examples.
ILLEGAL_STAKES = [
    pytest.param(
        lambda balance: balance + Decimal("0.01"),
        ApiUnprocessableEntityError,
        None,
        id="TC-BET-002_overdraft_balance_plus_one_cent",
        marks=pytest.mark.xfail(
            reason="BUG-001: API accepts stake > balance and drives the balance negative",
        ),
    ),
    pytest.param(
        lambda _: Decimal("-50.00"),
        ApiUnprocessableEntityError,
        "invalid_stake_min",
        id="TC-BET-003-S3_negative_stake",
        marks=pytest.mark.xfail(
            reason="BUG-004: API accepts a negative stake and credits the balance",
        ),
    ),
    pytest.param(
        lambda _: Decimal("10.001"),
        ApiUnprocessableEntityError,
        "invalid_stake_precision",
        id="TC-BET-003-S9_three_decimal_places",
    ),
]


@allure.epic("Core Wagering Engine")
@allure.feature("Bet Placement REST API: Ledger Integrity")
@pytest.mark.api
class TestRejectedStakeLedgerIntegrity:
    @allure.story("TC-BET-002 / TC-BET-003: A rejected stake never changes the balance")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.parametrize(("stake_for", "expected_exception", "expected_error"), ILLEGAL_STAKES)
    def test_illegal_stake_is_rejected_and_balance_unchanged(
        self,
        api_actor: Actor,
        target_match: Match,
        drained_balance: Decimal,
        stake_for: Callable[[Decimal], Decimal],
        expected_exception: type[ApiException],
        expected_error: str | None,
    ) -> None:
        """The API rejects the stake with the rule's error, and the balance stays as it was."""
        stake = stake_for(drained_balance)
        bet = BetMother.with_illegal_stake(match_id=target_match.id, stake=stake)

        with (
            allure.step(f"Stake {stake} against balance €{drained_balance:.2f} is rejected"),
            pytest.raises(expected_exception) as rejection,
        ):
            api_actor.attempts_to(PlaceBetViaApi.from_request(bet))

        balance_after = api_actor.asks_for(ApiBalance.value()).balance
        error = rejection.value.error

        with allure.step("Error contract and unchanged balance"), soft_assertions():
            if expected_error is not None:
                assert_that(error and error.error).described_as("Error model code").is_equal_to(
                    expected_error
                )
            assert_that(balance_after).described_as(
                "Stored balance after a rejected bet"
            ).is_equal_to(drained_balance)
