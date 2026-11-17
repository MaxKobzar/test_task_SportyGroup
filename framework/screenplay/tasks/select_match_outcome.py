"""
Screenplay Task: SelectMatchOutcome.
"""

from framework.api.models.betting import SelectionType
from framework.screenplay.abilities.browse_the_web import BrowseTheWeb
from framework.screenplay.actor import Actor


class SelectMatchOutcome:
    """Task to add an outcome (HOME/DRAW/AWAY) of a catalog match to the bet slip."""

    def __init__(self, match_id: str, selection: SelectionType):
        self.match_id = match_id
        self.selection = selection

    @classmethod
    def on(cls, match_id: str, selection: SelectionType) -> "SelectMatchOutcome":
        return cls(match_id=match_id, selection=selection)

    def perform_as(self, actor: Actor) -> None:
        actor.ability_to(BrowseTheWeb).on_betting_page().select_outcome(
            self.match_id, self.selection
        )
