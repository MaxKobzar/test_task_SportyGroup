# Test Plan: Single Bet Placement

**Application Under Test (AUT):** [Sports Betting QA Application](https://qae-assignment-tau.vercel.app/?user-id=candidate-Mc2IYbjdqhj8)
**Specification Source:** [Feature_Specification.pdf](file:///Users/maksym_kobzar/PET/sporty_group/materials/Feature_Specification.pdf)
**Methodology:** Risk-Based Testing (RBT) & Strategic Clean Engineering
**Automation/Interaction Protocol:** Selenium MCP Server (`selenium-mcp-server` over stdio JSON-RPC) / Playwright

---

## 1. Executive Summary & Strategy

Rather than pursuing redundant, exhaustive permutations across all 103 football matches and odds variations, this test plan employs **Risk-Based Testing (RBT)**. We concentrate validation on catastrophic failure modes:
1. **Financial Solvency & Ledger Integrity**: Ensuring balance can never go negative and that double-spending or concurrency race conditions are thwarted.
2. **Regulatory & Calculation Correctness**: Ensuring payout calculations strictly adhere to agreed odds without rounding or calculation bugs, and receipts accurately represent the contractual agreement.
3. **Temporal Match Integrity**: Preventing "past-posting" (wagering on already completed or started events).
4. **Input Boundaries & Data Validation**: Enforcing minimum/maximum stake limits and decimal formatting at both client and server layers.

### Scope Boundaries & Deferred Features (Phase 2)
To maximize testing depth on core financial and regulatory transaction paths, the following items from [Feature_Specification.pdf](file:///Users/maksym_kobzar/PET/sporty_group/materials/Feature_Specification.pdf) are intentionally classified as secondary and deferred to Phase 2:
* **Match Catalog Filters (Spec Section 2.6)**: Date filter (single day / date range) and Odds range filter (min/max range validation) are non-transactional navigation aids and will be validated in a dedicated discovery test suite.
* **Bet Slip Batch Clearing (Spec Section 2.2)**: `Remove All` and per-selection delete `( x )` buttons are low-risk UI convenience features covered under general slip component unit/regression tests.

### Specification Inconsistency Note (Minimum Stake)
In [Feature_Specification.pdf](file:///Users/maksym_kobzar/PET/sporty_group/materials/Feature_Specification.pdf), Table 4.1 specifies `"Minimum €1.01 (positive values)"`, whereas Section 3 specifies `"Stake min (per bet) €1.00"` and Section 4.4 specifies user-facing error copy `"Minimum stake is €1.00"`. In this test plan, **`€1.00` is adopted as the authoritative minimum stake boundary** to align with business logic and UI copy specifications.

### Key Empirical Findings Discovered via Automated Reconnaissance
During automated reconnaissance using the Selenium MCP Server against the live application, the following high-risk discrepancies were identified and factored into this plan:
* **Critical Financial Flaw (API Layer)**: While the UI disables the `Place Bet` button when the stake exceeds the balance, direct execution against `POST /api/place-bet` accepts stakes larger than available balance, creating an illegal **negative user balance** (e.g., balance `-30.00`).
* **Critical Calculation Defect (UI Receipt)**: In the success receipt modal, potential payout is hardcoded to `stake * 2` in the client script (`R * 2`), ignoring the actual match odds (e.g., stake €5.00 on odds 1.85 yields €10.00 instead of €9.25).
* **Display Defect (Team Inversion)**: The receipt displays team labels inverted as `${awayTeam} vs ${homeTeam}` (e.g., "PSG vs Marseille" instead of "Marseille vs PSG").
* **Temporal Exploit**: The UI and API accept wagers on matches explicitly marked as `PAST` (events from early 2026), violating the pre-match betting domain requirement.

---

## 2. Risk Assessment Matrix

| Risk ID | Risk Category | Failure Mode / Threat | Impact | Likelihood | Risk Level | Selected Scenario |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RSK-01** | **Financial Integrity** | Uncollateralized betting / negative balance via API bypass or client desync. | Catastrophic (Direct capital loss) | High | **CRITICAL** | `TC-BET-002` |
| **RSK-02** | **Contractual / Payout** | Incorrect payout calculation on receipt or inverted match participants. | High (Regulatory fines & disputes) | High (Observed bug) | **CRITICAL** | `TC-BET-001` |
| **RSK-03** | **Temporal Integrity** | Wagering on past or in-progress matches (past-posting arbitrage exploit). | Critical (Guaranteed player winnings) | High (Observed bug) | **CRITICAL** | `TC-BET-004` |
| **RSK-04** | **Concurrency** | Rapid double-click on `Place Bet` causing duplicate debits / race conditions. | High (Customer panic & reconciliation failure) | Medium | **HIGH** | `TC-BET-005` |
| **RSK-05** | **Boundary Enforcement** | Fractional penny truncation or sub-minimum / super-maximum stake acceptance. | Medium (Ledger rounding errors, compliance) | Medium | **HIGH** | `TC-BET-003` |
| **RSK-06** | **Fault Tolerance** | System hangs in loading state or drops bet on transient 500 error; broken Rebet. | Medium (UX drop-off & customer friction) | Medium | **MEDIUM** | `TC-BET-006` |

---

## 3. Prioritized Test Scenarios

### Scenario 1: Core Single Bet Placement & Contractual Receipt Verification (Critical User Journey)
* **ID:** `TC-BET-001`
* **Title:** Successful Single Bet Placement on an Upcoming Match with Balance Deduction & Receipt Verification
* **Priority:** Critical
* **Scope / Designation:** Primary End-to-End Critical User Journey (Automated in `tests/ui/test_critical_user_journey_e2e.py`)
* **Risk Rationale:** Core happy path. This is the primary revenue transaction of the product. If odds, stake, deducted balance, and potential payout fail to align accurately on both the client slip and the resulting legal receipt, the product faces immediate player disputes and regulatory compliance penalties.
* **Preconditions:**
  * User balance is known (e.g., reset to initial €125.50 via `POST /api/reset-balance`).
  * At least one valid upcoming match exists in the catalog (e.g., `Marseille vs PSG`, Kickoff date: 2026-11-17, Odds: 1=4.10, X=3.70, 2=1.85).
* **Steps:**
  1. Open application at `https://qae-assignment-tau.vercel.app/?user-id=candidate-Mc2IYbjdqhj8`.
  2. Verify initial header balance displays `€125.50`.
  3. Scroll to upcoming match `Marseille vs PSG` and click odds button `2` (Away, odds 1.85).
  4. Verify the Bet Slip populates with:
     * Match title: `Marseille vs PSG`
     * Selection: `Match Winner: Away`
     * Odds: `1.85`
     * `Total Stake`: `€0.00`
     * `Potential Payout`: `€0.00`
     * `Place Bet` button is disabled.
  5. In input `#bet-slip-stake-input`, enter `10.00`.
  6. Verify the slip dynamically calculates:
     * `Total Stake`: `€10.00`
     * `Potential Payout`: `€18.50` (`10.00 * 1.85`)
     * `Place Bet` button becomes enabled.
  7. Click `Place Bet` (`#bet-slip-place-bet`).
  8. Verify the button immediately enters loading state (`Placing...`) and is disabled.
  9. Wait for the transaction to resolve and the Success Receipt Modal to appear.
  10. Validate the receipt modal fields:
      * Bet ID: Present in format `#B-XXXXX`
      * Match: Must preserve `Home vs Away` ordering (`Marseille vs PSG`)
      * Stake: `€10.00`
      * Odds: `1.85`
      * Potential Payout: Mathematically exact `€18.50` (verifying against hardcoded multipliers)
      * Timestamp: Valid current placement time label
  11. Click the `Close` button on the modal.
  12. Verify the modal closes, the active selection is cleared from the Bet Slip, and the header balance is updated to `€115.50`.
* **Expected Result:**
  * Bet transitions through `Placing...` to successful placement.
  * Available balance is debited by exactly €10.00.
  * Success receipt matches all placement parameters and displays exact payout calculation `€18.50`.
  * Bet slip resets cleanly without lingering selections.

---

### Scenario 2: Overdraft Prevention & Multi-Layer Balance Enforcement
* **ID:** `TC-BET-002`
* **Title:** Prevent Wager Placement When Stake Exceeds Available Account Balance (Client & Server Parity)
* **Priority:** Critical
* **Risk Rationale:** Protects the platform from financial insolvency. If client-side checks can be bypassed or if the backend API fails to reject an overdraft, a bettor can wager uncollateralized funds, creating negative balances and irrecoverable operator debt.
* **Preconditions:**
  * User balance is set to a known amount (e.g., reduced to €25.50 by prior wagers or test setup).
* **Steps:**
  1. Navigate to the application with current balance of `€25.50`.
  2. Select an outcome on any upcoming match (e.g., `Bayern Munich vs Leverkusen`).
  3. In `#bet-slip-stake-input`, enter a stake amount strictly greater than the balance but within maximum stake limit (e.g., `50.00`).
  4. Observe the Bet Slip validation state.
  5. Verify the inline error message displays: `Insufficient balance`.
  6. Verify the `Place Bet` button is disabled (`disabled="true"`).
  7. **API Defense-in-Depth Verification**: Execute an HTTP `POST` directly to `/api/place-bet` with headers `x-user-id: candidate-Mc2IYbjdqhj8` and payload:
     ```json
     {
       "matchId": "bundesliga-bayern-leverkusen-2026-11-13",
       "selection": "HOME",
       "stake": 50.00
     }
     ```
  8. Inspect the HTTP status code and response body.
  9. Query `GET /api/balance` to verify current balance.
* **Expected Result:**
  * **UI**: Shows error `Insufficient balance` and locks the `Place Bet` button.
  * **API**: Strictly rejects the request with HTTP `422 Unprocessable Entity` (error: `insufficient_balance`).
  * **Ledger**: User balance remains strictly unchanged at `€25.50`; negative balance (e.g., `-24.50`) is strictly prevented.

---

### Scenario 3: Stake Boundary Value Analysis & Decimal Precision Validation
* **ID:** `TC-BET-003`
* **Title:** Boundary Condition Validation for Minimum (€1.00), Maximum (€100.00), and Decimal Formats
* **Priority:** High
* **Risk Rationale:** Boundary values frequently reveal off-by-one errors in validation logic. Sub-minimum stakes allow micro-transaction spamming, exceeding maximum stakes bypasses responsible gaming limits, and accepting fractional cents (>2 decimals) causes rounding discrepancies in multi-currency betting books.
* **Preconditions:**
  * Available balance is at least €100.00 (e.g., reset to €125.50).
  * An active match selection is present in the Bet Slip.
* **Steps:**
  1. Add an upcoming match selection to the Bet Slip.
  2. **Test Sub-Minimum Boundary (€0.99):**
     * Enter `0.99` in `#bet-slip-stake-input`.
     * Verify error message `Minimum stake is €1.00` appears.
     * Verify `Place Bet` button is disabled.
  3. **Test Minimum Valid Boundary (€1.00):**
     * Clear and enter `1.00`.
     * Verify error message clears and `Place Bet` button is enabled.
  4. **Test Maximum Valid Boundary (€100.00):**
     * Clear and enter `100.00`.
     * Verify `Place Bet` button remains enabled and potential payout reflects €100.00 * odds.
  5. **Test Super-Maximum Boundary (€100.01):**
     * Clear and enter `100.01`.
     * Verify error message `Maximum stake is €100.00` appears.
     * Verify `Place Bet` button is disabled.
  6. **Test Sub-Cent Precision Boundary (3+ Decimal Places):**
     * Attempt to type `10.555`.
     * Verify the input mask/validator rejects the third decimal place, maintaining `10.55`.
     * Attempt to send `{"stake": 10.555}` directly via `POST /api/place-bet`.
* **Expected Result:**
  * Only values in the closed interval `[1.00, 100.00]` with at most 2 decimal places are accepted.
  * Exact error messages match specifications: `Minimum stake is €1.00` and `Maximum stake is €100.00`.
  * Sub-cent precision payloads return HTTP `422` with `invalid_stake_precision`.

---

### Scenario 4: Temporal Event Integrity (Rejection of Wagers on Past Matches)
* **ID:** `TC-BET-004`
* **Title:** Pre-Match Event Integrity: Enforce Rejection of Wagers on Finished or Past Events
* **Priority:** Critical
* **Risk Rationale:** In pre-match sports betting, accepting wagers on past or started matches allows players to bet on known outcomes ("past-posting"), guaranteeing 100% win rate for the bettor and catastrophic financial drain for the sportsbook.
* **Preconditions:**
  * The match catalog returns matches with kickoff dates prior to current date/time (labeled `PAST` in the feed, e.g., `Manchester Utd vs Chelsea`, Kickoff: 2026-02-27).
* **Steps:**
  1. Open the application and view the match catalog.
  2. Locate a match card with the `PAST` status badge.
  3. Inspect the three odds buttons (`1`, `X`, `2`) on the card.
  4. Attempt to click an odds button on the `PAST` match.
  5. If the selection is added to the Bet Slip, input a valid stake (`10.00`) and click `Place Bet`.
  6. In parallel, submit a direct API request to `POST /api/place-bet` targeting the past match ID:
     ```json
     {
       "matchId": "premier-league-manutd-chelsea",
       "selection": "HOME",
       "stake": 10.00
     }
     ```
  7. Verify application response and balance behavior.
* **Expected Result:**
  * Odds buttons for `PAST` matches must be disabled/non-interactive in the UI.
  * If a past match ID reaches `/api/place-bet`, the API must reject the placement with HTTP `422 Unprocessable Entity` (error: `event_already_started` or `invalid_event_status`).
  * No stake is deducted and no bet receipt is issued for past events.

---

### Scenario 5: Concurrency, Idempotency & In-Progress State Lock
* **ID:** `TC-BET-005`
* **Title:** Prevent Duplicate Bet Placement via Rapid Multi-Click and Concurrent In-Flight Requests
* **Priority:** High
* **Risk Rationale:** Network latency often tempts users to click `Place Bet` multiple times. Without atomic locking or idempotency keys, duplicate wagers are created, deducting multiple stakes for a single user action and corrupting session state.
* **Preconditions:**
  * User balance is sufficient for multiple bets (e.g., €125.50).
  * An upcoming match selection is populated in the Bet Slip with a valid stake (€10.00).
* **Steps:**
  1. Populate the Bet Slip with an upcoming match and stake `€10.00`.
  2. Trigger rapid, successive clicks on the `Place Bet` button (`#bet-slip-place-bet`) within <100ms.
  3. Verify that on the very first click:
     * The button immediately changes label to `Placing...`.
     * The button attribute `disabled="true"` is applied immediately, suppressing all subsequent clicks.
  4. Simultaneously, issue two concurrent HTTP `POST` requests to `/api/place-bet` using the same `x-user-id` and payload:
     ```bash
     curl -X POST /api/place-bet -d '{"matchId":"ligue-1-marseille-psg-2026-11-17","selection":"HOME","stake":10}' &
     curl -X POST /api/place-bet -d '{"matchId":"ligue-1-marseille-psg-2026-11-17","selection":"HOME","stake":10}' &
     ```
  5. Inspect the HTTP responses from both concurrent requests.
  6. Verify the final account balance and total bets placed.
* **Expected Result:**
  * The UI strictly ignores duplicate clicks while in `Placing...` state.
  * The backend returns HTTP `200 OK` for the first request and HTTP `409 Conflict` (error: `bet_in_progress` or `duplicate_request`) for the overlapping request.
  * Exactly **one** bet is recorded; balance is debited by exactly €10.00 (not €20.00).

---

### Scenario 6: System Resilience & Error Recovery Flow (Rebet vs Close)
* **ID:** `TC-BET-006`
* **Title:** Resilient Error Recovery on Server Failure (500 / Network Error) with Rebet and Close Actions
* **Priority:** Medium
* **Risk Rationale:** Distributed backend services inevitably encounter intermittent timeouts, database deadlocks, or HTTP 500 errors. The client must not freeze in `Placing...`, must not deduct the stake, and must allow the user to either retry (`Rebet`) or abort (`Close`) without corrupting state.
* **Preconditions:**
  * Active selection in Bet Slip with stake `€10.00`.
  * Mock or route failure simulated for `POST /api/place-bet` (e.g., invalid payload or simulated 500 error).
* **Steps:**
  1. Populate the Bet Slip with selection and stake `€10.00`.
  2. Trigger bet placement when the backend produces an error (HTTP 500 or network disconnect).
  3. Verify the loading state clears and the Error Modal appears:
     * Modal Title: `Something went wrong`
     * Modal Body: Explains the bet could not be processed and suggests trying again.
     * Actions Present: `Rebet` (primary button), `Close` (secondary button), and top-right `X`.
  4. Verify the available balance is **not** deducted.
  5. **Test Rebet Action**:
     * Restore service connectivity.
     * Click `Rebet`.
     * Verify the modal closes and the placement request is immediately re-sent.
     * Verify successful placement resolves to the Success Receipt Modal.
  6. **Test Close / X Action**:
     * Trigger the error modal again.
     * Click `Close` (or top-right `X`).
     * Verify the error modal closes.
     * Verify the Bet Slip clears the current selection and stake back to empty state.
* **Expected Result:**
  * Failed bets never deduct user balance.
  * Error modal complies with UX requirements (`Something went wrong`, `Rebet`, `Close`).
  * `Rebet` successfully retries the transaction; `Close` and `X` dismiss the modal and reset the bet slip.

---
