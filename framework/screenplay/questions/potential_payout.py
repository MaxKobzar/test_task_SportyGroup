"""
Screenplay Question: PotentialPayout.
"""

from framework.screenplay.abilities.browse_the_web import BrowseTheWeb


class PotentialPayout:
    """Question inspecting the potential payout text/value in the bet slip."""

    @classmethod
    def value(cls) -> "PotentialPayout":
        return cls()

    def answered_by(self, actor) -> float:
        browser = actor.ability_to(BrowseTheWeb)
        page = browser.on_betting_page()
        return page.get_potential_payout_value()

    @classmethod
    def text(cls) -> "PotentialPayoutText":
        return PotentialPayoutText()


class PotentialPayoutText:
    def answered_by(self, actor) -> str:
        browser = actor.ability_to(BrowseTheWeb)
        page = browser.on_betting_page()
        return page.get_potential_payout_text()
