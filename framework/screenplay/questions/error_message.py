"""
Screenplay Questions: IsPlaceBetEnabled & InlineErrorMessage.
"""

from framework.screenplay.abilities.browse_the_web import BrowseTheWeb
from framework.screenplay.actor import Actor


class IsPlaceBetEnabled:
    """Whether the Place Bet button is enabled."""

    @classmethod
    def check(cls) -> "IsPlaceBetEnabled":
        return cls()

    def answered_by(self, actor: Actor) -> bool:
        return actor.ability_to(BrowseTheWeb).on_betting_page().is_place_bet_enabled()


class InlineErrorMessage:
    """The inline bet slip error, or None when no error is shown."""

    @classmethod
    def text(cls) -> "InlineErrorMessage":
        return cls()

    def answered_by(self, actor: Actor) -> str | None:
        return actor.ability_to(BrowseTheWeb).on_betting_page().get_inline_error()
