"""
Screenplay Task: RefreshPage.
"""

from framework.screenplay.abilities.browse_the_web import BrowseTheWeb
from framework.screenplay.actor import Actor


class RefreshPage:
    """Task to reload the betting page and wait until it is ready."""

    @classmethod
    def now(cls) -> "RefreshPage":
        return cls()

    def perform_as(self, actor: Actor) -> None:
        page = actor.ability_to(BrowseTheWeb).on_betting_page()
        page.refresh()
        page.wait_until_loaded()
