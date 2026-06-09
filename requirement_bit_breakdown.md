# Requirement: BIT Breakdown Table

Validates the data displayed in the **BIT Breakdown Table** widget on the DAM portfolio page.  
The checker fetches ground-truth data from the Matrixport API and CoinGecko, then compares it against what the UI renders.

---

## Tokens Under Test

| Token | Source (Amount) | Source (Price) |
|-------|----------------|----------------|
| USDT  | Matrixport Wallet + Balance+ | CoinGecko live rate |
| USDC  | Matrixport Wallet | Matrixport RFQ buy price |
| TRX   | Matrixport Wallet | Matrixport RFQ buy price |

---

## Acceptance Criteria

### Step 1 — Wallet Balance

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Call Matrixport `GET /mapi/v1/wallet/balance` | Response code = 0; `available_balance` for USDT, USDC, TRX is returned |

---

### Step 2 — Balance+ (Flexi Saving)

| Step | Action | Expected Result |
|------|--------|----------------|
| 2 | Call Matrixport `GET /flexible/api/v2/user/asset/summary` | Response code = 0; USDT balance from `currencies` array is returned (may be 0 if no Balance+ position) |

> The **Total Amount** shown in the portfolio for USDT = Wallet balance + Balance+ balance.

---

### Step 3 — Matrixport RFQ Price

| Step | Action | Expected Result |
|------|--------|----------------|
| 3 | Call Matrixport `GET /trader/v2/api/rfq-price` for USDC (qty=20) and TRX (qty=300), side=buy | Response code = 0; `price` field returned for each pair |

> USDT has no RFQ pair (it is the quote currency). Its reference price is sourced from CoinGecko (Step 4).

---

### Step 4 — CoinGecko 24h Price

| Step | Action | Expected Result |
|------|--------|----------------|
| 4 | Call CoinGecko `GET /api/v3/coins/markets` for `tether`, `usd-coin`, `tron` | `current_price` (USD) and `price_change_percentage_24h` returned for all three tokens |

---

### Step 5 — DAM Login

| Step | Action | Expected Result |
|------|--------|----------------|
| 5a | Navigate to `https://dam-sit.mqbc21.com/sign-in` | Sign-in page loads |
| 5b | Enter credentials and wait for Cloudflare Turnstile to complete | Sign-in button becomes enabled |
| 5c | Click Sign In | User is redirected away from `/sign-in` |

> **Session reuse:** If `dam_auth.json` exists from a prior run, the saved browser storage state is loaded instead of performing a fresh login, to avoid rate-limiting.

---

### Step 6 — Navigate to Portfolio

| Step | Action | Expected Result |
|------|--------|----------------|
| 6 | Navigate to `/portfolio?portfolioId=<PORTFOLIO_ID>` | Portfolio overview page loads for the specified portfolio |

---

### Step 7 — Locate "David BIT Account" Table

| Step | Action | Expected Result |
|------|--------|----------------|
| 7a | Find the heading element with class `typography-title` and text `David BIT Account` | Heading element is located in the DOM |
| 7b | Scroll the heading into view | Lazy-loaded table content begins rendering |
| 7c | Wait up to 15 seconds for `tbody tr` count > 1 | Table rows are populated with real data (not "No data to display") |

---

### Step 8 — Scrape Table Data

| Step | Action | Expected Result |
|------|--------|----------------|
| 8a | Extract column headers from `thead` | Headers include: Token, Price(24H), Total Amount, Value |
| 8b | Extract main token rows from `tbody` (filter: Token column matches `[A-Z]{2,10}`) | Exactly the main rows (USDC, USDT, TRX) are returned — sub-rows (per-account breakdown) are excluded |
| 8c | Extract Total Value from the section heading's ancestor element | A `$XX.XX` value matching the portfolio section total is captured |

---

### Step 9 — Amount & Price Comparison (≤ 1% tolerance)

| Step | Check | Pass Condition |
|------|-------|----------------|
| 9a | **Amount Match** — API balance vs Portfolio "Total Amount" | `abs(api_balance − port_amount) / port_amount × 100 ≤ 1%` |
| 9b | **Price Match** — Reference price vs Portfolio "Price(24H)" | `abs(ref_price − port_price) / port_price × 100 ≤ 1%` |

> Reference price = Matrixport RFQ price for USDC and TRX; CoinGecko `current_price` for USDT.

---

### Step 10 — Value & Total Verification (≤ 1% tolerance)

| Step | Check | Pass Condition |
|------|-------|----------------|
| 10a | **Value Match** — Calculated value vs Portfolio "Value" per row | `abs(amount × ref_price − port_value) / port_value × 100 ≤ 1%` |
| 10b | **Total Value Match** — Sum of calculated values vs Portfolio section total | `abs(Σ calc_value − port_total) / port_total × 100 ≤ 1%` |

---

## Output

The checker produces a colour-coded Excel report (`bit_breakdown_table_report.xlsx`) with 5 sheets:

| Sheet | Contents |
|-------|----------|
| Step 1 – Wallet Balance | Raw wallet balance per token |
| Step 2 – Balance+ | Balance+ (flexi saving) balance per token |
| Step 3-4 – Prices | Matrixport RFQ price + CoinGecko 24h price + change % |
| Step 8 – Portfolio | Scraped table rows (Token, Price, Total Amount, Value) |
| Step 9-10 – Comparison | Per-token Amount/Price/Value match with PASS/FAIL; Total Value verdict |

Rows are highlighted **green** for PASS and **red** for FAIL.

---

## Running the Checker

```bash
# Headless (default)
python bit_breakdown_table_check.py --portfolio-id <PORTFOLIO_ID>

# With visible browser window
python bit_breakdown_table_check.py --portfolio-id <PORTFOLIO_ID> --headed

# With verbose API output
python bit_breakdown_table_check.py --portfolio-id <PORTFOLIO_ID> --verbose

# Custom output filename
python bit_breakdown_table_check.py --portfolio-id <PORTFOLIO_ID> --out my_report.xlsx
```

**Script file:** `bit_breakdown_table_check.py`

---

## Automated Test Coverage

| Step | Check | Method |
|------|-------|--------|
| 1 | Wallet balance fetched | `fetch_wallet_balance()` |
| 2 | Balance+ balance fetched | `fetch_asset_summary()` |
| 3 | Matrixport RFQ price fetched | `fetch_mp_rfq_price()` |
| 4 | CoinGecko price fetched | `fetch_coingecko_markets()` |
| 5-8 | DAM login + table scrape | `scrape_portfolio()` |
| 9 | Amount & price within 1% | `compare()` → `within_pct()` |
| 10 | Value & total within 1% | `compare()` → `within_pct()` |
