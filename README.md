# Sporty Group QA Test Automation Framework

A production-ready, hybrid UI and API test automation framework built with **Python 3**, **Selenium WebDriver**, **Pytest**, **Requests**, **uv**, and **Allure Reporting**.

---

## 🏗 Architecture Overview

The framework is architected using industry best practices and clean engineering principles, combining both the **Page Object Model (POM)** and the **Screenplay Pattern** alongside a **Page Factory (Factory Method)**, a hierarchical **`conftest.py` fixture lifecycle**, dynamic CLI input via **`pytest_addoption`**, and an automated **`pytest_runtest_makereport` failure triage hook**.

```
sporty_group/
├── .github/workflows/ci.yml           # CI: pre-commit (lint, types) then API & UI tests
├── .pre-commit-config.yaml            # Ruff, mypy, collection check, guardrails
├── .env.example                       # Template for the local .env (never commit .env)
├── pyproject.toml                     # PEP 621 dependencies, dev tools, ruff & mypy config
├── uv.lock                            # Locked dependencies (cross-platform)
├── .python-version                    # Python version pinned for uv
├── pytest.ini                         # Pytest options, strict markers, logging format, markers
├── README.md                          # Framework documentation
├── conftest.py                        # Root: pytest_addoption, settings/api_client fixtures, triage hook
├── framework/                         # Every package exposes its public API in __init__.py (__all__)
│   ├── config/
│   │   └── settings.py                # Settings: strongly-typed config built from CLI options (.env defaults)
│   ├── core/
│   │   └── webdriver_factory.py       # WebDriverFactory: configured Chrome WebDriver
│   ├── api/
│   │   ├── client.py                  # BaseClient, BettingApiClient (session, timeouts, Allure telemetry)
│   │   ├── exceptions.py              # Typed exceptions per HTTP status, parse_model / parse_json_model
│   │   └── models/
│   │       ├── betting.py             # Pydantic V2 domain models: Match, Odds, Balance, PlaceBet* (Decimal money)
│   │       └── errors.py              # Error body models per documented status (Error400 … Error500)
│   ├── pages/                         # Page Object Model (POM)
│   │   ├── base_page.py               # BasePage: explicit waits, locators, safe actions
│   │   ├── betting_page.py            # BettingPage: dashboard, bet slip and receipt modal
│   │   └── page_factory.py            # PageFactory: Factory Method for Page Objects
│   ├── data/
│   │   ├── bet_mother.py              # BetMother: valid and illegal-stake PlaceBetRequest data
│   │   └── money.py                   # Decimal money: rounding, EUR formatting, the only UI number parsing
│   └── screenplay/                    # Screenplay Pattern (one class per module, file named after it)
│       ├── actor.py                   # Actor and the Task / Question protocols
│       ├── abilities/
│       │   ├── browse_the_web.py      # BrowseTheWeb (wraps WebDriver & PageFactory)
│       │   └── call_api.py            # CallAPI (wraps BettingApiClient)
│       ├── tasks/                     # Composable business actions
│       │   ├── navigate_to_app.py     # NavigateToApp
│       │   ├── select_match_outcome.py # SelectMatchOutcome (by catalog match id)
│       │   ├── enter_stake_amount.py  # EnterStakeAmount
│       │   ├── submit_bet_placement.py # SubmitBetPlacement
│       │   ├── close_receipt_modal.py # CloseReceiptModal
│       │   ├── refresh_page.py        # RefreshPage
│       │   ├── place_bet_via_api.py   # PlaceBetViaApi
│       │   └── reset_balance_via_api.py # ResetBalanceViaApi
│       └── questions/                 # State inquiry objects
│           ├── displayed_balance.py   # DisplayedBalance
│           ├── potential_payout.py    # PotentialPayout
│           ├── is_place_bet_enabled.py # IsPlaceBetEnabled
│           ├── inline_error_message.py # InlineErrorMessage
│           ├── is_bet_slip_empty.py   # IsBetSlipEmpty
│           ├── bet_slip_selection.py  # BetSlipSelection
│           ├── is_receipt_modal_displayed.py # IsReceiptModalDisplayed
│           ├── is_receipt_modal_closed.py # IsReceiptModalClosed
│           ├── receipt_details.py     # ReceiptDetails
│           ├── api_balance.py         # ApiBalance
│           └── api_matches_feed.py    # ApiMatchesFeed
├── docs/                              # QA docs: test plan, strategy, bug reports, evidence screenshots
└── tests/
    ├── conftest.py                    # Shared fixtures: reset_balance_precondition, target_match
    ├── ui/
    │   ├── conftest.py                # UI fixtures (driver, bettor_actor Screenplay Actor)
    │   └── test_critical_user_journey.py # TC-BET-001: single-bet journey and receipt (E2E)
    └── api/
        ├── conftest.py                # API fixtures (api_actor, drained_balance)
        └── test_bet_placement.py      # TC-BET-002 / TC-BET-003 S3,S9: rejected stake leaves balance unchanged
```

---

## 🧩 Architectural Highlights & Design Patterns

### 1. Page Object Model (POM) & Page Factory (Factory Method)
- **`BasePage`** encapsulates explicit wait strategies (`WebDriverWait`), locator abstractions, element interactions, and resilience mechanisms.
- **`BettingPage`** encapsulates the dashboard, match cards, odds buttons, bet slip inputs, and modal dialogs.
- **`PageFactory`** implements the **Factory Method** design pattern (`PageFactory.get_page(PageType.BETTING, driver, timeout)`), decoupling test logic from concrete page construction.
- **Locator policy**: stable element ids first; where the app has no id, class selectors are scoped under the nearest id.
- **Waits**: explicit waits only (implicit wait is 0), all driven by `--timeout`. Only `TimeoutException` becomes a boolean answer; any other WebDriver error propagates.

### 2. Screenplay Pattern
- **Actor-centric architecture**: Tests read as user-centric narratives:
  ```python
  bettor_actor.attempts_to(
      NavigateToApp.at(BettingPage),
      SelectMatchOutcome.on(target_match.id, SelectionType.HOME),
      EnterStakeAmount.of(Decimal("10.00")),
      SubmitBetPlacement.now(),
      CloseReceiptModal.if_displayed(),
      RefreshPage.now(),
  )
  balance = bettor_actor.asks_for(DisplayedBalance.value())
  ```
- **Abilities**: `BrowseTheWeb` (driver, app URL and timeout from `Settings`) and `CallAPI` bridge the Actor to the browser and REST endpoints.
- **Tasks & Questions**: Decouple intent ("what the user does") from technical implementation. They are typed through the `Task` / `Question[T]` protocols and never touch locators.
- **Imports**: tests import from package level (`from framework.screenplay.tasks import NavigateToApp`); modules inside `framework/` import concrete modules so the packages can never import each other in a cycle.

### Money and API contracts
- Money is `Decimal` end to end: responses are parsed with `parse_float=Decimal`, expected values round half-up to cents (`framework/data/money.py`).
- Response models encode the contract and the domain rules (balance ≥ 0, stake €1.00–€100.00 with cent precision, odds > 1, payout > 0). A 2xx response that breaks them raises `ApiContractViolationError` naming the field, the received value and the rule; the raw body is in the Allure HTTP step.
- Every HTTP call has a timeout; non-2xx responses raise the typed exception for the status code, carrying the parsed error body (never a made-up one).

### 3. Hierarchical `conftest.py` Layout
- **Root `conftest.py`**: Handles CLI inputs, global session fixtures (`settings`, `api_client`), and the failure triage hook.
- **`tests/conftest.py`**: Shared test suite fixtures (`reset_balance_precondition` state isolation, `target_match` from the live catalog).
- **`tests/ui/conftest.py`**: Manages browser lifecycle (`driver`) and UI Screenplay Actor (`bettor_actor`).
- **`tests/api/conftest.py`**: Provides REST API Screenplay Actor (`api_actor`) and the `drained_balance` precondition (balance below the maximum stake).

### 4. CLI Point of Input (`pytest_addoption`)
Every flag defaults from the matching `.env` / environment variable; the CLI always wins.
- `--base-url` (`BASE_URL`): Target application URL (default: `https://qae-assignment-tau.vercel.app`).
- `--user-id` (`USER_ID`): Candidate user id sent as `x-user-id`. **Required**, no default.
- `--browser` (`BROWSER`): Browser selection (default: `chrome`).
- `--headless` (`HEADLESS`): `true` / `false` (default: `false` locally, `true` when `CI` is set).
- `--browser-width` / `--browser-height`: Window resolution (default: `1440x900`).
- `--timeout` (`TIMEOUT`): Explicit wait and HTTP timeout in seconds (default: `10`).

### 5. Failure Triage Hook (`pytest_runtest_makereport`)
When a test fails in setup or in its body (including expected failures), the hook attaches diagnostic artifacts to Allure:
1. **Browser Screenshot** (PNG) captured directly from the active WebDriver session.
2. **Page Source** (HTML) of the exact DOM state at failure time.
3. **Execution Traceback Log** containing the failure traceback.

---

## 🧰 Tooling Choices

Each tool was picked for one job and earns its place by removing a class of failure.

| Tool | Role | Why this one | Instead of |
|---|---|---|---|
| **uv** | Python install, dependency resolution, lock file, virtualenv | One fast binary replaces pyenv + pip + Poetry; `uv.lock` is cross-platform, so CI and every laptop resolve the exact same versions; `uv run` syncs the env before each command, so a stale venv can't cause a false failure. | Poetry (slower resolver, separate Python management) |
| **pytest** | Test runner and fixture system | Fixture hierarchy (`conftest.py` per layer) drives the preconditions; `pytest_addoption` and `pytest_runtest_makereport` give the CLI input and failure triage; parametrize + strict `xfail` keep known bugs visible. | unittest (no fixture scopes, class boilerplate) |
| **Selenium WebDriver** | Browser automation | Required stack. Selenium Manager resolves the matching chromedriver automatically, so there is no driver binary to maintain. | — |
| **requests** | HTTP client | Required stack. A `Session` gives connection reuse, default headers and a response hook that logs every call to Allure. | — |
| **Pydantic v2** | API contract models | Validates every response against the OpenAPI schema and the business rules (stake limits, balance ≥ 0) in one place; `Decimal` money end to end; a broken contract fails with the field, value and rule. | Hand-written dict assertions |
| **assertpy** | Assertions | Readable fluent checks with `described_as(...)` messages, and `soft_assertions()` to report every receipt defect from one UI run instead of stopping at the first. | Bare `assert` (one failure per run, no context) |
| **Allure** | Reporting | Step tree mirrors the Screenplay narrative (Actor → Task/Question → HTTP call); failures carry the screenshot, page source and traceback; epics/features/severity map to the test plan. | pytest-html (flat, no steps or attachments per step) |
| **python-dotenv** | Local configuration | `.env` supplies defaults for the CLI options only, so secrets like `USER_ID` stay out of git and the CLI always wins. | Hardcoded config module |
| **Ruff** | Linting + formatting | One fast tool replaces flake8, isort, pyupgrade and black; rule set includes pytest-style, bugbear and blind-except checks. | flake8 + isort + black |
| **mypy** | Static typing | `disallow_untyped_defs` on `framework/` keeps the library contract explicit (generic `Question[T]`, typed page factory). | — |
| **pre-commit** | Local quality gate | Runs ruff, mypy, a pytest collection check and repo guardrails (no `except Exception`, no `.env`) before code leaves the laptop; CI runs the same hooks, so local and CI never disagree. | CI-only checks (slower feedback) |
| **GitHub Actions** | CI | Lives next to the code; `concurrency` serializes runs because every run mutates the same remote test user's balance. | — |

---

## 🚀 Getting Started

### Prerequisites
- [uv](https://docs.astral.sh/uv/) (`brew install uv`); it installs the pinned Python 3.10 automatically
- Google Chrome (desktop)
- Allure CLI (optional, for viewing HTML report: `brew install allure`)

### 1. Installation via uv
```bash
uv sync                        # creates the project-local .venv (runtime + dev tools)
cp .env.example .env           # then set USER_ID
uv run pre-commit install      # optional: hooks on every commit
```

### 2. Running Tests

#### Run All Tests (UI + API)
```bash
uv run pytest tests/
```

#### Run Only API Tests
```bash
uv run pytest tests/api/
```

#### Run Only UI Tests (TC-BET-001 critical user journey)
```bash
uv run pytest tests/ui/
```

#### Run a Single Test Plan Case
Parametrized case IDs start with the test plan reference, so `-k` selects them:
```bash
uv run pytest tests/api/ -k "TC-BET-003"     # rows S3 and S9 only
```

#### Known Bugs (strict xfail)
Cases blocked by a confirmed defect are marked `xfail` (strict globally via `xfail_strict = true`) with the bug ID and the exact
failure type the bug produces (`raises=`), so an unrelated error still fails the run (see `docs/bug-reports.md`).
A normal run shows them as `XFAIL`; once the bug is fixed the case turns `XPASS` and fails the run,
so the marker must be removed. To see the real assertion failures:
```bash
uv run pytest tests/ --runxfail
```

#### Run in Headed Browser (Visible UI)
```bash
uv run pytest tests/ui/ --headless false
```

#### Run with Custom Base URL or User ID
```bash
uv run pytest --base-url "https://qae-assignment-tau.vercel.app" --user-id "<candidate-user-id>"
```

### Continuous Integration
`.github/workflows/ci.yml` runs the pre-commit hooks, then the full suite headless. Set the repository secret `USER_ID`.
Runs are serialized (`concurrency`) because every run mutates the balance of the same remote test user.

Each run publishes two artifacts (kept 14 days), built even when tests fail:
- **`allure-report`**: a single-file Allure HTML report; download, unzip and open `index.html` (no Allure CLI needed).
- **`test-results`**: `junit.xml` and the raw `allure-results/`, for local `allure serve` or other tooling.

Tool versions are pinned in the workflow `env` (`UV_VERSION`, `ALLURE_VERSION`); keep your local uv on the same version (`uv self update`).

### 3. Generating & Viewing Allure Report
```bash
# Each run writes to reports/allure-results (anchored to the project root, cleared per run)
# Generate the HTML report and open it in the browser
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report

# Or build and open in one step
allure serve reports/allure-results
```
