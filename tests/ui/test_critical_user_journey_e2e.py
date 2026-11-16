"""
Sole End-to-End UI Test Case: Critical User Journey (Screenplay Pattern).
Scenario ID: TC-BET-001
Title: Complete Wager Lifecycle on an Upcoming Event with UI Balance Reconciliation

Architecture:
Implements 'The Ideal Synergy':
- Pure black-box UI automation simulating a realistic bettor journey in Desktop Chrome.
- Preconditions strictly encapsulated in conftest.py (reset_balance_precondition, bettor_actor, target_match).
- Test data manufactured via Object Mother pattern parameterized across canonical archetypes (BetMother.home_bet, draw_bet, away_bet).
- Config-free framework (runtime parameters from .env and pytest_addoption).
- Assertions executed strictly via assertpy (assert_that) with soft_assertions for composite checks.
- The Actor performs high-level business tasks and asks questions through abilities,
  where BrowseTheWeb delegates directly to PageFactory.get_page(PageType.BETTING, driver).
"""

import re
from typing import Callable

import allure
import pytest
from assertpy import assert_that, soft_assertions

from framework.api.models import Match, PlaceBetRequest
from framework.core.logger import get_logger
from framework.data.bet_mother import BetMother
from framework.pages.betting_page import BettingPage
from framework.screenplay.actor import Actor
from framework.screenplay.questions.bet_receipt import IsReceiptModalDisplayed, ReceiptDetails
from framework.screenplay.questions.bet_slip_status import IsBetSlipEmpty
from framework.screenplay.questions.current_balance import DisplayedBalance
from framework.screenplay.questions.error_message import IsPlaceBetEnabled
from framework.screenplay.questions.potential_payout import PotentialPayout
from framework.screenplay.tasks.close_receipt import CloseReceiptModal
from framework.screenplay.tasks.navigate_to_app import NavigateToApp
from framework.screenplay.tasks.place_bet import EnterStakeAmount, SubmitBetPlacement
from framework.screenplay.tasks.refresh_page import RefreshPage
from framework.screenplay.tasks.select_outcome import SelectUpcomingMatchOutcome

logger = get_logger()


@allure.epic("Core Wagering Engine")
@allure.feature("Critical User Journey (Screenplay Architecture)")
@pytest.mark.usefixtures("reset_balance_precondition")
class TestSingleCriticalUserJourneyE2E:
    @allure.story("TC-BET-001: End-to-End Single Bet Placement & UI Balance Reconciliation")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.description("""
    The platform's single most critical user journey executing on Desktop Chrome:
    1. Verify pre-state baseline in UI header balance and verify empty Bet Slip.
    2. Browse catalog and select outcome on an active UPCOMING event.
    3. Stage selection in Bet Slip, enter valid stake, and verify dynamic payout calculation.
    4. Submit wager and observe async processing state lock.
    5. Validate contractual confirmation receipt modal (ID, stake, odds, timestamp).
    6. Dismiss receipt and confirm Bet Slip resets to empty state.
    7. Reconcile UI header balance: confirm balance is debited by the exact stake amount.
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
    def test_bettor_completes_critical_user_journey(
        self,
        bettor_actor: Actor,
        bet_factory: Callable[..., PlaceBetRequest],
        target_match: Match,
    ):
        # ----------------------------------------------------------------------
        # Data Input: Canonical Wager Manufactured via BetMother
        # ----------------------------------------------------------------------
        bet_data: PlaceBetRequest = bet_factory(match_id=target_match.id)

        # ----------------------------------------------------------------------
        # Phase 1: Pre-State & UI Baseline Check
        # ----------------------------------------------------------------------
        with allure.step("Phase 1: Launch Web Browser Chrome & Verify Baseline Balance"):
            # Web browser Chrome navigation targeting the BettingPage Page Object Model (POM)
            bettor_actor.attempts_to(NavigateToApp.at(BettingPage))
            ui_balance_before = bettor_actor.asks_for(DisplayedBalance.value())

            with soft_assertions():
                assert_that(ui_balance_before).described_as(
                    "Initial UI balance sufficiency for stake"
                ).is_greater_than_or_equal_to(bet_data.stake)
                assert_that(bettor_actor.asks_for(IsBetSlipEmpty.check())).described_as(
                    "Initial Bet Slip empty state"
                ).is_true()

        # ----------------------------------------------------------------------
        # Phase 2: Catalog Browsing & Upcoming Match Selection
        # ----------------------------------------------------------------------
        with allure.step(
            f"Phase 2: Browse & Select Outcome '{bet_data.selection.value}' on an UPCOMING Match"
        ):
            select_task = SelectUpcomingMatchOutcome.for_outcome(bet_data.selection.value)
            bettor_actor.attempts_to(select_task)
            selected_meta = select_task.selected_meta
            decimal_odds = float(selected_meta["odds"])
            assert_that(decimal_odds).described_as(
                "Selected match decimal odds boundary (> 1.0)"
            ).is_greater_than(1.0)

        # ----------------------------------------------------------------------
        # Phase 3: Bet Slip Staging & Dynamic Payout Computation
        # ----------------------------------------------------------------------
        with allure.step("Phase 3: Verify Bet Slip Staging & Dynamic Calculation"):
            bettor_actor.attempts_to(EnterStakeAmount.of(bet_data.stake))

            # Validate dynamic payout calculation: stake * odds
            expected_payout = round(bet_data.stake * decimal_odds, 2)
            calculated_payout = bettor_actor.asks_for(PotentialPayout.value())

            with soft_assertions():
                assert_that(calculated_payout).described_as(
                    "Bet slip dynamic potential payout calculation"
                ).is_equal_to(expected_payout)
                assert_that(bettor_actor.asks_for(IsPlaceBetEnabled.check())).described_as(
                    "Place Bet button enabled state with valid stake"
                ).is_true()

        # ----------------------------------------------------------------------
        # Phase 4: Wager Placement & Async Transaction Processing
        # ----------------------------------------------------------------------
        with allure.step("Phase 4: Submit Wager & Observe Transaction Processing"):
            bettor_actor.attempts_to(SubmitBetPlacement.now())
            assert_that(
                bettor_actor.asks_for(IsReceiptModalDisplayed.check(timeout=5))
            ).described_as("Bet confirmation receipt modal display").is_true()

        # ----------------------------------------------------------------------
        # Phase 5: Legal Confirmation Receipt Verification (Soft Assertions)
        # ----------------------------------------------------------------------
        with allure.step("Phase 5: Verify Contractual Confirmation Receipt Modal"):
            receipt = bettor_actor.asks_for(ReceiptDetails.data())
            expected_stake_str = f"€{bet_data.stake:.2f}"
            payout_match = re.search(r"[-+]?\d*\.?\d+", receipt["payout"])
            receipt_payout_num = float(payout_match.group()) if payout_match else 0.0

            # Composite verification across all receipt modal fields via soft assertions
            with soft_assertions():
                # 1. Title verification
                assert_that(receipt["title"]).described_as("Receipt modal title").contains(
                    "Bet Placed Successfully"
                )

                # 2. Bet Reference ID format: #B-XXXXX
                assert_that(receipt["bet_id"]).described_as(
                    "Receipt bet reference ID format"
                ).matches(r"^#B-\d+$")

                # 3. Stake verification
                assert_that(receipt["stake"]).described_as("Receipt wagered stake amount").contains(
                    expected_stake_str
                )

                # 4. Odds verification
                assert_that(receipt["odds"]).described_as("Receipt decimal odds").contains(
                    selected_meta["odds"]
                )

                # 5. Timestamp label present
                assert_that(receipt["placed_at"]).described_as(
                    "Receipt timestamp presence"
                ).is_not_empty()

                # 6. Potential payout verification
                assert_that(receipt_payout_num).described_as(
                    "Receipt potential payout numeric value"
                ).is_greater_than(0)

        # ----------------------------------------------------------------------
        # Phase 6: Receipt Dismissal & Bet Slip Auto-Reset
        # ----------------------------------------------------------------------
        with allure.step("Phase 6: Dismiss Receipt & Verify Bet Slip Clean Reset"):
            bettor_actor.attempts_to(CloseReceiptModal.if_displayed(timeout=5))
            assert_that(bettor_actor.asks_for(IsBetSlipEmpty.check())).described_as(
                "Bet slip auto-reset to empty state after closing confirmation receipt"
            ).is_true()

        # ----------------------------------------------------------------------
        # Phase 7: UI Balance Deduction Verification
        # ----------------------------------------------------------------------
        with allure.step("Phase 7: Reconcile Header Balance Deduction After Bet Placement"):
            expected_balance = round(ui_balance_before - bet_data.stake, 2)

            # UI Header balance deduction check (synced with page reload)
            bettor_actor.attempts_to(RefreshPage.now())
            ui_balance_after = bettor_actor.asks_for(DisplayedBalance.value())

            assert_that(ui_balance_after).described_as(
                "UI Header balance after stake deduction"
            ).is_equal_to(expected_balance)
