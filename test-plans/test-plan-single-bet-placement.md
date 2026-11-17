# Test Plan: Single Bet Placement

- **Application Under Test (AUT):** [Sports Betting QA Application](https://qae-assignment-tau.vercel.app/?user-id=candidate-Mc2IYbjdqhj8)
- **Specification Source:** [Feature_Specification.pdf](../materials/Feature_Specification.pdf)
- **Defect Register:** [BUG_REPORTS.md](BUG_REPORTS.md)
- **Methodology:** Risk-Based Testing (RBT)
- **Automation Stack:** Python / pytest / Selenium WebDriver (UI) + HTTP client (API)

---

## 1. Executive Summary & Strategy

Rather than pursuing exhaustive permutations across all 103 football matches and odds variations, this plan applies **Risk-Based Testing (RBT)** and concentrates on catastrophic failure modes:

1. **Financial Solvency & Ledger Integrity** — balance can never go negative; concurrent requests can never debit more than the bets actually accepted.
2. **Contractual / Calculation Correctness** — payout equals `stake × odds` rounded to 2 decimals; the receipt faithfully represents the placed bet.
3. **Temporal Match Integrity** — no wagers on events that are no longer upcoming ("past-posting").
4. **Input & Request Validation** — stake, selection, match ID, payload and user-context rules enforced at **both** UI and API layers.

### Test Data Strategy (Time-Independent)
The match catalog is static while the calendar is not: an "upcoming" match today becomes `TODAY` and then `PAST`. Scenarios therefore **never hardcode a match ID** for positive flows. Matches are resolved at runtime from `GET /api/matches`:

### Scope Boundaries & Deferred Features
* **Match Catalog Filters (Spec §2.6)** — date and odds-range filters are non-transactional navigation aids; deferred to a dedicated discovery suite.
* **Bet Slip Batch Clearing (Spec §2.2)** — `Remove All` and per-selection `( x )` are low-risk UI conveniences; covered by slip component regression tests.

### Specification Inconsistency (Minimum Stake)
Spec Table 4.1 states `Minimum €1.01 (positive values)`, while §3 states `Stake min (per bet) €1.00` and §4.4 specifies copy `Minimum stake is €1.00`. **€1.00 is adopted as the working minimum** (two of three sources agree, including user-facing copy). TC-BET-003 tests **0.99, 1.00 and 1.01** so the outcome is informative under either reading. If `1.00` is rejected, it is logged as a **spec conflict for Product Owner resolution**, not as a product defect.

### Open Questions for Product Owner
1. **Minimum stake:** €1.00 or €1.01?
2. **Same-day matches:** `kickoffDate` is date-only (`YYYY-MM-DD`) with no kickoff time. Is a match labeled `TODAY` still bettable (pre-match) or should it be treated as started?
3. **Past matches in catalog:** §2.1 says the list displays *upcoming* matches. Should `PAST` matches be hidden entirely, or displayed but non-selectable?

### Key Empirical Findings (Automated Reconnaissance)
Medium-or-higher defects found on the live application and the scenarios that cover them. Full details are in [BUG_REPORTS.md](BUG_REPORTS.md):

| Bug ID | Finding | Severity | Covered by |
| :--- | :--- | :--- | :--- |
| BUG-001 | `POST /api/place-bet` accepts stake > balance → negative balance (e.g. `-30.00`) | Critical | TC-BET-002 |
| BUG-002 | Receipt payout hardcoded to `stake * 2` (€5.00 @ 3.05 shows €10.00, not €15.25) | Critical | TC-BET-001 |
| BUG-003 | UI and API accept wagers on `PAST` matches | Critical | TC-BET-004 |
| BUG-004 | API accepts a negative stake and **credits** the balance (`-50` → +€50.00) | Critical | TC-BET-003 (row S3) |
| BUG-005 | Header/slip balance not refreshed after a bet; the stale balance allows overdraft through the UI alone | High | TC-BET-001 (step 14), TC-BET-002 |
| BUG-006 | Receipt shows `Away vs Home` (e.g. "Inter Miami vs LAFC") | Medium | TC-BET-001 |
| BUG-007 | `POST /api/place-bet` returns `currency: "USD"` instead of `"EUR"` | Medium | TC-BET-001 |
| BUG-008 | `reset-balance` response (€125.50) disagrees with persisted balance (€120.00) | Medium | Reset consistency guard (§1 Test Data Strategy) |
| BUG-009 | Success receipt omits the Selection field | Medium | TC-BET-001 (step 12) |
| BUG-010 | API payout truncated to the cent instead of rounded (€1.15 @ 2.20: slip €2.53, API `2.52`) | Medium | TC-BET-003 (row S11) |

> Low-severity defects are tracked only in [BUG_REPORTS.md](BUG_REPORTS.md) and do not drive risk scoring in this plan.

---

## 2. Risk Assessment Matrix

Scoring: **Probability (P)** and **Impact (I)** on a 1–3 scale; **Score = P × I**. Score 9 = Critical (P0), 6 = High (P1), 3–4 = Medium (P2), 1–2 = Low (P3). Probability is 3 where a defect has already been observed.

| Risk ID | Category | Failure Mode / Threat | P | I | Score | Level | Scenario |
| :--- | :--- | :--- | :-: | :-: | :-: | :--- | :--- |
| **RSK-01** | Financial Integrity | Uncollateralized betting, negative balance or balance minting (API bypass, stale UI balance, negative stake) | 3 (BUG-001/004/005) | 3 | **9** | **CRITICAL** | `TC-BET-002`, `TC-BET-003` (S3) |
| **RSK-02** | Contractual / Payout | Wrong payout, selection, or participants on receipt / API response | 3 (BUG-002/006/007/009/010) | 3 | **9** | **CRITICAL** | `TC-BET-001`, `TC-BET-003` (S7, S11) |
| **RSK-03** | Temporal Integrity | Wagering on past or started matches (past-posting) | 3 (BUG-003) | 3 | **9** | **CRITICAL** | `TC-BET-004` |
| **RSK-04** | Concurrency | Double-click / parallel requests debit more than accepted bets | 2 | 3 | **6** | **HIGH** | `TC-BET-005` |
| **RSK-05** | Input & Request Validation | Out-of-range / malformed stake, invalid selection or match, missing auth accepted | 2 | 3 | **6** | **HIGH** | `TC-BET-003` |
| **RSK-06** | Fault Tolerance | UI hangs in `Placing...`, deducts on failure, or broken Rebet/Close | 2 | 2 | **4** | **MEDIUM** | `TC-BET-006` |

---

## 3. Prioritized Test Scenarios

### Scenario 1: Core Single Bet Placement & Receipt Verification (Critical User Journey)
* **ID:** `TC-BET-001`
* **Title:** Successful Single Bet on an Upcoming Match with Balance Deduction, Receipt and API Contract Verification
* **Priority:** Critical
* **Scope / Designation:** Primary E2E critical user journey (automated in `tests/ui/test_critical_user_journey_e2e.py`)
* **Risk Rationale:** The primary revenue transaction. If odds, stake, deducted balance and payout do not align across the bet slip, the receipt (the customer's contractual record) and the ledger, the operator faces disputes and regulatory penalties. Receipt defects BUG-002, BUG-006 and BUG-009 and the stale-balance defect BUG-005 have already been observed, so this is also regression-critical.
* **Preconditions:**
  * Balance reset via `POST /api/reset-balance`; `initial_balance` read from `GET /api/balance` (persisted value; observed: €120.00). The reset response body is not used (BUG-008).
  * `target_match` resolved from `GET /api/matches` as the latest match with `kickoffDate > today`. Example: `LAFC vs Inter Miami` (`mls-lafc-inter-miami-2026-12-28`, kickoff 2026-12-28), odds 1=2.20, X=3.45, 2=3.05.
* **Steps:**
  1. Open the application at `https://qae-assignment-tau.vercel.app/?user-id=candidate-Mc2IYbjdqhj8`.
  2. Verify the header balance displays `initial_balance` (e.g. `€120.00`).
  3. On the `target_match` card, click odds button `1` (Home).
  4. Verify the Bet Slip shows `Match Winner: Home` with the Home odds.
  5. On the same card, click odds button `2` (Away).
  6. Verify the Bet Slip **replaces** the selection (Spec §2.1/§2.2), and shows exactly one selection:
     * Match title: `<homeTeam> vs <awayTeam>` (e.g. `LAFC vs Inter Miami`)
     * Selection: `Match Winner: Away`
     * Odds: `<odds.away>` (e.g. `3.05`)
     * Available balance: `initial_balance` (Spec §2.2)
     * `Total Stake`: `€0.00`, `Potential Payout`: `€0.00`
     * `Place Bet` is disabled.
  7. Enter `10.00` in `#bet-slip-stake-input`.
  8. Verify the slip recalculates:
     * `Total Stake`: `€10.00`
     * `Potential Payout`: `round(10.00 × odds.away, 2)` (e.g. `€30.50`)
     * `Place Bet` is enabled.
  9. Click `Place Bet` (`#bet-slip-place-bet`).
  10. Verify the button immediately shows `Placing...` and its `disabled` property is `true`.
  11. Wait for the Success Receipt Modal.
  12. Validate every receipt field required by Spec §2.4:
      * **Bet ID:** present and non-empty (observed format `#B-XXXXX`; the format is informational, not a spec requirement)
      * **Match:** `Home vs Away` order (e.g. `LAFC vs Inter Miami`) — regression for BUG-006
      * **Selection:** `Away` / `Match Winner: Away` — regression for BUG-009
      * **Stake:** `€10.00`
      * **Odds at placement:** equal to the slip odds (odds are static for the session, Spec §3)
      * **Potential payout:** `round(10.00 × odds.away, 2)` (e.g. `€30.50`) — regression for BUG-002
      * **Placement timestamp:** present and within the current minute
  13. Click `Close` on the modal.
  14. Verify the modal closes, the Bet Slip has no active selection, and the header balance shows `initial_balance − 10.00` (e.g. `€110.00`) **without a page reload** — regression for BUG-005.
  15. **Ledger parity:** call `GET /api/balance`; verify `balance == initial_balance − 10.00` and `currency == "EUR"`.
  16. **API contract parity** (direct `POST /api/place-bet` on `target_match`, `selection: "AWAY"`, `stake: 10.00`): verify the 200 response has `selection == "AWAY"`, `stake == 10`, `odds == odds.away`, `payout == round(10 × odds.away, 2)`, `balance == previous balance − 10`, and `currency == "EUR"` — regression for BUG-007.
* **Expected Result:**
  * The selection is replaced, not added; the slip holds exactly one selection.
  * The bet moves from `Placing...` to a single success outcome.
  * The balance is debited by exactly €10.00 in both the UI and `GET /api/balance`.
  * The receipt shows all 7 fields from Spec §2.4 with the correct values: `Home vs Away` order and payout = `stake × odds`.
  * The API response matches the spec contract, including `currency: "EUR"`.
  * After the receipt is closed, the user returns to the main flow with no active selection.

---

### Scenario 2: Overdraft Prevention & Multi-Layer Balance Enforcement
* **ID:** `TC-BET-002`
* **Title:** Reject Stakes Exceeding Available Balance at UI and API Layers (Including Exact-Balance Boundary)
* **Priority:** Critical
* **Risk Rationale:** Protects the platform from insolvency. If the backend relies on the client to block overdrafts, a user can wager funds they do not have, creating negative balances and unrecoverable debt. This has already been observed through the API (BUG-001) and through the UI alone because of a stale client balance (BUG-005). The exact-balance boundary catches off-by-one comparisons (`<` vs `<=`).
* **Preconditions (deterministic setup — no set-balance endpoint exists):**
  1. `POST /api/reset-balance`, then `GET /api/balance` → `initial_balance` (persisted value; observed €120.00; the reset response body is not used, BUG-008).
  2. `POST /api/place-bet` on `target_match` (`kickoffDate > today`) with `stake: 100.00`, then `GET /api/balance` → `B` (expected `initial_balance − 100.00`; observed **€20.00**).
  3. All steps below use `target_match`. **Do not use a past or same-day match:** a `422` must come only from the balance rule, not from the event-status rule.
* **Steps:**
  1. Open the application (fresh page load, after the API setup bet); verify the header and slip show balance `B` (e.g. `€20.00`).
  2. Select an outcome on `target_match`.
  3. **Over-balance (UI):** enter a stake greater than `B` but within the maximum, e.g. `50.00`.
     * Verify the inline error `Insufficient balance` appears.
     * Verify the `Place Bet` `disabled` property is `true`.
  4. **Balance + €0.01 (UI):** enter `B + 0.01` (e.g. `20.01`); verify the same error and disabled state.
  5. **API over-balance:** `POST /api/place-bet` with header `x-user-id: candidate-Mc2IYbjdqhj8` and body:
     ```json
     { "matchId": "<target_match.id>", "selection": "HOME", "stake": 50.00 }
     ```
     Capture the status code and response body.
  6. **API balance + €0.01:** repeat step 5 with `stake: B + 0.01`.
  7. `GET /api/balance` → verify the balance is still exactly `B`.
  8. **Exact-balance boundary (positive):** in the UI, enter a stake equal to `B` (e.g. `20.00`); verify there is no error and `Place Bet` is enabled. Place the bet.
  9. Verify the success receipt appears and `GET /api/balance` returns `0.00` (never negative).
* **Expected Result:**
  * **UI:** stakes `> B` show `Insufficient balance` and lock `Place Bet`. A stake of exactly `B` is accepted.
  * **API:** stakes `> B` are rejected with HTTP `422` (semantic validation failure, Spec §5.3). The error body is checked only against the schema in `/api/docs?format=json`; the spec defines no specific error code string.
  * **Ledger:** the balance stays at `B` after rejected attempts and goes to exactly `0.00` after the exact-balance bet. It is never negative.

---

### Scenario 3: Stake & Request Validation Matrix (Boundaries, Format, Protocol)
* **ID:** `TC-BET-003`
* **Title:** Boundary Value Analysis and Validation of Stake, Selection, Match ID, Payload and User Context at UI and API Layers
* **Priority:** High
* **Risk Rationale:** Validation edges are where off-by-one and type-coercion bugs live. Sub-minimum stakes enable micro-transaction abuse. Over-maximum stakes bypass exposure limits. Sub-cent precision causes ledger rounding drift. A negative stake that is accepted turns a bet into a balance credit (observed: BUG-004, Critical). If the API checks less than the UI, every UI rule can be bypassed with a direct request. Missing user context is an authorization weakness. One data-driven matrix covers Spec §4.1–§4.4 cheaply at the API level, while the UI rows cover the copy users see.
* **Preconditions:**
  * Balance reset (≥ €100.00 available).
  * `target_match` resolved (`kickoffDate > today`). For row S7, prefer an outcome where `100 × odds` is not exact in binary floating point (e.g. LAFC vs Inter Miami Home `2.20`: `100 × 2.2 = 220.00000000000003`). That catches a server that rounds *up* or drops precision, but not one that truncates: `220.00000000000003` truncates to the correct `220.00`.
  * For row S11, choose a stake and outcome whose exact decimal product has at most 2 decimals but whose floating-point product falls just **below** it (e.g. LAFC vs Inter Miami Home `2.20` with stake `1.15`: exact `2.53`, float `2.5299999999999998`). If `target_match` has different odds, pick the stake at runtime: the first stake in `1.01 … 10.00` where `Decimal(stake) × Decimal(odds)` has ≤ 2 decimals and `floor(stake × odds × 100) / 100` is lower than it. Every upcoming match in the current catalog has such a stake.
* **Steps:**
  1. Add a `target_match` selection to the Bet Slip.
  2. For each **UI stake row** below, clear `#bet-slip-stake-input`, type the input, and record: the displayed value, the inline message, and the `Place Bet` `disabled` property.
  3. For each **API row** below, send `POST /api/place-bet` (with a valid `x-user-id` unless stated otherwise) and record the status code and body.
  4. After all rows, `GET /api/balance` → verify it changed only by the stakes of rows expected to succeed.

  **A. Stake rows (UI + API — Spec §3, §4.1, §4.4)**

  | Row | Stake input | Expected UI | Expected API |
  | :--- | :--- | :--- | :--- |
  | S1 | *(empty)* / omitted field | `Place Bet` disabled | `422` (or `400` if the schema treats it as malformed) |
  | S2 | `abc` / `"10"` (string in JSON) | Input rejected / not accepted; `Place Bet` disabled | `422` / `400` |
  | S3 | `0`, `-5`, `-50` | Minimum message, or the `-` sign is stripped by the input; disabled | `422`; balance unchanged (never credited) — regression for BUG-004 |
  | S4 | `0.99` | `Minimum stake is €1.00`; disabled | `422` |
  | S5 | `1.00` | No error; enabled (**if rejected → raise spec conflict, see §1**) | `200` |
  | S6 | `1.01` | No error; enabled | `200` |
  | S7 | `100.00` | No error; enabled; payout = `round(100.00 × odds, 2)` (e.g. odds 2.20 → `€220.00`) | `200`; `payout == 220.00` exactly |
  | S8 | `100.01` | `Maximum stake is €100.00`; disabled | `422` |
  | S9 | `10.555` | Third decimal blocked by the input **or** placement blocked with a precision message. Either is acceptable per Spec §4.1/§4.4. The value is never silently rounded and submitted. | `422` |
  | S10 | `1,5` / `1.2.3` (single decimal separator rule) | Rejected; `Place Bet` disabled | n/a (UI format rule) |
  | S11 | `1.15` on odds `2.20` (or the runtime-chosen stake, see Preconditions) | No error; enabled; payout = exact `stake × odds` to the cent (e.g. `€2.53`) | `200`; `payout == 2.53` exactly, equal to the slip value — regression for BUG-010 (observed `2.52`) |

  **B. Request / protocol rows (API only — Spec §4.2, §4.3, §5.1)**

  | Row | Request variation | Expected API |
  | :--- | :--- | :--- |
  | R1 | `selection: "WIN"` (not in `HOME`/`DRAW`/`AWAY`) | `422` |
  | R2 | `selection` omitted | `422` (or `400`) |
  | R3 | `matchId: ""` / `"   "` / omitted | `422` |
  | R4 | `matchId: "unknown-match-id"` | `422` |
  | R5 | Body `{not json` / body `[1,2]` (non-object) | `400` |
  | R6 | Header `x-user-id` missing / empty | `401` |
  | R7 | `GET` / `PUT` on `/api/place-bet` | `405` |
  | R8 | Valid body plus an extra field `"foo": "bar"` | `200` (extra fields ignored, Spec §5.3) |

* **Expected Result:**
  * Only stakes in the closed interval `[1.00, 100.00]` with at most 2 decimal places are accepted, at **both** layers.
  * UI copy matches Spec §4.4 exactly: `Minimum stake is €1.00`, `Maximum stake is €100.00`.
  * Payout is exact to the cent at the maximum stake (S7) and for a product that floating point represents just below its exact value (S11). The API payout equals the Bet Slip's Potential Payout (no truncation).
  * Every invalid request is rejected with the status class defined in Spec §5.3 (`400`/`401`/`405`/`422`). Error bodies are checked only against the published OpenAPI schema.
  * No rejected row changes the balance.

---

### Scenario 4: Temporal Event Integrity (Rejection of Wagers on Past Matches)
* **ID:** `TC-BET-004`
* **Title:** Pre-Match Integrity: No Wagers Accepted on Past Events at UI or API Layer
* **Priority:** Critical
* **Risk Rationale:** The product is pre-match only (Spec §1, §3). Accepting bets on finished events lets players bet on known outcomes ("past-posting"): a guaranteed win for the player and a direct loss for the operator. This has already been observed (BUG-003).
* **Preconditions:**
  * `past_match` resolved from `GET /api/matches` as any match with `kickoffDate < today` (example: `mls-inter-miami-lafc-2026-06-20`, `Inter Miami vs LAFC`, kickoff 2026-06-20).
  * Balance reset; `balance_before` captured.
* **Steps:**
  1. Open the application and view the match catalog.
  2. Check whether `past_match` is displayed. Spec §2.1 says the list shows *upcoming* matches.
  3. If it is displayed (labeled `PAST`), inspect its `1` / `X` / `2` odds buttons.
  4. Try clicking an odds button on the `PAST` card.
  5. If a selection is added, enter stake `10.00` and click `Place Bet`.
  6. Independently, send `POST /api/place-bet`:
     ```json
     { "matchId": "<past_match.id>", "selection": "HOME", "stake": 10.00 }
     ```
  7. `GET /api/balance` → compare with `balance_before`.
* **Expected Result:**
  * **UI:** `past_match` is either not shown or shown with odds buttons that do not work (`disabled` property `true`, or clicks are ignored); no selection reaches the Bet Slip. (Which of the two is correct is open question #3 in §1.)
  * **API:** the request is rejected with HTTP `422` (semantic match validation, Spec §5.3).
  * **Ledger:** the balance equals `balance_before`; no receipt is issued.
  * *Out of scope pending PO answer:* matches labeled `TODAY` (date-only kickoff, see §1 open question #2).

---

### Scenario 5: Concurrency & In-Progress State Lock
* **ID:** `TC-BET-005`
* **Title:** No Duplicate Debits from Rapid Multi-Click or Concurrent In-Flight Requests
* **Priority:** High
* **Risk Rationale:** Slow networks make users click `Place Bet` repeatedly. Without a UI lock and a server-side in-progress guard (`409`, Spec §5.3), one user action can create several bets and debit the stake several times. That leads to reconciliation failures and complaints.
* **Preconditions:**
  * Balance reset (enough for several bets); `balance_before` captured.
  * `target_match` in the Bet Slip with stake `€10.00`.
* **Steps:**
  1. **UI multi-click:** fire 3 click events on `#bet-slip-place-bet` within the same event-loop tick (JavaScript `element.click()` ×3 through `execute_script`, because WebDriver can't reliably click within 100 ms).
  2. Verify that right after the first click, the label is `Placing...` and the `disabled` property is `true`.
  3. Wait for the outcome; verify **exactly one** result modal appears (Spec §2.3, "one final outcome").
  4. Close the receipt; `GET /api/balance` → verify `balance_before − 10.00`. Record it as `balance_mid`.
  5. **API concurrency:** send N = 2 (then N = 5) identical `POST /api/place-bet` requests in parallel (thread pool, started from a shared barrier) with the same `x-user-id` and body:
     ```json
     { "matchId": "<target_match.id>", "selection": "HOME", "stake": 10.00 }
     ```
  6. Record every status code. Let `accepted = count(status == 200)`.
  7. `GET /api/balance` → `balance_after`.
* **Expected Result:**
  * **UI:** extra clicks during `Placing...` are ignored; exactly one bet is placed and €10.00 is debited.
  * **API (an invariant that holds regardless of timing):**
    * Every response is either `200` or `409` (bet already in progress); no `500`.
    * `balance_mid − balance_after == 10.00 × accepted` (the ledger debits only accepted bets).
    * `accepted ≥ 1`.
  * *Note:* requests that do not overlap in time are legitimately separate bets. The test therefore checks that debits match accepted bets, not a fixed `200` + `409` pair, which avoids timing-dependent flakiness.

---

### Scenario 6: Failure Handling & Error Recovery (Rebet / Close / X)
* **ID:** `TC-BET-006`
* **Title:** Error Modal on Server Failure with Working Rebet, Close and X Actions and No Balance Deduction
* **Priority:** Medium
* **Risk Rationale:** Backends fail intermittently (timeouts, deadlocks, 500s). The client must not freeze in `Placing...`, must never deduct the stake for a failed bet, and must let the user retry (`Rebet`) or give up (`Close`/`X`) without leaving the slip in a broken state (Spec §2.3, §2.5).
* **Preconditions:**
  * `target_match` in the Bet Slip with stake `€10.00`; `balance_before` captured.
  * **Failure injection:** use Chrome DevTools Protocol via Selenium. Call `Fetch.enable` with pattern `*/api/place-bet`, then answer the paused request with `Fetch.fulfillRequest` (`responseCode: 500`). Alternatively, use `Network.emulateNetworkConditions(offline=true)` for the network-error variant. (A deliberately invalid payload is **not** used: it causes a `400`/`422` validation response, not a server failure.)
* **Steps:**
  1. Enable the 500 interception and click `Place Bet`.
  2. Verify `Placing...` clears (no endless spinner) and the Error Modal appears:
     * Title: `Something went wrong`
     * Body: says the bet could not be processed and suggests trying again
     * Actions: `Rebet` (primary), `Close` (secondary), top-right `X`
  3. `GET /api/balance` → verify it equals `balance_before`.
  4. **Rebet:** turn off the interception and click `Rebet`.
     * Verify the modal closes, a new `POST /api/place-bet` is sent with the **same** match, selection and stake, and the Success Receipt Modal appears.
     * Verify the balance is now `balance_before − 10.00` (exactly one debit).
  5. **Close:** set up a new selection with stake `€10.00`, re-enable the interception, and trigger the error modal. Click `Close`.
     * Verify the modal closes and the Bet Slip has no selection and no stake.
  6. **X:** repeat step 5 but dismiss with the top-right `X`.
     * Verify the result is identical to `Close` (Spec §2.5).
  7. Final `GET /api/balance` → verify it is unchanged since step 4.
* **Expected Result:**
  * A failed placement never deducts the balance and never leaves the UI stuck in `Placing...`.
  * The error modal text and actions match Spec §2.5.
  * `Rebet` closes the modal and resends the same bet, which leads to a single success and a single debit.
  * `Close` and `X` behave identically: the modal closes and the selection and stake are cleared.

---

## 4. Traceability Summary

| Spec section | Requirement | Scenario(s) |
| :--- | :--- | :--- |
| §1, §3 | Upcoming / pre-match only | TC-BET-004 |
| §2.1 | Match list; selection replacement | TC-BET-001, TC-BET-004 |
| §2.2 | Slip: one selection, stake, balance, payout | TC-BET-001 |
| §2.2 | Remove All / per-selection `x` | Deferred (Phase 2) |
| §2.3 | `Placing...` state, single final outcome, stake deducted | TC-BET-001, TC-BET-005, TC-BET-006 |
| §2.4 | Receipt fields (all 7) | TC-BET-001 |
| §2.5 | Error modal, Rebet / Close / X | TC-BET-006 |
| §2.6 | Date / odds filters | Deferred (Phase 2) |
| §3 | Stake min/max/precision, currency EUR | TC-BET-001, TC-BET-003 |
| §4.1 | Stake required / numeric / min / max / precision / balance | TC-BET-002, TC-BET-003 |
| §4.2 | Selection & match ID validation | TC-BET-003 (R1–R4), TC-BET-004 |
| §4.3 | Payload / method / user context | TC-BET-003 (R5–R7) |
| §4.4 | UI error copy | TC-BET-002, TC-BET-003 |
| §5.3 | Response contract and error classes (400/401/405/409/422/500) | TC-BET-001, TC-BET-003, TC-BET-005, TC-BET-006 |
| §5.3 | Reset-balance consistency (response body == persisted state) | Reset consistency guard in `reset_balance_precondition` (BUG-008); every scenario uses the persisted value |
