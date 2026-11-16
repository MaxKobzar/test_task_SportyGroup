# Defect Report: Sports Betting — Single Bet Placement

- **Application Under Test (AUT):** [Sports Betting QA Application](https://qae-assignment-tau.vercel.app/?user-id=candidate-Mc2IYbjdqhj8)
- **Specification Source:** [Feature_Specification.pdf](../materials/Feature_Specification.pdf)
- **Related Test Plan:** [test-plan-single-bet-placement.md](test-plan-single-bet-placement.md)
- **Test Methodology:** Risk-Based Testing (RBT); exploratory + scripted verification (Selenium WebDriver for UI, direct HTTP for API)
- **Environment:** macOS (Apple Silicon), Chrome 157 (headless, 1440×1000), Python 3.10, Selenium 4.52
- **Frontend Build:** `/assets/index-BAomKdAy.js`
- **Test Account ID:** `candidate-Mc2IYbjdqhj8`
- **Last Verified:** 2026-11-16 — all defects below reproduced on this date

> **Reproduction precondition (applies to every defect):** start each repro with `POST /api/reset-balance` (header `x-user-id: candidate-Mc2IYbjdqhj8`).
>
> **Reference test data** (the latest upcoming match in the catalog, chosen so the data stays valid longest):
> - **Upcoming match:** `mls-lafc-inter-miami-2026-12-28` — **LAFC** (home) vs **Inter Miami** (away), MLS, kickoff **2026-12-28**, odds 1=2.20 / X=3.45 / 2=3.05. Valid until 2026-12-27; after that, use any match with `kickoffDate` after today from `GET /api/matches`.
> - **Past match (BUG-003 only):** `mls-inter-miami-lafc-2026-06-20` — **Inter Miami** (home) vs **LAFC** (away), MLS, kickoff **2026-06-20**, odds 1=2.65 / X=3.45 / 2=2.45. Permanently valid.

---

## Executive Summary & Defect Triage

9 defects of Medium severity or higher are confirmed: **4 Critical, 1 High, 4 Medium**. Together they let a player (a) bet money they do not have — through the API *and* through the normal UI, (b) **mint balance with a negative stake**, and (c) bet on matches that have already finished. The customer's receipt also misstates the payout, the match and the selection.

| Bug ID | Title | Severity | Layer | Impact Area |
| :--- | :--- | :--- | :--- | :--- |
| [**BUG-001**](#bug-001) | API permits negative account balance (overdraft) | **Critical** | API | Financial solvency |
| [**BUG-002**](#bug-002) | Receipt potential payout hardcoded to `stake × 2` | **Critical** | UI | Contractual / regulatory |
| [**BUG-003**](#bug-003) | Wagers accepted on `PAST` (finished) matches | **Critical** | UI + API | Past-posting fraud |
| [**BUG-004**](#bug-004) | Negative stake accepted by API and **credits** the balance | **Critical** | API | Financial solvency / fraud |
| [**BUG-005**](#bug-005) | Balance not refreshed after a bet → stale balance enables UI-only overdraft | **High** | UI | Financial solvency / UX |
| [**BUG-006**](#bug-006) | Receipt shows match participants inverted (`Away vs Home`) | **Medium** | UI | Contractual accuracy |
| [**BUG-007**](#bug-007) | `POST /api/place-bet` returns `currency: "USD"` instead of `"EUR"` | **Medium** | API | Reconciliation |
| [**BUG-008**](#bug-008) | `reset-balance` response (€125.50) disagrees with persisted balance (€120.00) | **Medium** | API | Ledger consistency |
| [**BUG-009**](#bug-009) | Success receipt omits the **Selection** field | **Medium** | UI | Contractual accuracy |

**Notes on this revision**
- IDs are ordered by severity. Low-severity findings are not part of this register.
- Each defect has a **Test Data** line naming the exact data used and the equivalent data class that reproduces it if that data goes stale.
- Expected results quote only spec-defined status classes. Error codes such as `invalid_stake_min` are quoted as observations, not requirements.
- The frontend bundle is minified; quoted source lines are on line 49 of `/assets/index-BAomKdAy.js`.

### Verified as working (no defect)
Stake min/max/precision/type validation at both layers (except negative values, BUG-004). Invalid selection, blank/unknown match ID and non-object body → `422`/`400`. Missing or empty `x-user-id` → `401`. `PUT`/`DELETE`/`PATCH` → `405`. Concurrent requests: 5 parallel bets gave 3×`200` + 2×`409`, and the debit was exactly €30. Error modal copy plus Rebet/Close/X behaviour match spec §2.5. The UI input masks `10.555` → `10.55` and strips the `-` sign. All 103 matches have odds within [1.01, 1000].

---

## Detailed Bug Reports

### BUG-001
**Title:** API Permits Negative Account Balance (Overdraft via `POST /api/place-bet`)
**Severity:** Critical

* **Test Data:** `matchId: mls-lafc-inter-miami-2026-12-28` (LAFC vs Inter Miami, kickoff 2026-12-28), selection `HOME` (odds 2.20); stakes `100` then `50`; starting balance €120.00 (persisted, see BUG-008). Reproduces with any match with `kickoffDate` after today in `GET /api/matches` and any stake greater than the remaining balance.
* **Reproduction Steps:**
  1. `POST /api/reset-balance` → `GET /api/balance` returns `120`.
  2. Place a €100.00 bet so the balance becomes €20.00:
     ```bash
     curl -X POST https://qae-assignment-tau.vercel.app/api/place-bet \
       -H "Content-Type: application/json" -H "x-user-id: candidate-Mc2IYbjdqhj8" \
       -d '{"matchId":"mls-lafc-inter-miami-2026-12-28","selection":"HOME","stake":100}'
     ```
  3. Send the same request with `"stake": 50` (greater than the €20.00 balance).
  4. `GET /api/balance`, then open the web app and select **LAFC vs Inter Miami → 1**.
* **Expected Result:** Per Spec §4.1 (*Must not exceed available balance — UI + API*), step 3 is rejected with HTTP `422` (semantic validation failure, Spec §5.3) and an insufficient-balance error. The balance stays at €20.00.
* **Actual Result:** HTTP `200`:
  ```json
  {"message":"Bet placed successfully","matchId":"mls-lafc-inter-miami-2026-12-28","selection":"HOME","stake":50,"odds":2.2,"payout":110,"balance":-30,"currency":"USD"}
  ```
  `GET /api/balance` → `{"balance": -30, "currency": "EUR"}`. The UI header shows **`Balance: €-30.00`**. Only the UI blocks further bets (`Insufficient balance`); the server never does. The same overdraft is also reachable **without touching the API** — see BUG-005.
* **Business Impact:** Players can bet on credit with no limit, exposing the operator to unrecoverable losses and regulatory sanctions.
* **Evidence:** [bug_001_negative_balance.png](screenshots/bug_001_negative_balance.png) — header `Balance: €-30.00`; the slip for LAFC vs Inter Miami shows `Insufficient balance`.

---

### BUG-002
**Title:** Potential Payout in Success Receipt Hardcoded to `stake × 2` (Ignores Odds)
**Severity:** Critical

* **Test Data:** `matchId: mls-lafc-inter-miami-2026-12-28` (LAFC vs Inter Miami, kickoff 2026-12-28), selection `AWAY` (odds 3.05); stake `5.00`. Reproduces with any match with `kickoffDate` after today in `GET /api/matches` and any outcome whose odds ≠ 2.00.
* **Reproduction Steps:**
  1. Open `https://qae-assignment-tau.vercel.app/?user-id=candidate-Mc2IYbjdqhj8`.
  2. On **LAFC vs Inter Miami** (MLS, Mon, Dec 28), click odds `2` (Away, 3.05).
  3. Enter stake `5.00`. The Bet Slip correctly shows Potential Payout **€15.25**.
  4. Click **Place Bet** and wait for the success receipt.
* **Expected Result:** Per Spec §2.4, the receipt shows the potential payout at the placement odds: `5.00 × 3.05 = €15.25`.
* **Actual Result:** The receipt (`#B-43255`) shows **€10.00**. It is always `stake × 2`, whatever the odds: €50.00 @ 2.20 shows **€100.00** instead of €110.00 (`#B-52634`), and €10.00 @ 2.65 shows **€20.00** instead of €26.50 (`#B-48857`). Source in the minified bundle `/assets/index-BAomKdAy.js` (line 49):
  ```javascript
  matchLabel:`${al.awayTeam} vs ${al.homeTeam}`,stakeAmount:R,odds:al.odds,potentialPayout:R*2,placedLab…
  ```
* **Business Impact:** The customer's record of the bet shows the wrong payout, which leads to disputes, chargebacks and regulatory complaints; for odds above 2.00 it under-states winnings.
* **Evidence:** [bug_002_slip_payout_15_25.png](screenshots/bug_002_slip_payout_15_25.png) (slip: €15.25) → [bug_002_006_009_receipt.png](screenshots/bug_002_006_009_receipt.png) (receipt: STAKE €5.00, ODDS 3.05, Potential Payout **€10.00**).

---

### BUG-003
**Title:** Wagers Accepted on Finished Matches (`PAST` Badge) at UI and API
**Severity:** Critical

* **Test Data:** `matchId: mls-inter-miami-lafc-2026-06-20` (Inter Miami vs LAFC, kickoff 2026-06-20), selection `HOME` (odds 2.65); stake `10.00`. Stable: the match stays in the past. Reproduces with any match whose `kickoffDate` is before today.
* **Reproduction Steps:**
  1. Open the app and scroll to **Inter Miami vs LAFC** (badge `PAST`, *MLS, Sat, Jun 20*).
  2. Inspect odds button `1` (2.65): its `disabled` property is `false`.
  3. Click it, enter stake `10.00`, and click **Place Bet**.
  4. Separately: `POST /api/place-bet` with `{"matchId":"mls-inter-miami-lafc-2026-06-20","selection":"HOME","stake":10}`.
* **Expected Result:** Spec §1/§3 allow upcoming (pre-match) events only, and §2.1 says the list displays upcoming matches. Past matches are either not shown or not selectable. The API rejects the request with HTTP `422` (semantic match validation, Spec §5.3). No balance is deducted.
* **Actual Result:** The odds buttons are fully interactive. The UI bet succeeds with receipt `#B-48857`. The API returns `200`:
  ```json
  {"message":"Bet placed successfully","matchId":"mls-inter-miami-lafc-2026-06-20","selection":"HOME","stake":10,"odds":2.65,"payout":26.5,"balance":110,"currency":"USD"}
  ```
  The balance is debited by €10.00 (`120 → 110`).
* **Business Impact:** Players can bet on matches whose result is already known and win every time, a direct and repeatable loss for the operator (past-posting fraud).
* **Evidence:** [bug_003_past_match_bet_accepted.png](screenshots/bug_003_past_match_bet_accepted.png) — success receipt `#B-48857` above the `PAST` card *Inter Miami vs LAFC (Sat, Jun 20)*.

---

### BUG-004
**Title:** Negative Stake Accepted by API and Credits the User's Balance
**Severity:** Critical

* **Test Data:** `matchId: mls-lafc-inter-miami-2026-12-28` (LAFC vs Inter Miami, kickoff 2026-12-28), selection `HOME` (odds 2.20); stake `-50` (also `-5`, `-0.5`). Reproduces with any match with `kickoffDate` after today in `GET /api/matches` and any negative stake.
* **Reproduction Steps:**
  1. `POST /api/reset-balance`; `GET /api/balance` → `120`.
  2. ```bash
     curl -X POST https://qae-assignment-tau.vercel.app/api/place-bet \
       -H "Content-Type: application/json" -H "x-user-id: candidate-Mc2IYbjdqhj8" \
       -d '{"matchId":"mls-lafc-inter-miami-2026-12-28","selection":"HOME","stake":-50}'
     ```
  3. `GET /api/balance`.
* **Expected Result:** Per Spec §3/§4.1 (minimum €1.00, positive values; UI + API), the request is rejected with HTTP `422`, the same way the API already rejects `0` and `0.99` (`invalid_stake_min`).
* **Actual Result:** HTTP `200`:
  ```json
  {"message":"Bet placed successfully","matchId":"mls-lafc-inter-miami-2026-12-28","selection":"HOME","stake":-50,"odds":2.2,"payout":-110.01,"balance":170,"currency":"USD"}
  ```
  The balance **rises from €120.00 to €170.00**. Repeatable for any negative value (`-5` → €125.00, `-0.5` → €120.50). `0` and `0.99` are rejected with `422`, so the minimum-stake check appears to cover only `[0, 1)`. The UI is not affected: it strips the `-` sign.
* **Business Impact:** Anyone with an HTTP client can add unlimited money to their balance and then withdraw or bet it, an unbounded direct financial loss.
* **Evidence:** API-only; response above, `GET /api/balance` before/after `120 → 170`. Supporting: [bug_004_ui_strips_negative_sign.png](screenshots/bug_004_ui_strips_negative_sign.png) — typing `-5` in the LAFC vs Inter Miami slip yields `5`, so the defect cannot be triggered from the UI.

---

### BUG-005
**Title:** Displayed Balance Not Refreshed After a Successful Bet; Stale Balance Lets a Normal User Overdraw Through the UI
**Severity:** High

* **Test Data:** `matchId: mls-lafc-inter-miami-2026-12-28` (LAFC vs Inter Miami, kickoff 2026-12-28), selection `1`/HOME (odds 2.20); stakes `100.00` then `50.00`; starting balance €120.00. Reproduces with any match with `kickoffDate` after today in `GET /api/matches` and any two consecutive UI bets whose total exceeds the balance.
* **Reproduction Steps:**
  1. `POST /api/reset-balance`, then open the app. The header and empty slip show `Balance: €120.00`.
  2. Select **LAFC vs Inter Miami → 1** (2.20), stake `100.00`, **Place Bet**, then **Close** the receipt.
  3. Observe the header balance and call `GET /api/balance`.
  4. Without reloading, select **LAFC vs Inter Miami → 1** again, enter `50.00`, and click **Place Bet**.
  5. Reload the page.
* **Expected Result:** Per Spec §2.3 ("On success: stake is deducted"), the header and slip show €20.00 straight after step 2. In step 4 the slip shows `Insufficient balance` and `Place Bet` is disabled (Spec §4.1/§4.4).
* **Actual Result:** After step 2 the header still shows **€120.00** while the API says **€20.00**; it stays stale until a full reload. In step 4 `Place Bet` is enabled, the €50.00 bet is **accepted**, and receipt `#B-52634` is shown. After reload the header shows **`€-30.00`**. Combined with BUG-001, a normal user can overdraw through the UI alone.
* **Business Impact:** Customers see a wrong, inflated balance after every bet and can unknowingly bet money they don't have, creating debt and support load without any API manipulation.
* **Evidence:**
  * [bug_005_ui_overdraft_stale_balance_receipt.png](screenshots/bug_005_ui_overdraft_stale_balance_receipt.png) — the €50.00 bet accepted (`#B-52634`) while the header still shows €120.00 (real balance: €20.00).
  * [bug_005_ui_overdraft_negative_after_reload.png](screenshots/bug_005_ui_overdraft_negative_after_reload.png) — after reload: `Balance: €-30.00`.

---

### BUG-006
**Title:** Match Participants Inverted on Success Receipt (`Away vs Home`)
**Severity:** Medium

* **Test Data:** `matchId: mls-lafc-inter-miami-2026-12-28` (home `LAFC`, away `Inter Miami`, kickoff 2026-12-28), selection `AWAY`; stake `5.00`. Affects every match; reproduces with any match with `kickoffDate` after today in `GET /api/matches`.
* **Reproduction Steps:**
  1. Select **LAFC** (home) vs **Inter Miami** (away), outcome `2`, stake `5.00`.
  2. Click **Place Bet** and read the `MATCH` line on the receipt.
* **Expected Result:** Per Spec §2.1/§2.4, the match details read `Home vs Away` → `LAFC vs Inter Miami`, matching the catalog and the Bet Slip.
* **Actual Result:** The receipt (`#B-43255`) shows **`Inter Miami vs LAFC`**. The same happens on every match: the past fixture *Inter Miami (home) vs LAFC* produces a receipt reading `LAFC vs Inter Miami` (`#B-48857`). Source (`/assets/index-BAomKdAy.js`, line 49): ``matchLabel:`${al.awayTeam} vs ${al.homeTeam}` ``.
* **Business Impact:** The receipt contradicts the slip, so customers doubt which side they backed, which drives disputes and support contacts.
* **Evidence:** [bug_002_006_009_receipt.png](screenshots/bug_002_006_009_receipt.png) — the catalog card reads LAFC / Inter Miami; the receipt reads `Inter Miami vs LAFC`.

---

### BUG-007
**Title:** `POST /api/place-bet` Returns `currency: "USD"` Instead of `"EUR"`
**Severity:** Medium

* **Test Data:** `matchId: mls-lafc-inter-miami-2026-12-28` (LAFC vs Inter Miami, kickoff 2026-12-28), selection `HOME` (odds 2.20); stake `100`. Affects every successful placement; reproduces with any match with `kickoffDate` after today in `GET /api/matches` and any valid stake.
* **Reproduction Steps:**
  1. Send a valid `POST /api/place-bet` (LAFC vs Inter Miami, `HOME`, stake `100`).
  2. Inspect `currency` in the response; compare it with `GET /api/balance`.
* **Expected Result:** Per Spec §3 (Currency: EUR) and §5.3 (`currency: "EUR"`).
* **Actual Result:** `"currency": "USD"` on every successful placement, while `GET /api/balance` and `POST /api/reset-balance` return `"EUR"`.
  ```json
  {"message":"Bet placed successfully","matchId":"mls-lafc-inter-miami-2026-12-28","selection":"HOME","stake":100,"odds":2.2,"payout":220,"balance":20,"currency":"USD"}
  ```
* **Business Impact:** Bet records carry the wrong currency, which breaks settlement, reporting and audit reconciliation against the EUR ledger.
* **Evidence:** API response above. Reproduced 2026-11-16 on every successful placement in the run (HOME and AWAY, upcoming and past matches).

---

### BUG-008
**Title:** `POST /api/reset-balance` Response Body Disagrees With Persisted Balance
**Severity:** Medium

* **Test Data:** No match data required. Account `candidate-Mc2IYbjdqhj8`; `POST /api/reset-balance` response `125.5` vs persisted `120`.
* **Reproduction Steps:**
  1. `POST /api/reset-balance` → note `balance` in the response.
  2. `GET /api/balance` (immediately, and again after a few seconds).
  3. Open the app and read the header balance.
* **Expected Result:** Per Spec §5.3: *"Response body and persisted state must be consistent after reset."* Every source reports the same value.
* **Actual Result:** The reset response says **`125.5`**, but `GET /api/balance` returns **`120`** and the UI shows **€120.00**. Reproduced 3/3 times; not a timing issue.
* **Business Impact:** The ledger and the API that reports on it disagree. Any client or test that trusts the reset response works from a wrong balance, and real reconciliation jobs would produce false mismatches.
* **Evidence:** [bug_008_reset_balance_mismatch_ui.png](screenshots/bug_008_reset_balance_mismatch_ui.png) — the UI shows €120.00 straight after a reset whose response returned `125.5`.

---

### BUG-009
**Title:** Success Receipt Omits the Selection (Outcome Backed)
**Severity:** Medium

* **Test Data:** `matchId: mls-lafc-inter-miami-2026-12-28` (LAFC vs Inter Miami, kickoff 2026-12-28), selection `AWAY` (`Match Winner: Away`); stake `5.00`. Affects every receipt; reproduces with any match with `kickoffDate` after today in `GET /api/matches`.
* **Reproduction Steps:**
  1. Select **LAFC vs Inter Miami → 2** (Away); the slip shows `Match Winner: Away`.
  2. Stake `5.00`, then **Place Bet**.
  3. Read the receipt fields.
* **Expected Result:** Per Spec §2.4, the receipt shows Bet ID, Match details, **Selection**, Stake, Odds at placement, Potential payout and Placement timestamp.
* **Actual Result:** The receipt (`#B-43255`) shows Bet ID, Match, Stake, Odds, Potential Payout and Timestamp. **There is no Selection field** (no Home/Draw/Away / `Match Winner: …`). The receipt view model in the bundle has no selection property: `{betId, matchLabel, stakeAmount, odds, potentialPayout, placedLabel}`.
* **Business Impact:** The customer's only confirmation does not say which outcome they backed; combined with the inverted teams (BUG-006) it cannot be relied on.
* **Evidence:** [bug_002_slip_payout_15_25.png](screenshots/bug_002_slip_payout_15_25.png) (slip: `Match Winner: Away`) → [bug_002_006_009_receipt.png](screenshots/bug_002_006_009_receipt.png) (receipt: no Selection line).
