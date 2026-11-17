"""
Screenplay Question: IsReceiptModalClosed.
"""

from framework.screenplay.abilities.browse_the_web import BrowseTheWeb
from framework.screenplay.actor import Actor


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
