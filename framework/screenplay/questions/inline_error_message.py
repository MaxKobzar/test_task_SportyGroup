"""
Screenplay Question: InlineErrorMessage.
"""

from framework.screenplay.abilities.browse_the_web import BrowseTheWeb
from framework.screenplay.actor import Actor


class InlineErrorMessage:
    """The inline bet slip error, or None when no error is shown."""

    @classmethod
    def text(cls) -> "InlineErrorMessage":
        return cls()

    def answered_by(self, actor: Actor) -> str | None:
        return actor.ability_to(BrowseTheWeb).on_betting_page().get_inline_error()
