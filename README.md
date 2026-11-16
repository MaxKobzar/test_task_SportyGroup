# Sporty Group QA Test Automation Framework

A production-ready, hybrid UI and API test automation framework built with **Python 3**, **Selenium WebDriver**, **Pytest**, **Requests**, **Poetry**, and **Allure Reporting**.

---

## 🏗 Architecture Overview

The framework is architected using industry best practices and clean engineering principles, combining both the **Page Object Model (POM)** and the **Screenplay Pattern** alongside a **Page Factory (Factory Method)**, a hierarchical **`conftest.py` fixture lifecycle**, dynamic CLI input via **`pytest_addoption`**, and an automated **`pytest_runtest_makereport` failure triage hook**.

```
sporty_group/
├── pyproject.toml                     # Poetry configuration & dependency specification
├── poetry.lock                        # Locked dependencies
├── pytest.ini                         # Pytest default CLI options, logging & markers
├── README.md                          # Framework documentation
├── conftest.py                        # Root configuration: pytest_addoption & failure triage hook
├── framework/
│   ├── config/
│   │   └── settings.py                # Strongly-typed configuration parsed from CLI
│   ├── core/
│   │   ├── webdriver_factory.py       # Factory producing configured Chrome WebDriver
│   │   └── logger.py                  # Formatted execution logger
│   ├── api/
│   │   ├── client.py                  # REST API client (Requests session, balance, matches, bets)
│   │   └── models.py                  # Pydantic V2 models for API schema contracts
│   ├── pages/                         # Page Object Model (POM)
│   │   ├── base_page.py               # Base Page with explicit waits, locators, safe actions
│   │   ├── betting_page.py            # Betting Dashboard & Slip Page Object
│   │   └── page_factory.py            # Page Factory implementing Factory Method pattern
│   └── screenplay/                    # Screenplay Pattern
│       ├── actor.py                   # Screenplay Actor (named, can, attempts_to, asks_for)
│       ├── abilities/
│       │   ├── browse_the_web.py      # Ability: BrowseTheWeb (wraps WebDriver & PageFactory)
│       │   └── call_api.py            # Ability: CallAPI (wraps BettingApiClient)
│       ├── tasks/                     # Composable business actions
│       │   ├── navigate_to_app.py     # NavigateToApp
│       │   ├── select_outcome.py      # SelectOutcome
│       │   ├── place_bet.py           # EnterStakeAmount & SubmitBetPlacement
│       │   ├── close_receipt.py       # CloseReceiptModal
│       │   ├── refresh_page.py        # RefreshPage
│       │   └── reset_balance.py       # ResetBalanceViaApi
│       └── questions/                 # State inquiry objects
│           ├── current_balance.py     # DisplayedBalance
│           ├── potential_payout.py    # PotentialPayout
│           ├── error_message.py       # IsPlaceBetEnabled & InlineErrorMessage
│           └── bet_receipt.py         # IsReceiptModalDisplayed
└── tests/
    ├── conftest.py                    # Shared test suite fixtures (lifecycle logging, reset_balance_precondition)
    ├── ui/
    │   ├── conftest.py                # UI fixtures (driver, bettor_actor Screenplay Actor)
    │   └── test_critical_user_journey_e2e.py # Sole E2E UI critical user journey (Screenplay + BetMother)
    └── api/
        ├── conftest.py                # API fixtures (api_actor Screenplay Actor)
        └── test_bet_placement_api.py  # Sole REST API test suite (Screenplay + BetMother)
```

---

## 🧩 Architectural Highlights & Design Patterns

### 1. Page Object Model (POM) & Page Factory (Factory Method)
- **`BasePage`** encapsulates explicit wait strategies (`WebDriverWait`), locator abstractions, element interactions, and resilience mechanisms.
- **`BettingPage`** encapsulates the dashboard, match cards, odds buttons, bet slip inputs, and modal dialogs.
- **`PageFactory`** implements the **Factory Method** design pattern (`PageFactory.get_page(PageType.BETTING, driver)`), decoupling test logic from concrete page construction.

### 2. Screenplay Pattern
- **Actor-centric architecture**: Tests read as user-centric narratives:
  ```python
  bettor_actor.attempts_to(
      NavigateToApp.at(settings.target_url),
      SelectOutcome.on_match(match_index=0, outcome="HOME"),
      EnterStakeAmount.of(10.00),
      SubmitBetPlacement.now(),
      CloseReceiptModal.if_displayed(),
      RefreshPage.now(),
  )
  balance = bettor_actor.asks_for(DisplayedBalance.value())
  ```
- **Abilities**: `BrowseTheWeb` and `CallAPI` bridge the Actor to the browser and REST endpoints.
- **Tasks & Questions**: Decouple intent ("what the user does") from technical implementation.

### 3. Hierarchical `conftest.py` Layout
- **Root `conftest.py`**: Handles CLI inputs, global session fixtures (`test_config`, `api_client`), and the failure triage hook.
- **`tests/conftest.py`**: Shared test suite fixtures (`log_test_lifecycle`, `reset_balance_precondition` state isolation).
- **`tests/ui/conftest.py`**: Manages browser lifecycle (`driver`) and UI Screenplay Actor (`bettor_actor`).
- **`tests/api/conftest.py`**: Provides REST API Screenplay Actor (`api_actor`).

### 4. CLI Point of Input (`pytest_addoption`)
Configurable flags supported:
- `--base-url`: Target application URL (default: `https://qae-assignment-tau.vercel.app`).
- `--user-id`: Candidate test ID (default: `candidate-Mc2IYbjdqhj8`).
- `--browser`: Browser selection (default: `chrome`).
- `--headless`: Headless mode toggle (`true` / `false`, default: `true`).
- `--browser-width` / `--browser-height`: Window resolution (default: `1440x900`).

### 5. Failure Triage Hook (`pytest_runtest_makereport`)
When any test fails, the hook automatically extracts and attaches diagnostic artifacts into Allure:
1. **Browser Screenshot** (PNG) captured directly from the active WebDriver session.
2. **Page Source** (HTML) of the exact DOM state at failure time.
3. **Execution Traceback Log** containing test output and error logs.
   *(Includes the integration hook line: `# Application log also added here`)*.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Poetry 2.0+
- Google Chrome (desktop)
- Allure CLI (optional, for viewing HTML report: `brew install allure`)

### 1. Installation via Poetry
```bash
poetry install
```

### 2. Running Tests

#### Run All Tests (UI + API)
```bash
poetry run pytest tests/
```

#### Run Only API Tests
```bash
poetry run pytest tests/api/
```

#### Run Only UI Tests (Page Object Model)
```bash
poetry run pytest tests/ui/test_pom_bet_placement.py
```

#### Run High-Value E2E Critical User Journey Tests
```bash
# POM implementation
poetry run pytest tests/ui/test_critical_user_journey_e2e.py

# Screenplay implementation
poetry run pytest tests/ui/test_screenplay_critical_user_journey.py
```

#### Run Only UI Tests (Screenplay Pattern)
```bash
poetry run pytest tests/ui/test_screenplay_bet_placement.py
```

#### Run in Headed Browser (Visible UI)
```bash
poetry run pytest tests/ui/ --headless false
```

#### Run with Custom Base URL or User ID
```bash
poetry run pytest --base-url "https://qae-assignment-tau.vercel.app" --user-id "candidate-Mc2IYbjdqhj8"
```

### 3. Generating & Viewing Allure Report
```bash
# Generate report from collected test artifacts
allure generate allure-results -o allure-report --clean

# Open report in browser
allure open allure-report
```
