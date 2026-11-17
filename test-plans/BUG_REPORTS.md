# Defect Report: Sports Betting — Single Bet Placement

- **Application Under Test (AUT):** [Sports Betting QA Application](https://qae-assignment-tau.vercel.app/?user-id=candidate-Mc2IYbjdqhj8)
- **Specification Source:** [Feature_Specification.pdf](../materials/Feature_Specification.pdf)
- **Related Test Plan:** [test-plan-single-bet-placement.md](test-plan-single-bet-placement.md)
- **Test Methodology:** Risk-Based Testing (RBT); exploratory + scripted verification (Selenium WebDriver for UI, direct HTTP for API)
- **Environment:** macOS (Apple Silicon), Chrome 157 (headless, 1440×1000), Python 3.10, Selenium 4.52
- **Frontend Build:** `/assets/index-BAomKdAy.js`
- **Test Account ID:** `candidate-Mc2IYbjdqhj8`

> **Reproduction precondition (applies to every defect):** start each repro with `POST /api/reset-balance` (header `x-user-id: candidate-Mc2IYbjdqhj8`).
>
> **Reference test data** (the latest upcoming match in the catalog, chosen so the data stays valid longest):
> - **Upcoming match:** `mls-lafc-inter-miami-2026-12-28` — **LAFC** (home) vs **Inter Miami** (away), MLS, kickoff **2026-12-28**, odds 1=2.20 / X=3.45 / 2=3.05. Valid until 2026-12-27; after that, use any match with `kickoffDate` after today from `GET /api/matches`.
> - **Past match (BUG-003 only):** `mls-inter-miami-lafc-2026-06-20` — **Inter Miami** (home) vs **LAFC** (away), MLS, kickoff **2026-06-20**, odds 1=2.65 / X=3.45 / 2=2.45. Permanently valid.

---

## Executive Summary & Defect Triage

17 defects are confirmed: **4 Critical, 1 High, 5 Medium, 7 Low**. Together they let a player (a) bet money they do not have — through the API *and* through the normal UI, (b) **mint balance with a negative stake**, and (c) bet on matches that have already finished. The customer's receipt also misstates the payout, the match and the selection, and the API settles payouts a cent below what the Bet Slip promises. The Low findings are protocol-conformance gaps in the API and defects in the match-catalog filters (Spec §2.6).

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
| [**BUG-010**](#bug-010) | API payout truncated to the cent instead of rounded (pays €0.01 less than the slip) | **Medium** | API | Payout accuracy |
| [**BUG-011**](#bug-011) | Malformed or empty JSON body returns `500`/`422` instead of `400` | Low | API | Protocol conformance |
| [**BUG-012**](#bug-012) | `GET /api/place-bet` returns `200 {}` instead of `405` | Low | API | Protocol conformance |
| [**BUG-013**](#bug-013) | `405` responses omit the mandatory `Allow` header | Low | API | Protocol conformance |
| [**BUG-014**](#bug-014) | Odds filter applies an invalid range (min > max) without feedback | Low | UI | Catalog filters |
| [**BUG-015**](#bug-015) | Odds filter lower bound is exclusive (spec: inclusive) | Low | UI | Catalog filters |
| [**BUG-016**](#bug-016) | Match counter stuck at "Showing 103 matches"; no empty-state message | Low | UI | Catalog filters / UX |
| [**BUG-017**](#bug-017) | Match card shows kickoff date only, no kickoff time | Low | UI + API | Match information |

**Notes on this revision**
- IDs are ordered by severity. BUG-010 – BUG-017 were added on 2026-11-17. None of them repeats BUG-001 – BUG-009 or a check already listed under *Verified as working*. Each new report has a **Detected by** line naming the test case that catches it, or stating that none does.
- Each defect has a **Test Data** line naming the exact data used and the equivalent data class that reproduces it if that data goes stale.
- Expected results quote only spec-defined status classes. Error codes such as `invalid_stake_min` are quoted as observations, not requirements.
- The frontend bundle is minified; quoted source lines are on line 49 of `/assets/index-BAomKdAy.js`.

### Verified as working (no defect)
Stake min/max/precision/type validation at both layers (except negative values, BUG-004). Invalid selection, blank/unknown match ID and non-object body → `422`/`400`. Missing or empty `x-user-id` → `401`. `PUT`/`DELETE`/`PATCH` → `405`. Concurrent requests: 5 parallel bets gave 3×`200` + 2×`409`, and the debit was exactly €30. Error modal copy plus Rebet/Close/X behaviour match spec §2.5. The UI input masks `10.555` → `10.55` and strips the `-` sign. All 103 matches have odds within [1.01, 1000].

Added 2026-11-17: a client-supplied `odds` field in the request body is ignored (the server uses catalog odds). Lower-case `selection` (`"home"`) and a whitespace-padded `matchId` are rejected with `422`. 30 sequential bets were all accepted with no throttling. For every match the implied probabilities sum to more than 1 (`1/home + 1/draw + 1/away` from 1.033 to 1.147), so betting all three outcomes never guarantees a profit. The date filter handles a single day and an inclusive range (either click order) correctly.

*Observed, not logged:* on 2026-11-17 around 09:30, every valid `POST /api/place-bet` returned `500 internal_server_error` for about 2 minutes, with no balance change. It could not be reproduced afterwards, so it is not registered.

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
* **Business Impact:** Any client or reconciliation job that trusts the reset response works from a wrong balance and reports false ledger mismatches.
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

---

### BUG-010
**Title:** API Payout Truncated to the Cent Instead of Rounded; the Settled Payout Is €0.01 Below the Slip's Potential Payout
**Severity:** Medium

* **Test Data:** `matchId: mls-lafc-inter-miami-2026-12-28` (LAFC vs Inter Miami, kickoff 2026-12-28), selection `HOME` (odds 2.20); stake `1.15` (exact product `2.53`). Second example: `eredivisie-ajax-az-2026-11-21` (Ajax vs AZ Alkmaar), `AWAY` (odds 4.40), stake `1.15` (exact product `5.06`). Reproduces with any match with `kickoffDate` after today and any stake whose `stake × odds` is not exactly representable in binary floating point, or ends in a half cent.
* **Reproduction Steps:**
  1. `POST /api/reset-balance`.
  2. In the UI, select **LAFC vs Inter Miami → 1** (2.20) and enter stake `1.15`. Note the slip's **Potential Payout**.
  3. ```bash
     curl -X POST https://qae-assignment-tau.vercel.app/api/place-bet \
       -H "Content-Type: application/json" -H "x-user-id: candidate-Mc2IYbjdqhj8" \
       -d '{"matchId":"mls-lafc-inter-miami-2026-12-28","selection":"HOME","stake":1.15}'
     ```
  4. Compare `payout` in the response with the slip value from step 2.
* **Expected Result:** Per Spec §2.2/§2.4 the payout is `stake × odds` in EUR to the cent: `1.15 × 2.20 = €2.53`. The slip, the receipt and the API agree.
* **Actual Result:** The slip shows **€2.53**, but the API returns **`"payout": 2.52`**:
  ```json
  {"message":"Bet placed successfully","matchId":"mls-lafc-inter-miami-2026-12-28","selection":"HOME","stake":1.15,"odds":2.2,"payout":2.52,"balance":118.85,"currency":"USD"}
  ```
  The server floors the floating-point product (`1.15 × 2.2 = 2.5299999999999998` → `2.52`). Further API results on 2026-11-17, with the exact value in brackets: Ajax–AZ `AWAY` 4.40 × `1.15` → `5.05` (5.06) and × `2.30` → `10.11` (10.12); Derby–Norwich `DRAW` 3.25 × `1.16` → `3.76` (3.77). Half-cent values always go down: Ajax–AZ `HOME` 1.85 × `1.10` → `2.03` (2.035 rounds to 2.04) and × `1.50` → `2.77` (2.775 rounds to 2.78). The same floor explains `"payout": -110.01` for a `-50` stake in BUG-004. A sweep of the catalog shows 509 combinations with an exact 2-decimal product that lose a cent, for upcoming matches and stakes €1.00–€10.00 alone. The UI slip uses `toFixed(2)` on the float, so it also shows some half-cent values a cent low (`1.15 × 3.90 = 4.485` → `€4.48`).
* **Business Impact:** Customers are systematically settled €0.01 below the payout shown before confirming, always in the operator's favour, which is a fair-payout compliance risk and a source of disputes.
* **Detected by:** TC-BET-003 row S11 (stake `1.15` on odds `2.20`, added 2026-11-17). S7 (`100 × 2.20`) and TC-BET-001 step 16 (`10 × 3.05`) use products that floor correctly, so they miss it.
* **Evidence:** API response above. [bug_010_017_slip_payout_5_06.png](screenshots/bug_010_017_slip_payout_5_06.png) — the Ajax vs AZ Alkmaar slip shows €5.06 for €1.15 @ 4.40; the same UI bet's `place-bet` response (captured via CDP) returned `"payout": 5.05`.

---

### BUG-011
**Title:** Malformed or Empty JSON Body Returns `500` / `422` Instead of `400`
**Severity:** Low

* **Test Data:** No match data required. Bodies `{bad`, `{not json`, `{"matchId":`, `   ` (whitespace only) and an empty body, all with `Content-Type: application/json`.
* **Reproduction Steps:**
  1. ```bash
     curl -i -X POST https://qae-assignment-tau.vercel.app/api/place-bet \
       -H "Content-Type: application/json" -H "x-user-id: candidate-Mc2IYbjdqhj8" -d '{bad'
     ```
  2. Repeat with each body listed in Test Data.
* **Expected Result:** Per Spec §4.3/§5.3 and the OpenAPI document (`400` example `invalid_json` / *"Malformed JSON body."*), all of them are rejected with **`400`**.
* **Actual Result:**
  | Body | Status | Response |
  | :--- | :-: | :--- |
  | `{bad`, `{not json`, `{"matchId":`, `   ` | **`500`** | `{"error":"internal_server_error","message":"Unable to process request."}` |
  | *(empty)* | **`422`** | `{"error":"invalid_match_id","message":"Match id is invalid."}` |
  | `"str"` (valid JSON, not an object) | `400` | `{"error":"invalid_json","message":"Malformed JSON body."}` — the error code fits the `{bad` case |
  | `null` / `[1,2]` | `400` | `invalid_request` (correct) |

  The parse error is not caught, so it escapes as an unhandled server error. No balance change. Reproduced 2/2 runs; other validation (for example stake `101` → `422`) behaved normally in the same run, so this is not the transient outage noted above.
* **Business Impact:** Client mistakes surface as server faults, inflating 5xx alerts, masking real outages and telling integrators to retry instead of fixing the request.
* **Detected by:** TC-BET-003 row R5 (`{not json` → `400`). The empty-body variant is not in the matrix.
* **Evidence:** Responses above (2026-11-17).

---

### BUG-012
**Title:** `GET /api/place-bet` Returns `200 {}` Instead of `405 Method Not Allowed`
**Severity:** Low

* **Test Data:** No match data required.
* **Reproduction Steps:**
  1. `curl -i https://qae-assignment-tau.vercel.app/api/place-bet -H "x-user-id: candidate-Mc2IYbjdqhj8"`
  2. For comparison, send `HEAD` and `PUT` to the same URL.
* **Expected Result:** Per Spec §4.3/§5.3, an unsupported method returns `405`. `HEAD`, `PUT`, `DELETE` and `PATCH` already do, and so does `GET /api/reset-balance`.
* **Actual Result:** `GET` returns **`HTTP/2 200`** with body `{}` and `content-type: application/json`. No bet is placed; the balance is unchanged (`120 → 120`).
* **Business Impact:** Monitoring, caches and clients see a successful empty response where the endpoint should refuse the request.
* **Detected by:** TC-BET-003 row R7 (`GET` / `PUT` → `405`). It is not a duplicate of the *Verified as working* entry, which covered only `PUT`/`DELETE`/`PATCH`.
* **Evidence:** `curl -i` output above (2026-11-17).

---

### BUG-013
**Title:** `405 Method Not Allowed` Responses Omit the Mandatory `Allow` Header
**Severity:** Low

* **Test Data:** No match data required. Any unsupported method, for example `PUT /api/place-bet`, `POST /api/matches`, `POST /api/balance`, `GET /api/reset-balance`.
* **Reproduction Steps:**
  1. `curl -i -X POST https://qae-assignment-tau.vercel.app/api/matches -H "x-user-id: candidate-Mc2IYbjdqhj8"`
  2. Inspect the response headers.
* **Expected Result:** RFC 9110 §15.5.6: *"The origin server MUST generate an `Allow` header field in a 405 response containing a list of the target resource's currently supported methods."* For example, `Allow: GET` on `/api/matches`.
* **Actual Result:** `405` with `{"error":"method_not_allowed"}`. There is no `Allow` header; only the CORS header `access-control-allow-methods: GET, OPTIONS` is present, and that applies to cross-origin preflight only.
* **Business Impact:** HTTP clients, API gateways and contract-testing tools can't discover the allowed methods; there is no user-facing effect.
* **Detected by:** Not covered. TC-BET-003 R7 checks only the status code.
* **Evidence:** Response headers above (2026-11-17), the same on all four endpoints.

---

### BUG-014
**Title:** Odds Filter Applies an Invalid Range (Min > Max) Without Any Feedback
**Severity:** Low

* **Test Data:** Odds filter Min `3.00`, Max `2.00`. Catalog-independent.
* **Reproduction Steps:**
  1. Open the app and click **Odds: All**.
  2. Type `3` in **Min** and `2` in **Max**.
  3. Click **Apply**.
* **Expected Result:** Per Spec §2.6, the odds filter *"must reject invalid ranges with clear feedback"*: an error message is shown and the range is not applied (or **Apply** is disabled).
* **Actual Result:** No message appears and **Apply** stays enabled. The filter is applied, the toggle reads **`Odds: 3.00 - 2.00`**, and the list becomes empty without explanation. While the invalid values are typed, the popover's range label shows `3.00 - 10.00`, which does not match the Max input.
* **Business Impact:** Users see an unexplained empty catalog and may assume no matches are available; bets and money are unaffected.
* **Detected by:** Not covered. Filters are deferred to Phase 2 in the test plan (§1 Scope Boundaries, §4 Traceability).
* **Evidence:** [bug_014_odds_min_gt_max_no_feedback.png](screenshots/bug_014_odds_min_gt_max_no_feedback.png) — Min `3,00`, Max `2`, **Apply** enabled, no validation message.

---

### BUG-015
**Title:** Odds Filter Lower Bound Is Exclusive; Spec Requires an Inclusive Range
**Severity:** Low

* **Test Data:** `bundesliga-bayern-stuttgart-2026-12-15` card *Bayern Munich vs Stuttgart* (UPCOMING, Tue Dec 15, odds 1.45 / 4.60 / **7.20**); draw odds `3.45`, which appears on 8 matches (for example `mls-lafc-inter-miami-2026-12-28`); PSG vs Marseille is `ligue-1-psg-marseille` (1.35 / 5.00 / 7.50).
* **Reproduction Steps:**
  1. Open **Odds** and set Min `7.20`, Max `8.00`, then **Apply**.
  2. Set Min `3.45`, Max `3.45`, then **Apply**.
  3. For comparison, set Min `1.00`, Max `1.35`, then **Apply** (PSG vs Marseille has home odds 1.35).
* **Expected Result:** Per Spec §2.6, the min/max range is inclusive. Step 1 shows Bayern vs Stuttgart (7.20 equals the minimum). Step 2 shows the 8 matches priced at 3.45. Step 3 shows PSG vs Marseille.
* **Actual Result:** Step 1 hides Bayern vs Stuttgart. Step 2 returns **0** matches. Step 3 shows PSG vs Marseille, so the upper bound is inclusive. In 5 of 6 ranges tested, the result counts match the rule `min < odds ≤ max` (for example 2.00–3.00 → 69 cards; the inclusive rule gives 73). The exception: in the 5.00–7.50 range, PSG vs Marseille (X 5.00, 2 7.50) is hidden although 7.50 is inside the upper bound.
* **Business Impact:** Users filtering from a listed price miss matching events; navigation only, no money is affected.
* **Detected by:** Not covered (filters deferred to Phase 2).
* **Evidence:** [bug_015_016_odds_exact_empty_stale_counter.png](screenshots/bug_015_016_odds_exact_empty_stale_counter.png) — `Odds: 3.45 - 3.45` applied, empty list.

---

### BUG-016
**Title:** Match Counter Stays at "Showing 103 matches" After Filtering; No Empty-State Message
**Severity:** Low

* **Test Data:** Any filter that narrows the list, for example Date `21/11/2026` (1 match), Odds `2.00 – 3.00` (69 matches) or Odds `3.45 – 3.45` (0 matches).
* **Reproduction Steps:**
  1. Open the app and note the counter `Showing 103 matches` next to *Upcoming Football Matches*.
  2. Apply any date or odds filter.
  3. Read the counter, and look at the list when no match qualifies.
* **Expected Result:** The counter shows the number of matches actually displayed. When none qualify, the list shows an empty-state message (for example, "No matches found for the selected filters").
* **Actual Result:** The counter stays at **`Showing 103 matches`** for 69, 3, 2, 1 and 0 visible cards. With 0 results the list area is blank, with no message.
* **Business Impact:** Users are misled about how many events match, and an empty filtered catalog looks broken (cosmetic only).
* **Detected by:** Not covered (filters deferred to Phase 2).
* **Evidence:** [bug_015_016_odds_exact_empty_stale_counter.png](screenshots/bug_015_016_odds_exact_empty_stale_counter.png) — `Showing 103 matches` above an empty list.

---

### BUG-017
**Title:** Match Card Shows Kickoff Date Only, With No Kickoff Time
**Severity:** Low

* **Test Data:** Any match, for example `mls-lafc-inter-miami-2026-12-28` (card label `Mon, Dec 28`), `eredivisie-ajax-az-2026-11-21` (`Saturday`) or the same-day `TODAY` match `ligue-1-marseille-psg-2026-11-17` (`Today`).
* **Reproduction Steps:**
  1. Open the app and read the label next to the competition name on any match card.
  2. `GET /api/matches` and inspect `kickoffDate`.
* **Expected Result:** Per Spec §2.1, each match shows a *"kickoff date/time label"*, so the user can tell when the match starts.
* **Actual Result:** Cards show only a day: `Mon, Dec 28`, a weekday name such as `Saturday`, or `Today`. No time is shown anywhere, and the API carries only a date (`kickoffDate: "YYYY-MM-DD"`), so the UI has no time to display.
* **Business Impact:** On match day customers can't tell whether a `TODAY` match has already kicked off, which matters for a pre-match-only product (test plan open question #2).
* **Detected by:** Not covered.
* **Evidence:** [bug_010_017_slip_payout_5_06.png](screenshots/bug_010_017_slip_payout_5_06.png) — card labels `Fri, Nov 13`, `Today`, `Saturday`, `Fri, Nov 27`, `Tue, Dec 01`, `Fri, Dec 04`, none with a time.
