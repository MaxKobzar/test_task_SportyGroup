"""
Betting Page Object for the Sporty Betting web application.
Encapsulates DOM locators, element interactions, and validation queries.
"""

import re
from typing import Dict, Optional

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from framework.core.logger import get_logger
from framework.pages.base_page import BasePage

logger = get_logger()


class BettingPage(BasePage):
    """Page Object Model representing the sports betting dashboard and bet slip."""

    # Header Locators
    LOC_HEADER_BALANCE = (By.ID, "header-balance")
    LOC_HEADER_TITLE = (By.ID, "header-title")

    # Match Section Locators
    LOC_MATCH_CARDS = (By.CSS_SELECTOR, ".matchCard")
    LOC_ODDS_BUTTONS = (By.CSS_SELECTOR, "button.oddsButton")

    # Bet Slip Locators
    LOC_BET_SLIP = (By.ID, "bet-slip")
    LOC_BET_SLIP_COUNT = (By.ID, "bet-slip-count")
    LOC_REMOVE_ALL_BTN = (By.ID, "bet-slip-remove-all")
    LOC_SELECTION_TEAMS = (By.CSS_SELECTOR, ".betSelectionTeams")
    LOC_SELECTION_MARKET = (By.CSS_SELECTOR, ".betSelectionMarket")
    LOC_SELECTION_ODDS = (By.CSS_SELECTOR, ".betSelectionOdds")
    LOC_REMOVE_SELECTION_BTN = (By.ID, "bet-slip-selection-remove")
    LOC_STAKE_INPUT = (By.ID, "bet-slip-stake-input")
    LOC_TOTAL_STAKE = (By.ID, "bet-slip-total-stake")
    LOC_POTENTIAL_PAYOUT = (By.ID, "bet-slip-potential-payout")
    LOC_PLACE_BET_BTN = (By.ID, "bet-slip-place-bet")
    LOC_INLINE_ERROR = (By.CSS_SELECTOR, "#bet-slip-error, .errorMessage, [class*='errorText']")

    # Receipt / Success Modal Locators
    LOC_MODAL_ROOT = (By.ID, "modal-success")
    LOC_MODAL_CONTAINER = (By.CSS_SELECTOR, "#modal-success, div[role='dialog']")
    LOC_MODAL_TITLE = (By.CSS_SELECTOR, ".modalTitle")
    LOC_MODAL_BET_ID = (By.ID, "modal-success-bet-id")
    LOC_MODAL_MATCH = (By.ID, "modal-success-match")
    LOC_MODAL_STAKE = (By.ID, "modal-success-stake")
    LOC_MODAL_ODDS = (By.ID, "modal-success-odds")
    LOC_MODAL_PAYOUT = (By.ID, "modal-success-payout")
    LOC_MODAL_PLACED_AT = (By.ID, "modal-success-placed-at")
    LOC_MODAL_CLOSE_BTN = (By.ID, "modal-success-close")
    LOC_MODAL_CLOSE_X = (By.ID, "modal-success-close-x")

    def __init__(self, driver: webdriver.Remote, timeout: int = 10):
        super().__init__(driver=driver, timeout=timeout)

    @classmethod
    def get_url(cls, base_url: Optional[str] = None, user_id: Optional[str] = None) -> str:
        """Construct the full application URL for the betting page from config or environment."""
        import os

        base = base_url or os.getenv("BASE_URL") or "https://qae-assignment-tau.vercel.app"
        uid = user_id or os.getenv("USER_ID") or "candidate-Mc2IYbjdqhj8"
        sep = "&" if "?" in base else "?"
        return f"{base}{sep}user-id={uid}"

    def wait_until_loaded(self) -> "BettingPage":
        """Wait for the initial matches and odds buttons to be rendered."""
        logger.info("Waiting for betting page to hydrate and load matches...")
        self.wait.until(EC.presence_of_element_located(self.LOC_HEADER_BALANCE))
        self.wait.until(EC.presence_of_element_located(self.LOC_ODDS_BUTTONS))
        return self

    def get_current_balance(self) -> float:
        """Extract the numeric balance value from the header."""
        balance_elem = self.find_element(self.LOC_HEADER_BALANCE)
        raw_text = balance_elem.text
        logger.info(f"Header balance raw text: '{raw_text}'")
        match = re.search(r"[-+]?\d*\.?\d+", raw_text.replace(",", ""))
        if match:
            return float(match.group())
        raise ValueError(f"Could not parse numeric balance from header: '{raw_text}'")

    def get_selection_details(self) -> Dict[str, str]:
        """Retrieve the details of the active selection in the bet slip."""
        teams = self.get_text(self.LOC_SELECTION_TEAMS)
        market = self.get_text(self.LOC_SELECTION_MARKET)
        odds_raw = self.get_text(self.LOC_SELECTION_ODDS)
        # Extract numeric odds from "Odds: 2.45"
        odds_match = re.search(r"\d+\.?\d*", odds_raw)
        odds = odds_match.group() if odds_match else odds_raw
        return {"teams": teams, "market": market, "odds": odds}

    def enter_stake(self, amount: float | str) -> "BettingPage":
        """Enter stake amount into the bet slip stake input."""
        inp = self.find_element(self.LOC_STAKE_INPUT)
        inp.clear()
        inp.send_keys(str(amount))
        logger.info(f"Entered stake amount: {amount}")
        return self

    def get_potential_payout_text(self) -> str:
        """Get the displayed potential payout text."""
        elem = self.find_element(self.LOC_POTENTIAL_PAYOUT)
        return elem.text.strip()

    def get_potential_payout_value(self) -> float:
        """Parse the numeric potential payout."""
        text = self.get_potential_payout_text()
        match = re.search(r"[-+]?\d*\.?\d+", text.replace(",", ""))
        if match:
            return float(match.group())
        raise ValueError(f"Could not parse numeric payout from: '{text}'")

    def is_place_bet_enabled(self) -> bool:
        """Check if Place Bet button is enabled and clickable."""
        btn = self.find_element(self.LOC_PLACE_BET_BTN)
        is_disabled = btn.get_attribute("disabled") is not None
        has_disabled_class = "placeBetButtonDisabled" in (btn.get_attribute("class") or "")
        return not is_disabled and not has_disabled_class

    def click_place_bet(self) -> "BettingPage":
        """Click the Place Bet button and wait for placement transaction to conclude."""
        btn = self.find_element(self.LOC_PLACE_BET_BTN)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
        btn.click()
        logger.info("Clicked 'PLACE BET' button")
        # Wait for "PLACING..." transition to complete
        try:
            WebDriverWait(self.driver, 10).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, ".placeBetButtonPlacing, .spinner")
                )
            )
        except (TimeoutException, NoSuchElementException, WebDriverException):
            pass
        return self

    def is_receipt_displayed(self, timeout: int = 5) -> bool:
        """Check if receipt modal or close button is displayed."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.LOC_MODAL_ROOT)
            )
            return True
        except (TimeoutException, NoSuchElementException, WebDriverException):
            # Fallback to close button check
            return self.is_visible(self.LOC_MODAL_CLOSE_BTN, timeout=timeout)

    def get_receipt_details(self, timeout: int = 5) -> Dict[str, str]:
        """Retrieve all data attributes from the confirmed bet receipt modal."""
        self.wait.until(EC.visibility_of_element_located(self.LOC_MODAL_ROOT))
        title = self.get_text(self.LOC_MODAL_TITLE)
        bet_id = self.get_text(self.LOC_MODAL_BET_ID)
        match = self.get_text(self.LOC_MODAL_MATCH)
        stake = self.get_text(self.LOC_MODAL_STAKE)
        odds = self.get_text(self.LOC_MODAL_ODDS)
        payout = self.get_text(self.LOC_MODAL_PAYOUT)
        placed_at = self.get_text(self.LOC_MODAL_PLACED_AT)

        details = {
            "title": title,
            "bet_id": bet_id,
            "match": match,
            "stake": stake,
            "odds": odds,
            "payout": payout,
            "placed_at": placed_at,
        }
        logger.info(f"Confirmed receipt details: {details}")
        return details

    def close_receipt(self) -> "BettingPage":
        """Close the bet receipt modal and wait for dismissal."""
        close_btn = self.find_element(self.LOC_MODAL_CLOSE_BTN)
        close_btn.click()
        logger.info("Closed receipt modal")
        try:
            WebDriverWait(self.driver, 5).until(
                EC.invisibility_of_element_located(self.LOC_MODAL_ROOT)
            )
        except (TimeoutException, NoSuchElementException, WebDriverException):
            pass
        return self

    def is_bet_slip_empty(self) -> bool:
        """Check if the bet slip is in its empty state (no active selections)."""
        slip_elem = self.find_element(self.LOC_BET_SLIP)
        slip_text = slip_elem.text
        has_empty_indicator = "Select odds to place a bet" in slip_text or "0" in slip_text
        has_stake_input = self.is_visible(self.LOC_STAKE_INPUT, timeout=1)
        return has_empty_indicator and not has_stake_input

    def get_inline_error(self) -> Optional[str]:
        """Return inline error text if present."""
        if self.is_visible(self.LOC_INLINE_ERROR, timeout=2):
            return self.get_text(self.LOC_INLINE_ERROR)
        return None
