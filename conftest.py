"""
Root pytest configuration and fixture orchestration.
Provides CLI parameter registration (pytest_addoption),
.env configuration integration, failure triage artifact collection
(pytest_runtest_makereport), and core session fixtures.
"""

import os
from dataclasses import dataclass

import allure
import pytest
from dotenv import load_dotenv
from selenium.common.exceptions import WebDriverException

from framework.api.client import BettingApiClient
from framework.core.logger import DATE_FORMAT, LOG_FORMAT, get_logger

# Load environment configuration from .env file
load_dotenv()

logger = get_logger()


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """
    Single point of logger configuration for all test runs (CLI, PyCharm, CI).

    Ensures consistent log formatting starting with: timestamp, filename, log level, log message,
    even when pytest is executed from sub-directories or through IDE test runners.
    """
    config.option.log_cli = True
    config.option.log_cli_level = "INFO"
    config.option.log_cli_format = LOG_FORMAT
    config.option.log_cli_date_format = DATE_FORMAT
    config.option.log_format = LOG_FORMAT
    config.option.log_date_format = DATE_FORMAT


def pytest_addoption(parser):
    """Register custom command-line options with fallback defaults from .env."""
    group = parser.getgroup("sporty-framework", "Sporty Betting Test Automation Options")
    group.addoption(
        "--base-url",
        action="store",
        default=os.getenv("BASE_URL", "https://qae-assignment-tau.vercel.app"),
        help="Base URL of the target betting application (default from .env: BASE_URL)",
    )
    group.addoption(
        "--user-id",
        action="store",
        default=os.getenv("USER_ID", "candidate-Mc2IYbjdqhj8"),
        help="Unique test candidate user identifier (default from .env: USER_ID)",
    )
    group.addoption(
        "--browser",
        action="store",
        default=os.getenv("BROWSER", "chrome"),
        help="Browser to run tests with (default from .env: BROWSER)",
    )
    default_headless = os.getenv("HEADLESS", "false")
    if os.environ.get("CI"):
        default_headless = "true"
    group.addoption(
        "--headless",
        action="store",
        default=default_headless,
        help="Run browser in headless mode ('true' or 'false', default from .env: HEADLESS)",
    )
    group.addoption(
        "--browser-width",
        action="store",
        default=int(os.getenv("BROWSER_WIDTH", "1440")),
        type=int,
        help="Browser viewport width in pixels (default from .env: BROWSER_WIDTH)",
    )
    group.addoption(
        "--browser-height",
        action="store",
        default=int(os.getenv("BROWSER_HEIGHT", "900")),
        type=int,
        help="Browser viewport height in pixels (default from .env: BROWSER_HEIGHT)",
    )
    group.addoption(
        "--timeout",
        action="store",
        default=int(os.getenv("TIMEOUT", "10")),
        type=int,
        help="Default timeout in seconds (default from .env: TIMEOUT)",
    )


@dataclass(frozen=True)
class TestConfig:
    """Test runtime configuration derived from .env file and pytest_addoption CLI arguments."""

    base_url: str
    user_id: str
    browser: str
    headless: bool
    browser_width: int
    browser_height: int
    timeout: int

    @property
    def target_url(self) -> str:
        """Constructs target application URL including user-id parameter."""
        sep = "&" if "?" in self.base_url else "?"
        return f"{self.base_url}{sep}user-id={self.user_id}"


@pytest.fixture(scope="session")
def test_config(request) -> TestConfig:
    """Construct TestConfig from parsed pytest_addoption CLI options and .env."""
    headless_raw = request.config.getoption("--headless")
    headless_bool = (
        headless_raw.lower() in ("true", "1", "yes")
        if isinstance(headless_raw, str)
        else bool(headless_raw)
    )
    base_url = request.config.getoption("--base-url")
    user_id = request.config.getoption("--user-id")
    os.environ["BASE_URL"] = base_url
    os.environ["USER_ID"] = user_id

    return TestConfig(
        base_url=base_url,
        user_id=user_id,
        browser=request.config.getoption("--browser"),
        headless=headless_bool,
        browser_width=request.config.getoption("--browser-width"),
        browser_height=request.config.getoption("--browser-height"),
        timeout=request.config.getoption("--timeout"),
    )


@pytest.fixture(scope="session")
def api_client(test_config: TestConfig) -> BettingApiClient:
    """Session-scoped REST API client configured via parsed options and .env."""
    return BettingApiClient(base_url=test_config.base_url, user_id=test_config.user_id)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to collect helpful triage information upon test failure:
    - Browser screenshot for failed UI tests
    - Page source HTML of the failed page
    - Execution log of the current test
    """
    outcome = yield
    report = outcome.get_result()

    is_failed = report.failed or (hasattr(report, "wasxfail") and report.skipped)
    if report.when == "call" and (report.failed or is_failed):
        logger.error(
            f"Test '{item.name}' failed or xfailed. Initiating triage artifact collection..."
        )

        # Locate WebDriver from funcargs (direct driver fixture or Screenplay Actor)
        driver = item.funcargs.get("driver", None)
        if not driver:
            actor = item.funcargs.get("bettor_actor", None)
            if actor:
                try:
                    from framework.screenplay.abilities.browse_the_web import BrowseTheWeb

                    driver = actor.ability_to(BrowseTheWeb).driver
                except (KeyError, AttributeError, ValueError):
                    pass

        # 1. Capture browser screenshot in case of failed UI test
        if driver:
            try:
                screenshot = driver.get_screenshot_as_png()
                allure.attach(
                    screenshot,
                    name=f"failure_screenshot_{item.name}",
                    attachment_type=allure.attachment_type.PNG,
                )
                logger.info(f"Attached failure screenshot for {item.name}")
            except (WebDriverException, OSError) as ex:
                logger.warning(f"Could not capture failure screenshot: {ex}")

            # 2. Capture page_source of the failed page
            try:
                source = driver.page_source
                allure.attach(
                    source,
                    name=f"failure_page_source_{item.name}",
                    attachment_type=allure.attachment_type.HTML,
                )
                logger.info(f"Attached failure page_source for {item.name}")
            except (WebDriverException, OSError) as ex:
                logger.warning(f"Could not capture page_source: {ex}")

        # 3. Log of execution of current test
        try:
            exec_log = (
                report.longreprtext if report.longreprtext else "No failure traceback recorded."
            )
            allure.attach(
                exec_log,
                name=f"execution_log_{item.name}",
                attachment_type=allure.attachment_type.TEXT,
            )
            logger.info(f"Attached execution log for {item.name}")
            # Application log also added here
        except (AttributeError, TypeError, OSError) as ex:
            logger.warning(f"Could not capture execution log: {ex}")
