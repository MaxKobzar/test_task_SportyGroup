"""
Screenplay Task: CloseReceiptModal.
"""

from framework.screenplay.abilities.browse_the_web import BrowseTheWeb
from framework.screenplay.actor import Actor


class CloseReceiptModal:
    """Task to dismiss the bet receipt modal when it is shown."""

    def __init__(self, timeout: float | None = None):
        self.timeout = timeout

    @classmethod
    def if_displayed(cls, timeout: float | None = None) -> "CloseReceiptModal":
        return cls(timeout=timeout)

    def perform_as(self, actor: Actor) -> None:
        page = actor.ability_to(BrowseTheWeb).on_betting_page()
        if page.is_receipt_displayed(timeout=self.timeout):
            page.close_receipt()
