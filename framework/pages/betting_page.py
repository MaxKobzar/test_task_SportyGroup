"""
Betting Page Object for the Sporty Betting web application.
Encapsulates locators, element interactions, and state queries for the dashboard,
bet slip and receipt modal.

Locator policy: stable element ids first. Where the app exposes no id, a class selector is
scoped under the nearest id so a style change elsewhere cannot match it.
"""

import logging
import re
from decimal import Decimal
from typing import TypedDict

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from framework.api.models.models import SelectionType
from framework.data.money import parse_amount
from framework.pages.base_page import BasePage, Locator

logger = logging.getLogger(__name__)

AMOUNT_PATTERN = re.compile(r"€\s*[-+]?\d")


class SlipSelection(TypedDict):
    teams: str
    market: str
    odds: str


class Receipt(TypedDict):
    title: str
    bet_id: str
    match: str
    stake: str
    odds: str
    payout: str
    placed_at: str
    summary: str


class BettingPage(BasePage):
    """Page Object for the sports betting dashboard, bet slip and receipt modal."""

    # Header
    HEADER_BALANCE = (By.ID, "header-balance")

    # Match catalog
    MATCH_CARDS = (By.CSS_SELECTOR, "[id^='match-card-']")

    # Bet slip
    BET_SLIP_COUNT = (By.ID, "bet-slip-count")
    BET_SLIP_EMPTY_STATE = (By.CSS_SELECTOR, "#bet-slip .betSlipBodyEmpty")
    SELECTION_TEAMS = (By.CSS_SELECTOR, "#bet-slip .betSelectionTeams")
    SELECTION_MARKET = (By.CSS_SELECTOR, "#bet-slip .betSelectionMarket")
    SELECTION_ODDS = (By.CSS_SELECTOR, "#bet-slip .betSelectionOdds")
    STAKE_INPUT = (By.ID, "bet-slip-stake-input")
    POTENTIAL_PAYOUT = (By.ID, "bet-slip-potential-payout")
    PLACE_BET_BUTTON = (By.ID, "bet-slip-place-bet")
    PLACING_INDICATOR = (By.CSS_SELECTOR, "#bet-slip .placeBetButtonPlacing, #bet-slip .spinner")
    INLINE_ERROR = (
        By.CSS_SELECTOR,
        "#bet-slip-error, #bet-slip .errorMessage, #bet-slip [class*='errorText']",
    )

    # Receipt modal
    MODAL = (By.ID, "modal-success")
    MODAL_TITLE = (By.CSS_SELECTOR, "#modal-success .modalTitle")
    MODAL_SUMMARY = (By.CSS_SELECTOR, "#modal-success .modalSummary")
    MODAL_BET_ID = (By.ID, "modal-success-bet-id")
    MODAL_MATCH = (By.ID, "modal-success-match")
    MODAL_STAKE = (By.ID, "modal-success-stake")
    MODAL_ODDS = (By.ID, "modal-success-odds")
    MODAL_PAYOUT = (By.ID, "modal-success-payout")
    MODAL_PLACED_AT = (By.ID, "modal-success-placed-at")
    MODAL_CLOSE_BUTTON = (By.ID, "modal-success-close")

    @staticmethod
    def odds_button(match_id: str, selection: SelectionType) -> Locator:
        """Odds button for one outcome of one catalog match."""
        return (By.ID, f"odds-{match_id}-{SelectionType(selection).value.lower()}")

    def wait_until_loaded(self) -> None:
        """Wait until the catalog is rendered and the header shows a fetched balance amount."""
        logger.info("Waiting for matches and balance to load")
        wait = self._wait()
        wait.until(EC.presence_of_element_located(self.MATCH_CARDS))
        wait.until(
            lambda driver: AMOUNT_PATTERN.search(driver.find_element(*self.HEADER_BALANCE).text)
        )

    # --- Header -----------------------------------------------------------------------

    def get_current_balance(self) -> Decimal:
        """Numeric balance shown in the header."""
        return parse_amount(self.get_text(self.HEADER_BALANCE))

    # --- Bet slip ---------------------------------------------------------------------

    def select_outcome(self, match_id: str, selection: SelectionType) -> None:
        """Add an outcome to the bet slip and wait for the stake input."""
        self.click(self.odds_button(match_id, selection))
        self.find_element(self.STAKE_INPUT)

    def get_selection_details(self) -> SlipSelection:
        """Teams, market label and odds of the active slip selection."""
        odds_text = self.get_text(self.SELECTION_ODDS)  # e.g. "Odds: 2.45"
        odds_match = re.search(r"\d+(?:\.\d+)?", odds_text)
        return SlipSelection(
            teams=self.get_text(self.SELECTION_TEAMS),
            market=self.get_text(self.SELECTION_MARKET),
            odds=odds_match.group() if odds_match else odds_text,
        )

    def enter_stake(self, amount: Decimal) -> None:
        """Type the stake into the bet slip."""
        self.type_text(self.STAKE_INPUT, str(amount))

    def get_potential_payout(self) -> Decimal:
        """Potential payout shown in the slip."""
        return parse_amount(self.get_text(self.POTENTIAL_PAYOUT))

    def is_place_bet_enabled(self) -> bool:
        """True if the Place Bet button is neither disabled nor styled as disabled."""
        button = self.find_element(self.PLACE_BET_BUTTON)
        styled_disabled = "placeBetButtonDisabled" in (button.get_attribute("class") or "")
        return button.is_enabled() and not styled_disabled

    def place_bet(self) -> None:
        """Click Place Bet and wait for the placing state to end."""
        button = self.find_element(self.PLACE_BET_BUTTON)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        button.click()
        logger.info("Clicked Place Bet")
        self._wait().until(EC.invisibility_of_element_located(self.PLACING_INDICATOR))

    def is_bet_slip_empty(self) -> bool:
        """True once the slip shows its empty state: no stake input, zero selections."""
        if not self.is_invisible(self.STAKE_INPUT):
            return False
        return self.get_text(self.BET_SLIP_COUNT) == "0" and self.is_visible(
            self.BET_SLIP_EMPTY_STATE
        )

    def get_inline_error(self) -> str | None:
        """Inline slip error text, or None if no error is shown."""
        if self.is_visible(self.INLINE_ERROR, timeout=0):
            return self.get_text(self.INLINE_ERROR)
        return None

    # --- Receipt modal ----------------------------------------------------------------

    def is_receipt_displayed(self, timeout: float | None = None) -> bool:
        """True if the receipt modal becomes visible within the timeout."""
        return self.is_visible(self.MODAL, timeout)

    def is_receipt_closed(self, timeout: float | None = None) -> bool:
        """True if the receipt modal is hidden or removed within the timeout."""
        return self.is_invisible(self.MODAL, timeout)

    def get_receipt_details(self, timeout: float | None = None) -> Receipt:
        """All fields of the receipt modal."""
        self.find_element(self.MODAL, timeout)
        receipt = Receipt(
            title=self.get_text(self.MODAL_TITLE),
            bet_id=self.get_text(self.MODAL_BET_ID),
            match=self.get_text(self.MODAL_MATCH),
            stake=self.get_text(self.MODAL_STAKE),
            odds=self.get_text(self.MODAL_ODDS),
            payout=self.get_text(self.MODAL_PAYOUT),
            placed_at=self.get_text(self.MODAL_PLACED_AT),
            summary=self.get_text(self.MODAL_SUMMARY),
        )
        logger.info("Receipt details: %s", receipt)
        return receipt

    def close_receipt(self) -> None:
        """Dismiss the receipt modal and wait until it is gone."""
        self.click(self.MODAL_CLOSE_BUTTON)
        self._wait().until(EC.invisibility_of_element_located(self.MODAL))
        logger.info("Closed receipt modal")
