"""
Screenplay Question: ReceiptDetails.
"""

from framework.pages.betting_page import Receipt
from framework.screenplay.abilities.browse_the_web import BrowseTheWeb
from framework.screenplay.actor import Actor


class ReceiptDetails:
    """The fields shown on the confirmation receipt."""

    @classmethod
    def data(cls) -> "ReceiptDetails":
        return cls()

    def answered_by(self, actor: Actor) -> Receipt:
        return actor.ability_to(BrowseTheWeb).on_betting_page().get_receipt_details()
