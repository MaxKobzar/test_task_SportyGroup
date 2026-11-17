"""Screenplay Tasks: what an Actor does, one class per module."""

from framework.screenplay.tasks.close_receipt_modal import CloseReceiptModal
from framework.screenplay.tasks.enter_stake_amount import EnterStakeAmount
from framework.screenplay.tasks.navigate_to_app import NavigateToApp
from framework.screenplay.tasks.place_bet_via_api import PlaceBetViaApi
from framework.screenplay.tasks.refresh_page import RefreshPage
from framework.screenplay.tasks.reset_balance_via_api import ResetBalanceViaApi
from framework.screenplay.tasks.select_match_outcome import SelectMatchOutcome
from framework.screenplay.tasks.submit_bet_placement import SubmitBetPlacement

__all__ = [
    "CloseReceiptModal",
    "EnterStakeAmount",
    "NavigateToApp",
    "PlaceBetViaApi",
    "RefreshPage",
    "ResetBalanceViaApi",
    "SelectMatchOutcome",
    "SubmitBetPlacement",
]
