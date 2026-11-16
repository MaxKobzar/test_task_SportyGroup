"""
Sole API Test Case: Critical Wagering Transaction & Business Rule Validation (Screenplay Pattern).
Scenario ID: TC-API-001
Title: Atomic Bet Placement, Dynamic Payout Calculation, and Ledger Balance Invariance

Architecture:
Implements Murat's Master Test Architect Risk-Based Standards:
- Pure REST API validation targeting backend service layer without browser overhead.
- Screenplay Pattern: The Actor ('Bettor') uses the CallAPI ability to perform Tasks and ask Questions.
- Strict Pydantic V2 Contract Models ensuring OpenAPI 3.0.3 schema adherence.
- Fluent assertions via assertpy (assert_that) with soft_assertions for composite contract checks.
- Comprehensive Allure reporting with Epics, Features, Stories, Severities, and Step Telemetry.
- Backend state isolation precondition (reset_balance_precondition) configured in conftest.py.
"""

from typing import Callable

import allure
import pytest
from assertpy import assert_that, soft_assertions

from framework.api.models import Balance, Match, PlaceBetRequest, PlaceBetResponse
from framework.core.logger import get_logger
from framework.data.bet_mother import BetMother
from framework.screenplay.actor import Actor
from framework.screenplay.questions.api_balance import ApiBalance
from framework.screenplay.questions.api_matches import ApiMatchesFeed
from framework.screenplay.tasks.place_bet_api import PlaceBetViaApi

logger = get_logger()


@allure.epic("Core Wagering Engine")
@allure.feature("Bet Placement Direct REST API (Screenplay Architecture)")
@pytest.mark.usefixtures("reset_balance_precondition")
class TestBetPlacementApi:
    @allure.story(
        "TC-API-001: Atomic Bet Placement, Dynamic Payout Calculation, and Ledger Invariance"
    )
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.description("""
    Validates the single most critical financial and operational transaction in the sportsbook:
    1. Pre-State Baseline: Query ledger balance directly via GET /api/balance; verify currency (EUR)
       and confirm funds sufficiency.
    2. Catalog Discovery & Odds Contract: Retrieve match feed via GET /api/matches and dynamically
       resolve market odds for the parameterized outcome selection ('HOME', 'DRAW', 'AWAY').
    3. Test Data Generation (Object Mother): Fabricate domain-validated PlaceBetRequest via BetMother.
    4. Transaction Execution: Submit single bet via POST /api/place-bet using PlaceBetViaApi.from_request.
    5. Contract Schema & Business Rule Verification: Soft-assert all fields against PlaceBetResponse:
       - Match ID, selection, and stake fidelity against fabricated BetMother model.
       - Mathematical payout calculation rule: payout == round(stake * odds, 2).
       - Ledger balance debit rule: balance == round(initial_balance - stake, 2).
    6. Ledger Persistence Invariance: Independently query GET /api/balance to verify the debited
       state is committed and persistent across subsequent requests.
    """)
    @pytest.mark.parametrize(
        "bet_factory",
        [
            BetMother.home_bet,
            BetMother.draw_bet,
            BetMother.away_bet,
        ],
        ids=["home_bet", "draw_bet", "away_bet"],
    )
    def test_bettor_places_single_bet_validates_business_rules_and_ledger_invariance(
        self, api_actor: Actor, bet_factory: Callable[..., PlaceBetRequest], target_match: Match
    ) -> None:
        stake_amount = BetMother.DEFAULT_STAKE

        # ----------------------------------------------------------------------
        # Phase 1: Pre-State Baseline & Account Currency Check
        # ----------------------------------------------------------------------
        with allure.step("Phase 1: Query Baseline Balance & Verify Ledger Currency"):
            baseline_balance: Balance = api_actor.asks_for(ApiBalance.value())
            initial_balance = baseline_balance.balance

            with soft_assertions():
                assert_that(baseline_balance.currency).described_as(
                    "Baseline account ledger currency"
                ).is_equal_to("EUR")
                assert_that(initial_balance).described_as(
                    "Baseline funds sufficiency for stake"
                ).is_greater_than_or_equal_to(stake_amount)

        # ----------------------------------------------------------------------
        # Phase 2: Match Catalog Retrieval & Target Event Selection
        # ----------------------------------------------------------------------
        with allure.step("Phase 2: Retrieve Active Matches Feed & Select Target Fixture"):
            matches = api_actor.asks_for(ApiMatchesFeed.all())
            assert_that(matches).described_as("Active match catalog feed").is_not_empty()

        # ----------------------------------------------------------------------
        # Phase 3: Manufacture Test Data via Object Mother & Execute Placement
        # ----------------------------------------------------------------------
        with allure.step("Phase 3: Manufacture Test Data via BetMother & Place Single Bet"):
            bet_request: PlaceBetRequest = bet_factory(
                match_id=target_match.id,
                stake=stake_amount,
            )
            decimal_odds = target_match.odds.for_selection(bet_request.selection)

            place_bet_task = PlaceBetViaApi.from_request(bet_request)
            api_actor.attempts_to(place_bet_task)

            bet_receipt: PlaceBetResponse = place_bet_task.response  # type: ignore[assignment]

        # ----------------------------------------------------------------------
        # Phase 4: Validate Contract Schema & Mathematical Business Rules
        # ----------------------------------------------------------------------
        with allure.step("Phase 4: Validate Contract Schema, Payout Math, and Balance Debit"):
            expected_payout = round(stake_amount * decimal_odds, 2)
            expected_balance = round(initial_balance - stake_amount, 2)

            with soft_assertions():
                # 1. Status message confirmation
                assert_that(bet_receipt.message).described_as("Confirmation message").is_equal_to(
                    "Bet placed successfully"
                )

                # 2. Match ID fidelity against Object Mother request
                assert_that(bet_receipt.match_id).described_as(
                    "Wagered match ID fidelity"
                ).is_equal_to(bet_request.match_id)

                # 3. Selection fidelity against Object Mother request
                assert_that(bet_receipt.selection).described_as(
                    "Wagered outcome selection fidelity"
                ).is_equal_to(bet_request.selection)

                # 4. Stake fidelity against Object Mother request
                assert_that(bet_receipt.stake).described_as(
                    "Contractual wager stake amount"
                ).is_equal_to(bet_request.stake)

                # 5. Odds contract fidelity
                assert_that(bet_receipt.odds).described_as(
                    "Contractual decimal odds applied to wager"
                ).is_equal_to(decimal_odds)

                # 6. Business Rule: Dynamic payout formula (stake * odds)
                assert_that(bet_receipt.payout).described_as(
                    "Dynamic payout computation formula (stake * odds)"
                ).is_equal_to(expected_payout)

                # 7. Business Rule: Atomic ledger balance debit (initial - stake)
                assert_that(bet_receipt.balance).described_as(
                    "Immediate account balance deduction (initial - stake)"
                ).is_equal_to(expected_balance)

        # ----------------------------------------------------------------------
        # Phase 5: Financial Ledger State Persistence Check
        # ----------------------------------------------------------------------
        with allure.step("Phase 5: Reconcile Backend Financial Ledger State Persistence"):
            persisted_balance: Balance = api_actor.asks_for(ApiBalance.value())

            with soft_assertions():
                assert_that(persisted_balance.balance).described_as(
                    "Persisted balance in backend ledger matching deduction"
                ).is_equal_to(expected_balance)
                assert_that(persisted_balance.balance).described_as(
                    "Persisted balance strictly synchronized with placement response"
                ).is_equal_to(bet_receipt.balance)
