"""
Base Page Object Model class.
Owns explicit waits; every wait uses the configured timeout unless a call overrides it.
Only TimeoutException is translated into a boolean answer: any other WebDriver error
(dead session, stale element, invalid selector) propagates so it is never mistaken for
"element not visible".
"""

import logging
from typing import TypeAlias

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)

Locator: TypeAlias = tuple[str, str]


class BasePage:
    """Common browser interactions built on explicit waits."""

    def __init__(self, driver: WebDriver, timeout: float):
        self.driver = driver
        self.timeout = timeout

    def _wait(self, timeout: float | None = None) -> WebDriverWait[WebDriver]:
        return WebDriverWait(self.driver, self.timeout if timeout is None else timeout)

    def open(self, url: str) -> None:
        """Navigate to the URL."""
        logger.info("Navigating to %s", url)
        self.driver.get(url)

    def refresh(self) -> None:
        """Reload the current page."""
        logger.info("Refreshing page")
        self.driver.refresh()

    def wait_until_loaded(self) -> None:
        """Block until the page is ready for interaction. Pages override this."""

    def find_element(self, locator: Locator, timeout: float | None = None) -> WebElement:
        """Wait for the element to be visible and return it."""
        return self._wait(timeout).until(EC.visibility_of_element_located(locator))

    def click(self, locator: Locator, timeout: float | None = None) -> None:
        """Wait for the element to be clickable and click it."""
        element = self._wait(timeout).until(EC.element_to_be_clickable(locator))
        logger.info("Clicking %s", locator)
        element.click()

    def type_text(self, locator: Locator, text: str, timeout: float | None = None) -> None:
        """Replace the element's value with text."""
        element = self.find_element(locator, timeout)
        element.clear()
        logger.info("Typing %r into %s", text, locator)
        element.send_keys(text)

    def get_text(self, locator: Locator, timeout: float | None = None) -> str:
        """Visible text of the element, stripped."""
        return self.find_element(locator, timeout).text.strip()

    def is_visible(self, locator: Locator, timeout: float | None = None) -> bool:
        """True if the element becomes visible within the timeout."""
        try:
            self._wait(timeout).until(EC.visibility_of_element_located(locator))
        except TimeoutException:
            return False
        return True

    def is_invisible(self, locator: Locator, timeout: float | None = None) -> bool:
        """True if the element is hidden or absent within the timeout."""
        try:
            self._wait(timeout).until(EC.invisibility_of_element_located(locator))
        except TimeoutException:
            return False
        return True
