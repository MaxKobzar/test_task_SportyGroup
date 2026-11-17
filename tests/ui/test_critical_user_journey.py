"""
E2E UI Test Case: TC-BET-001, a bettor places a single bet and gets a correct receipt.

Why this test (risk-based selection):
- This is the core revenue journey: select odds -> enter stake -> place bet -> receipt ->
  balance. If any step breaks, no bet can be placed.
- RSK-02 Payout and receipt correctness scores 9/9. The receipt is the user's record of the
  bet, so a wrong payout, wrong match order or missing selection directly misinforms the
  customer. Only the rendered UI shows what the customer actually sees, so this belongs at
  the E2E level. Rejection and business rules are tested more cheaply at the API level
  (TC-BET-002, TC-BET-003).
- Every receipt value is checked against what was shown before placement (slip and match
  catalog), as the brief requires, not just for being present.

Design notes:
- Parametrized over DRAW/HOME/AWAY: each outcome button must put its own odds and market
  label on the slip and the receipt, so all three wirings are covered through the real UI.
- The match comes from the API catalog with kickoff strictly after today (`target_match`),
  and its odds are the expected odds. No hardcoded IDs or values.
- The balance is read right after placement, WITHOUT a page reload: that is what the user
  sees. A reload would hide BUG-005.
- Soft assertions collect every receipt and balance defect in a single run.
- xfail(strict=True, raises=AssertionError) for the known receipt and balance defects:
  Selenium/infra errors still fail loudly, and when the bugs are fixed the XPASS is the
  signal to remove the marker.
"""

import allure
import pytest
from assertpy import assert_that, soft_assertions

from framework.api import Match, PlaceBetRequest, SelectionType
from framework.data import BetMother, format_eur, to_cents
from framework.pages import BettingPage
from framework.screenplay import Actor
from framework.screenplay.questions import (
    BetSlipSelection,
    DisplayedBalance,
    IsBetSlipEmpty,
    IsPlaceBetEnabled,
    IsReceiptModalClosed,
    IsReceiptModalDisplayed,
    PotentialPayout,
    ReceiptDetails,
)
from framework.screenplay.tasks import (
    CloseReceiptModal,
    EnterStakeAmount,
    NavigateToApp,
    SelectMatchOutcome,
    SubmitBetPlacement,
)

RECEIPT_TIMEOUT_SECONDS = 8


@allure.epic("Core Wagering Engine")
@allure.feature("Critical User Journey")
@pytest.mark.ui
@pytest.mark.usefixtures("reset_balance_precondition")
class TestSingleBetCriticalUserJourney:
    @allure.story("TC-BET-001: Place a single bet and receive a correct receipt")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.xfail(
        raises=AssertionError,
        reason=(
            "BUG-002 receipt payout is stake x 2; BUG-006 receipt shows away vs home; "
            "BUG-009 receipt omits the selection; BUG-005 header balance not updated"
        ),
    )
    @pytest.mark.parametrize(
        "selection",
        [SelectionType.DRAW, SelectionType.HOME, SelectionType.AWAY],
        ids=lambda selection: selection.value,
    )
    def test_bettor_places_single_bet_and_receives_receipt(
        self, bettor_actor: Actor, target_match: Match, selection: SelectionType
    ) -> None:
        bet: PlaceBetRequest = BetMother.for_outcome(selection, match_id=target_match.id)
        odds = target_match.odds.for_selection(bet.selection)
        expected_payout = to_cents(bet.stake * odds)
        expected_match_label = f"{target_match.home_team} vs {target_match.away_team}"

        with allure.step("Open the app and record the starting balance"):
            bettor_actor.attempts_to(NavigateToApp.at(BettingPage))
            balance_before = bettor_actor.asks_for(DisplayedBalance.value())
            assert_that(bettor_actor.asks_for(IsBetSlipEmpty.check())).described_as(
                "Bet slip is empty on arrival"
            ).is_true()

        with allure.step(f"Select {bet.selection.value} on {expected_match_label}"):
            bettor_actor.attempts_to(SelectMatchOutcome.on(target_match.id, bet.selection))
            slip = bettor_actor.asks_for(BetSlipSelection.details())
            with soft_assertions():
                assert_that(slip["teams"]).described_as("Slip match label").is_equal_to(
                    expected_match_label
                )
                assert_that(slip["odds"]).described_as("Slip odds vs catalog").is_equal_to(
                    f"{odds:.2f}"
                )

        with allure.step(f"Enter stake {format_eur(bet.stake)} and check the potential payout"):
            bettor_actor.attempts_to(EnterStakeAmount.of(bet.stake))
            with soft_assertions():
                assert_that(bettor_actor.asks_for(PotentialPayout.value())).described_as(
                    "Slip potential payout = stake x odds"
                ).is_equal_to(expected_payout)
                assert_that(bettor_actor.asks_for(IsPlaceBetEnabled.check())).described_as(
                    "Place Bet enabled for a valid stake"
                ).is_true()

        with allure.step("Place the bet"):
            bettor_actor.attempts_to(SubmitBetPlacement.now())
            assert_that(
                bettor_actor.asks_for(IsReceiptModalDisplayed.check(RECEIPT_TIMEOUT_SECONDS))
            ).described_as("Success receipt modal is shown").is_true()

        with allure.step("Verify receipt, slip reset and balance deduction"):
            receipt = bettor_actor.asks_for(ReceiptDetails.data())
            slip_empty_after = bettor_actor.asks_for(IsBetSlipEmpty.check())
            balance_after = bettor_actor.asks_for(DisplayedBalance.value())

            with soft_assertions():
                assert_that(receipt["bet_id"]).described_as("Receipt bet ID").matches(r"^#B-\d+$")
                assert_that(receipt["match"]).described_as(
                    "Receipt match, home team first"
                ).is_equal_to(expected_match_label)
                assert_that(receipt["summary"]).described_as(
                    "Receipt shows the selection from the slip"
                ).contains(slip["market"])
                assert_that(receipt["stake"]).described_as("Receipt stake").is_equal_to(
                    format_eur(bet.stake)
                )
                assert_that(receipt["odds"]).described_as("Receipt odds at placement").is_equal_to(
                    f"{odds:.2f}"
                )
                assert_that(receipt["payout"]).described_as(
                    "Receipt payout = stake x odds"
                ).is_equal_to(format_eur(expected_payout))
                assert_that(receipt["placed_at"]).described_as(
                    "Receipt placement timestamp"
                ).is_not_empty()
                assert_that(slip_empty_after).described_as(
                    "Bet slip cleared after placement"
                ).is_true()
                assert_that(balance_after).described_as(
                    "Header balance reduced by the stake, without reload"
                ).is_equal_to(balance_before - bet.stake)

            bettor_actor.attempts_to(CloseReceiptModal.if_displayed())
            assert_that(bettor_actor.asks_for(IsReceiptModalClosed.check())).described_as(
                "Receipt modal is closed"
            ).is_true()
