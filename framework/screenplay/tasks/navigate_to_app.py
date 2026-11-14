"""
Screenplay Task: NavigateToApp.
Navigates the Actor to a target Page Object Model (POM) page.
"""
from typing import Optional, Type, Union
from framework.pages.base_page import BasePage
from framework.pages.betting_page import BettingPage
from framework.screenplay.abilities.browse_the_web import BrowseTheWeb


class NavigateToApp:
    """Task to navigate the Actor to a specific Page Object Model (POM) page."""

    def __init__(
        self,
        page_target: Union[Type[BasePage], str] = BettingPage,
        url: Optional[str] = None,
    ):
        self.page_target = page_target
        self.url = url

    @classmethod
    def at(
        cls,
        page_target: Union[Type[BasePage], str] = BettingPage,
        url: Optional[str] = None,
    ) -> "NavigateToApp":
        """
        Factory method to initiate navigation.
        Accepts a Page Object Model class (e.g. BettingPage) or direct URL string.
        """
        # Backwards compatibility: if a URL string is passed as first argument
        if isinstance(page_target, str) and (page_target.startswith("http://") or page_target.startswith("https://")):
            return cls(page_target=BettingPage, url=page_target)
        return cls(page_target=page_target, url=url)

    def perform_as(self, actor) -> None:
        browser = actor.ability_to(BrowseTheWeb)

        # Delegate page resolution via PageFactory through BrowseTheWeb
        if isinstance(self.page_target, type) and issubclass(self.page_target, BasePage):
            page = browser.on(self.page_target)
        else:
            page = browser.on_betting_page()

        # Resolve destination URL (explicit url, page get_url(), or default config)
        target_url = self.url
        if not target_url:
            if hasattr(page, "get_url"):
                target_url = page.get_url()
            elif hasattr(self.page_target, "get_url"):
                target_url = self.page_target.get_url()
            else:
                import os
                base = os.getenv("BASE_URL", "https://qae-assignment-tau.vercel.app")
                uid = os.getenv("USER_ID", "candidate-Mc2IYbjdqhj8")
                sep = "&" if "?" in base else "?"
                target_url = f"{base}{sep}user-id={uid}"

        page.open(target_url)
        page.wait_until_loaded()
