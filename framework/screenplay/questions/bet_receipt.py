"""
Screenplay Question: BetReceiptModal & ReceiptDetails.
"""

from typing import Dict

from framework.screenplay.abilities.browse_the_web import BrowseTheWeb


class IsReceiptModalDisplayed:
    """Question inspecting whether the receipt modal is displayed."""

    def __init__(self, timeout: int = 5):
        self.timeout = timeout

    @classmethod
    def check(cls, timeout: int = 5) -> "IsReceiptModalDisplayed":
        return cls(timeout=timeout)

    def answered_by(self, actor) -> bool:
        browser = actor.ability_to(BrowseTheWeb)
        page = browser.on_betting_page()
        return page.is_receipt_displayed(timeout=self.timeout)


class ReceiptDetails:
    """Question extracting the structured fields from the confirmation receipt."""

    def __init__(self, timeout: int = 5):
        self.timeout = timeout

    @classmethod
    def data(cls, timeout: int = 5) -> "ReceiptDetails":
        return cls(timeout=timeout)

    def answered_by(self, actor) -> Dict[str, str]:
        browser = actor.ability_to(BrowseTheWeb)
        page = browser.on_betting_page()
        return page.get_receipt_details(timeout=self.timeout)
