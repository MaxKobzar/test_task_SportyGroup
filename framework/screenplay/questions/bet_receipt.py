"""
Screenplay Question: BetReceiptModal & ReceiptDetails.
"""
from typing import Dict
from framework.screenplay.abilities.browse_the_web import BrowseTheWeb


class IsReceiptModalDisplayed:
    """Question inspecting whether the receipt modal is displayed."""

    @classmethod
    def check(cls, timeout: int = 5) -> "IsReceiptModalDisplayed":
        obj = cls()
        obj.timeout = timeout
        return obj

    def answered_by(self, actor) -> bool:
        browser = actor.ability_to(BrowseTheWeb)
        page = browser.on_betting_page()
        return page.is_receipt_displayed(timeout=getattr(self, "timeout", 5))


class ReceiptDetails:
    """Question extracting the structured fields from the confirmation receipt."""

    @classmethod
    def data(cls, timeout: int = 5) -> "ReceiptDetails":
        obj = cls()
        obj.timeout = timeout
        return obj

    def answered_by(self, actor) -> Dict[str, str]:
        browser = actor.ability_to(BrowseTheWeb)
        page = browser.on_betting_page()
        return page.get_receipt_details(timeout=getattr(self, "timeout", 5))
