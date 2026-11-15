"""
Base Page Object Model class.
Provides reusable methods, explicit waits, and resilient element interactions.
"""

from typing import List, Optional, Tuple

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from framework.core.logger import get_logger

logger = get_logger()


class BasePage:
    """Base Page Object containing common browser interactions and explicit waits."""

    def __init__(self, driver: webdriver.Remote, timeout: int = 10):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)

    def open(self, url: str) -> None:
        """Navigate to the specified URL."""
        logger.info(f"Navigating to {url}")
        self.driver.get(url)

    def refresh(self) -> None:
        """Refresh current page."""
        logger.info("Refreshing page...")
        self.driver.refresh()

    def find_element(self, locator: Tuple[By, str], timeout: Optional[int] = None) -> WebElement:
        """Wait for element to be present and visible in DOM."""
        wait = self.wait if timeout is None else WebDriverWait(self.driver, timeout)
        return wait.until(EC.visibility_of_element_located(locator))

    def find_present_element(
        self, locator: Tuple[By, str], timeout: Optional[int] = None
    ) -> WebElement:
        """Wait for element to exist in DOM, even if not yet visible."""
        wait = self.wait if timeout is None else WebDriverWait(self.driver, timeout)
        return wait.until(EC.presence_of_element_located(locator))

    def find_elements(
        self, locator: Tuple[By, str], timeout: Optional[int] = None
    ) -> List[WebElement]:
        """Wait for at least one element matching locator to be present."""
        wait = self.wait if timeout is None else WebDriverWait(self.driver, timeout)
        try:
            wait.until(EC.presence_of_element_located(locator))
            return self.driver.find_elements(*locator)
        except (TimeoutException, NoSuchElementException, WebDriverException):
            return []

    def click(self, locator: Tuple[By, str], timeout: Optional[int] = None) -> None:
        """Wait for element to be clickable and click it."""
        wait = self.wait if timeout is None else WebDriverWait(self.driver, timeout)
        element = wait.until(EC.element_to_be_clickable(locator))
        logger.info(f"Clicking element: {locator}")
        element.click()

    def type_text(
        self,
        locator: Tuple[By, str],
        text: str,
        clear: bool = True,
        timeout: Optional[int] = None,
    ) -> None:
        """Type text into element, optionally clearing it first."""
        element = self.find_element(locator, timeout=timeout)
        if clear:
            element.clear()
        logger.info(f"Typing '{text}' into element: {locator}")
        element.send_keys(text)

    def get_text(self, locator: Tuple[By, str], timeout: Optional[int] = None) -> str:
        """Get visible inner text of element."""
        element = self.find_element(locator, timeout=timeout)
        return element.text.strip()

    def is_visible(self, locator: Tuple[By, str], timeout: int = 3) -> bool:
        """Check whether element is visible within the given timeout."""
        try:
            WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(locator))
            return True
        except (TimeoutException, NoSuchElementException, WebDriverException):
            return False

    def wait_for_invisibility(self, locator: Tuple[By, str], timeout: int = 5) -> bool:
        """Wait until element becomes invisible or absent."""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(locator)
            )
        except (TimeoutException, NoSuchElementException, WebDriverException):
            return False
