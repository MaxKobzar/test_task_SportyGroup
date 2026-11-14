"""
Screenplay Task: PlaceBet.
Handles entering stake and clicking place bet.
"""
from framework.screenplay.abilities.browse_the_web import BrowseTheWeb


class EnterStakeAmount:
    """Task to input stake into the bet slip."""

    def __init__(self, amount: float | str):
        self.amount = amount

    @classmethod
    def of(cls, amount: float | str) -> "EnterStakeAmount":
        return cls(amount=amount)

    def perform_as(self, actor) -> None:
        browser = actor.ability_to(BrowseTheWeb)
        page = browser.on_betting_page()
        page.enter_stake(self.amount)


class SubmitBetPlacement:
    """Task to click Place Bet button."""

    @classmethod
    def now(cls) -> "SubmitBetPlacement":
        return cls()

    def perform_as(self, actor) -> None:
        browser = actor.ability_to(BrowseTheWeb)
        page = browser.on_betting_page()
        page.click_place_bet()
