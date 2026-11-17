"""
Screenplay Questions: IsReceiptModalDisplayed, IsReceiptModalClosed & ReceiptDetails.
"""

from framework.pages.betting_page import Receipt
from framework.screenplay.abilities.browse_the_web import BrowseTheWeb
from framework.screenplay.actor import Actor


class IsReceiptModalDisplayed:
    """Whether the receipt modal appears within the timeout (default: session timeout)."""

    def __init__(self, timeout: float | None = None):
        self.timeout = timeout

    @classmethod
    def check(cls, timeout: float | None = None) -> "IsReceiptModalDisplayed":
        return cls(timeout=timeout)

    def answered_by(self, actor: Actor) -> bool:
        page = actor.ability_to(BrowseTheWeb).on_betting_page()
        return page.is_receipt_displayed(timeout=self.timeout)


class IsReceiptModalClosed:
    """Whether the receipt modal is gone within the timeout (default: session timeout)."""

    def __init__(self, timeout: float | None = None):
        self.timeout = timeout

    @classmethod
    def check(cls, timeout: float | None = None) -> "IsReceiptModalClosed":
        return cls(timeout=timeout)

    def answered_by(self, actor: Actor) -> bool:
        page = actor.ability_to(BrowseTheWeb).on_betting_page()
        return page.is_receipt_closed(timeout=self.timeout)


class ReceiptDetails:
    """The fields shown on the confirmation receipt."""

    @classmethod
    def data(cls) -> "ReceiptDetails":
        return cls()

    def answered_by(self, actor: Actor) -> Receipt:
        return actor.ability_to(BrowseTheWeb).on_betting_page().get_receipt_details()
