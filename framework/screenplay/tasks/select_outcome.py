"""
Screenplay Task: SelectMatchOutcome.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from framework.screenplay.abilities.browse_the_web import BrowseTheWeb


class SelectMatchOutcome:
    """Task to select an outcome (HOME/DRAW/AWAY) on the match with the given catalog ID."""

    def __init__(self, match_id: str, outcome: str):
        self.match_id = match_id
        self.outcome = outcome

    @classmethod
    def on(cls, match_id: str, outcome: str) -> "SelectMatchOutcome":
        return cls(match_id=match_id, outcome=outcome)

    def perform_as(self, actor) -> None:
        browser = actor.ability_to(BrowseTheWeb)
        page = browser.on_betting_page()
        page.click((By.ID, f"odds-{self.match_id}-{self.outcome.lower()}"))
        page.wait.until(EC.visibility_of_element_located(page.LOC_STAKE_INPUT))
