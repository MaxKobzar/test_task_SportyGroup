"""
Screenplay Task: CloseReceiptModal.
"""
from framework.screenplay.abilities.browse_the_web import BrowseTheWeb


class CloseReceiptModal:
    """Task to dismiss the bet receipt modal if visible."""

    @classmethod
    def if_displayed(cls, timeout: int = 5) -> "CloseReceiptModal":
        obj = cls()
        obj.timeout = timeout
        return obj

    def perform_as(self, actor) -> None:
        browser = actor.ability_to(BrowseTheWeb)
        page = browser.on_betting_page()
        if page.is_receipt_displayed(timeout=getattr(self, "timeout", 5)):
            page.close_receipt()
