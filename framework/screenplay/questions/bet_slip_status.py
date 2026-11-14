"""
Screenplay Question: IsBetSlipEmpty.
"""
from framework.screenplay.abilities.browse_the_web import BrowseTheWeb


class IsBetSlipEmpty:
    """Question inspecting whether the Bet Slip is currently empty."""

    @classmethod
    def check(cls) -> "IsBetSlipEmpty":
        return cls()

    def answered_by(self, actor) -> bool:
        browser = actor.ability_to(BrowseTheWeb)
        page = browser.on_betting_page()
        return page.is_bet_slip_empty()
