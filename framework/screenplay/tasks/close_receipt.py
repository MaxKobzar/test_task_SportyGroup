"""
Screenplay Task: CloseReceiptModal.
"""

from framework.screenplay.abilities.browse_the_web import BrowseTheWeb


class CloseReceiptModal:
    """Task to dismiss the bet receipt modal if visible."""

    def __init__(self, timeout: int = 5):
        self.timeout = timeout

    @classmethod
    def if_displayed(cls, timeout: int = 5) -> "CloseReceiptModal":
        return cls(timeout=timeout)

    def perform_as(self, actor) -> None:
        browser = actor.ability_to(BrowseTheWeb)
        page = browser.on_betting_page()
        if page.is_receipt_displayed(timeout=self.timeout):
            page.close_receipt()
