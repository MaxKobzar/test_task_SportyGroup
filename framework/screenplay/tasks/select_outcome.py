"""
Screenplay Tasks: SelectOutcome & SelectUpcomingMatchOutcome.
"""

from typing import Dict

from framework.screenplay.abilities.browse_the_web import BrowseTheWeb


class SelectOutcome:
    """Task to select a specific match outcome by index."""

    def __init__(self, outcome: str = "HOME", match_index: int = 0):
        self.outcome = outcome
        self.match_index = match_index

    @classmethod
    def on_match(cls, match_index: int = 0, outcome: str = "HOME") -> "SelectOutcome":
        return cls(outcome=outcome, match_index=match_index)

    def perform_as(self, actor) -> None:
        browser = actor.ability_to(BrowseTheWeb)
        page = browser.on_betting_page()
        page.select_outcome(outcome=self.outcome, match_index=self.match_index)


class SelectUpcomingMatchOutcome:
    """Task to locate an upcoming match and select the requested outcome."""

    def __init__(self, outcome: str = "HOME"):
        self.outcome = outcome
        self.selected_meta: Dict[str, str] = {}

    @classmethod
    def for_outcome(cls, outcome: str = "HOME") -> "SelectUpcomingMatchOutcome":
        return cls(outcome=outcome)

    def perform_as(self, actor) -> None:
        browser = actor.ability_to(BrowseTheWeb)
        page = browser.on_betting_page()
        self.selected_meta = page.select_upcoming_match_outcome(outcome=self.outcome)
