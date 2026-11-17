# Strategy & Recommendations

- **Test Plan:** [test-plan-single-bet-placement.md](test-plan-single-bet-placement.md)
- **Defect Register:** [bug-reports.md](bug-reports.md)
- **Automated tests:** [`tests/ui/test_critical_user_journey.py`](../tests/ui/test_critical_user_journey.py), [`tests/api/test_bet_placement.py`](../tests/api/test_bet_placement.py)

---

## 1. Why These 2 Tests Were Automated

Candidates were ranked by **risk score × regression value ÷ automation cost**. The three risks that score 9 (RSK-01 ledger integrity, RSK-02 payout/receipt correctness, RSK-03 past-posting) each have confirmed Critical defects. The two automated tests together cover the first two, and each one runs at the cheapest layer that can still observe its risk.

| Test | Covers | Why it beat the other candidates |
| :--- | :--- | :--- |
| **E2E UI: `TC-BET-001` critical user journey**, parametrized over HOME / DRAW / AWAY | RSK-02; regressions for BUG-002, BUG-005, BUG-006, BUG-009 | It is the revenue path: if it breaks, nobody can place a bet. The receipt is the customer's contractual record, and the receipt defects (wrong payout, inverted teams, missing selection, stale balance) **only appear in the rendered UI**, so an API test can't see them. Every receipt value is compared with what the user saw before placing the bet (catalog odds, slip label, slip payout), not just checked for presence. |
| **API: rejected stake leaves the balance unchanged** (`TC-BET-002` overdraft + `TC-BET-003` S3 negative stake / S9 precision) | RSK-01; regressions for BUG-001, BUG-004 | Ledger integrity is the most expensive failure mode (insolvency, minting money), and **only the server can enforce it**: any client that skips the UI skips the UI's checks. A data-driven API test covers several business rules in seconds, with no browser flakiness. It asserts on the **stored balance**, not just the status code, so a "400 but debited anyway" regression is caught too. |

**Candidates considered and not chosen:**
- **`TC-BET-004` past-posting (RSK-03, score 9):** high risk, but at the API level it is one request plus a balance check, which is the same pattern as the chosen API test. The ledger test covers more rules for the same effort. It is the next test to automate (see §3).
- **`TC-BET-005` concurrency** and **`TC-BET-006` failure injection:** valuable, but expensive and timing-sensitive against a shared live user (see §2). They are not a good fit for a 2-test budget where reliability matters more than coverage.
- **Validation copy and boundary rows in the UI:** the same rules are checked more cheaply and reliably through the API. The UI only needs to prove the journey works.

**Design choices that keep both tests trustworthy:**
- **No hardcoded data.** `target_match` is resolved at runtime from `GET /api/matches` (kickoff after today plus a safety margin), so the tests don't break as the calendar moves on.
- **Known bugs are strict `xfail` with `raises=`.** A known defect shows up as `XFAIL`, an unrelated error still fails the run, and a fixed bug turns into `XPASS`, which tells you to remove the marker.
- **The stored balance is the source of truth** (`GET /api/balance`), never the reset response body (BUG-008).

---

## 2. Intentionally Left as Manual Only

| Area | Why manual |
| :--- | :--- |
| **Exploratory testing around the bet flow** | Exploration is a discovery activity, and it turned up defects outside the scripted scenarios (e.g. the catalog-filter bugs BUG-014 – BUG-016 and the OpenAPI drift in BUG-018). Once a finding is confirmed and high-risk, it becomes an automated regression row, not the other way round. |
| **`TC-BET-005` UI multi-click and API concurrency** | Verified by hand and working: 5 parallel bets gave 3×`200` + 2×`409` with an exact €30 debit. The outcome depends on timing, so a single pass proves little and a failure is hard to tell apart from network jitter. Against **one shared remote user** with no isolation, parallel bets also corrupt the balance for every other run. It needs an isolated environment and a carefully designed invariant check before it can run in CI. |
| **`TC-BET-006` error modal / Rebet / Close / X** | Verified by hand and working (copy and actions match Spec §2.5). Automating it needs failure injection (CDP `Fetch.fulfillRequest` returning `500`). That is Chrome-specific, brittle across browser versions, and checks a Medium-risk path. It is cheap to verify by hand with DevTools request blocking. |
| **Visual and copy review** (layout, receipt formatting, `PAST` / `TODAY` badges, filter empty states) | People judge these well and pixel-level assertions judge them badly. Automated visual diffs would mostly produce noise without a stable baseline. |
| **Spec ambiguities** (minimum stake €1.00 vs €1.01, bettability of `TODAY` matches, whether `PAST` matches are shown) | Automating an unresolved requirement just encodes a guess. These stay as manual checks and open questions until the Product Owner decides. |
| **Low-impact UI conveniences** (odds/date filters, `Remove All`, per-selection `x`) | They don't move money. The defects found there (BUG-014 – BUG-016) are Low severity and are tracked in the defect register. |

---

## 3. Top Recommendations for Scaling

### 1. Isolate test data so the suite can run in parallel and in CI without conflicts
Today every run changes the balance of **one shared remote user**, so CI runs are serialized (`concurrency: live-test-user`) and there is no `set-balance` endpoint, which forces workarounds like the `drained_balance` setup bet. To scale:
- Provision a **user per test or per worker** (a test-only `POST /api/test-users` or seeded pool), with a **set-balance** endpoint for precise preconditions (exact-balance, €0.00, below-minimum).
- Add a **controllable clock** or seeded match catalog, so `TODAY` / `PAST` / upcoming states are deterministic rather than inferred from the real date.
- Then enable `pytest-xdist` and remove the CI concurrency lock.

### 2. Shift coverage down the test pyramid and gate merges in CI/CD
- **API contract tests** generated from `/api/docs?format=json` (e.g. Schemathesis), so the spec/implementation drift seen in BUG-007, BUG-011 and BUG-018 is caught automatically instead of by exploration.
- **Backend unit and property-based tests** for the money rules (`stake × odds` rounding, min/max/precision, balance ≥ 0). One Hypothesis property such as *"payout == round(Decimal(stake) × Decimal(odds), 2)"* would have caught BUG-002 and BUG-010.
- **Expand the API layer next** with `TC-BET-004` (past-posting) and the full `TC-BET-003` matrix. Keep the UI layer to a few critical journeys.
- **Pipeline:** lint and type check plus the API suite on every PR (fast, blocking); the UI journeys on merge and nightly, with Allure history for flakiness trends. Run the critical journey as a **post-deploy smoke** on each environment.

### 3. Resolve spec gaps before they turn into bugs
Several findings come from an ambiguous or contradictory spec rather than from code alone. Agree on these with the Product Owner and record the answers as executable acceptance criteria:
- **Minimum stake:** €1.00 (§3, §4.4 copy) or €1.01 (Table 4.1)?
- **Kickoff time:** `kickoffDate` is date-only. Add a kickoff **timestamp** and define the bet-acceptance cutoff (is a `TODAY` match still pre-match?).
- **`PAST` matches:** hidden from the catalog, or shown but non-selectable?
- **Error contract:** define error codes for insufficient balance, `405`/`409`/`500`, and make the OpenAPI document match the server (BUG-018).
- **Rounding rule:** state explicitly that payout uses half-up rounding to the cent, using decimal (not float) arithmetic (BUG-010).

---

## 4. Author's Notes

### 1. Contract models encode the specification, not the current implementation
The Pydantic models in [`framework/api/models/`](../framework/api/models/) describe what the API **should** return according to the Feature Specification and the OpenAPI document. They were deliberately **not** relaxed to match how the API behaves today. For example:
- `balance` is `NonNegativeMoney` (≥ €0.00), so an overdraft accepted by the server (BUG-001) cannot be parsed into a valid `Balance` or `PlaceBetResponse`.
- `payout` is `PositiveMoney` (> €0.00) and `stake` is the shared `Stake` type (€1.00 – €100.00, cent precision), so a negative stake that the server accepts and credits (BUG-004) breaks the response contract.

When a response breaks these rules, the client raises **`ApiContractViolationError`**, naming the field, the value received and the rule it broke. The raw body is attached to the Allure HTTP step. This is intentional. Fitting the models to the observed behaviour would make the defects look like valid data and silently hide them in every test that reads those fields. With the models as they are, every test that touches an affected response fails loudly until the bug is fixed.

**Recommendation:** negative-input rules (negative, zero, over-maximum and over-precision stakes; stakes above the balance; malformed payloads) belong in **backend unit tests on the development side**, where they are fast, cheap and run on every commit (see §3.2). The API suite here keeps a thin, risk-driven regression layer over the most expensive of these rules (TC-BET-002, TC-BET-003 S3/S9). It does not try to repeat the whole validation matrix through the network.

### 2. Failure triage artifacts and how to extend them
The `pytest_runtest_makereport` hook in the root [`conftest.py`](../conftest.py) attaches triage evidence to the Allure report whenever a test fails during setup or in its body, including expected (`xfail`) failures:
- **Screenshot** (PNG) of the browser at the moment of failure (UI tests)
- **Page source** (HTML) of the DOM at that moment (UI tests)
- **Failure traceback** as a text attachment (all tests)

API tests also get every request/response pair as an Allure step from the client's session hook.

The hook is the single extension point for more evidence. The next most valuable additions:
- **Browser console log** (`goog:loggingPrefs` + `driver.get_log("browser")`): catches front-end JavaScript errors behind a broken render.
- **Network log / HAR** from the Chrome DevTools Protocol: shows which XHR failed or returned stale data (e.g. the header balance in BUG-005).
- **Video or step-by-step screenshots** for timing-sensitive UI failures.
- **Application logs and telemetry**: send a correlation ID (e.g. a W3C `traceparent` header) with every API call. On failure, the hook can then attach the matching backend logs or trace link from the observability stack, so a UI symptom can be followed to the server-side cause in one report.
