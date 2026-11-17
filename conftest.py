"""
Root pytest configuration and fixture orchestration.
Provides CLI parameter registration (pytest_addoption) with .env defaults,
the session Settings and API client fixtures, and failure triage artifact
collection (pytest_runtest_makereport).
"""

import logging
import os
from collections.abc import Generator

import allure
import pytest
from dotenv import load_dotenv
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webdriver import WebDriver

from framework.api.client import BettingApiClient
from framework.config.settings import Settings

# .env only supplies defaults for the CLI options below; it is never read anywhere else.
load_dotenv()

logger = logging.getLogger(__name__)

# Fixtures the triage hook inspects for a live browser session.
DRIVER_FIXTURE = "driver"


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """
    Anchor --alluredir to the project root: a relative path would otherwise resolve against
    the working directory, so IDE runs from tests/api or tests/ui scatter results there.
    Runs before allure-pytest's own pytest_configure (tryfirst), which opens the directory.
    """
    alluredir = config.getoption("allure_report_dir", None)
    if alluredir and not os.path.isabs(alluredir):
        config.option.allure_report_dir = str(config.rootpath / alluredir)


def _str_to_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in ("true", "1", "yes"):
        return True
    if normalized in ("false", "0", "no"):
        return False
    raise ValueError(f"Expected a boolean ('true'/'false'), got {value!r}")


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register custom command-line options with defaults from the environment / .env."""
    group = parser.getgroup("sporty-framework", "Sporty Betting Test Automation Options")
    group.addoption(
        "--base-url",
        default=os.getenv("BASE_URL", "https://qae-assignment-tau.vercel.app"),
        help="Base URL of the target betting application (env: BASE_URL)",
    )
    group.addoption(
        "--user-id",
        default=os.getenv("USER_ID"),
        help="Candidate user identifier sent as x-user-id (env: USER_ID, required)",
    )
    group.addoption(
        "--browser",
        default=os.getenv("BROWSER", "chrome"),
        help="Browser to run tests with (env: BROWSER)",
    )
    group.addoption(
        "--headless",
        type=_str_to_bool,
        default=_str_to_bool(os.getenv("HEADLESS", "true" if os.getenv("CI") else "false")),
        help="Run browser headless: 'true' or 'false' (env: HEADLESS; forced true when CI is set)",
    )
    group.addoption(
        "--browser-width",
        type=int,
        default=int(os.getenv("BROWSER_WIDTH", "1440")),
        help="Browser window width in pixels (env: BROWSER_WIDTH)",
    )
    group.addoption(
        "--browser-height",
        type=int,
        default=int(os.getenv("BROWSER_HEIGHT", "900")),
        help="Browser window height in pixels (env: BROWSER_HEIGHT)",
    )
    group.addoption(
        "--timeout",
        type=int,
        default=int(os.getenv("TIMEOUT", "10")),
        help="Explicit wait and HTTP timeout in seconds (env: TIMEOUT)",
    )


@pytest.fixture(scope="session")
def settings(request: pytest.FixtureRequest) -> Settings:
    """Session configuration built from the parsed CLI options."""
    config = request.config
    user_id = config.getoption("--user-id")
    if not user_id:
        raise pytest.UsageError("No user id configured: pass --user-id or set USER_ID in .env")
    return Settings(
        base_url=config.getoption("--base-url").rstrip("/"),
        user_id=user_id,
        browser=config.getoption("--browser"),
        headless=config.getoption("--headless"),
        browser_width=config.getoption("--browser-width"),
        browser_height=config.getoption("--browser-height"),
        timeout=config.getoption("--timeout"),
    )


@pytest.fixture(scope="session")
def api_client(settings: Settings) -> Generator[BettingApiClient, None, None]:
    """Session-scoped REST API client; the HTTP session is closed at teardown."""
    client = BettingApiClient(
        base_url=settings.base_url, user_id=settings.user_id, timeout=settings.timeout
    )
    yield client
    client.close()


def _attach_browser_state(driver: WebDriver, name: str) -> None:
    try:
        allure.attach(
            driver.get_screenshot_as_png(),
            name=f"failure_screenshot_{name}",
            attachment_type=allure.attachment_type.PNG,
        )
        allure.attach(
            driver.page_source,
            name=f"failure_page_source_{name}",
            attachment_type=allure.attachment_type.HTML,
        )
    except WebDriverException as ex:
        logger.warning("Could not capture browser state: %s", ex)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, pytest.TestReport, None]:
    """
    Attach triage artifacts to Allure when setup or the test body fails (including xfail):
    browser screenshot, page source, and the failure traceback.
    """
    outcome = yield
    report: pytest.TestReport = outcome.get_result()

    failed = report.failed or (report.skipped and hasattr(report, "wasxfail"))
    if report.when not in ("setup", "call") or not failed:
        return

    logger.error("%s failed during %s; collecting triage artifacts", item.name, report.when)
    driver = getattr(item, "funcargs", {}).get(DRIVER_FIXTURE)
    if isinstance(driver, WebDriver):
        _attach_browser_state(driver, item.name)

    allure.attach(
        report.longreprtext or "No failure traceback recorded.",
        name=f"execution_log_{item.name}",
        attachment_type=allure.attachment_type.TEXT,
    )
