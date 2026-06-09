# DAM AI — Web Automation Testing

End-to-end test suite for the **DAM (Digital Asset Management)** web application, built with [Playwright](https://playwright.dev/python/) and [pytest](https://pytest.org/). Includes automated E2E tests (Page Object Model pattern) and standalone acceptance-criteria checkers for portfolio data validation.

---

## Tech Stack

| Tool | Version |
|------|---------|
| Python | 3.14+ |
| pytest | 9.0.3 |
| Playwright (Python) | 1.60.0 |
| pytest-playwright | 0.8.0 |
| requests | latest |
| openpyxl | latest |

---

## Project Structure

```
DAM_AI_MCP_Web_Automation_Testing/
├── conftest.py                     # Shared pytest fixtures
├── requirement_login.txt           # Python dependencies
│
├── requirement_login.md            # Login test case requirements
├── requirement_cex_connection.md   # CEX Connection test case requirements
├── requirement_bit_breakdown.md    # BIT Breakdown Table acceptance criteria
│
├── DAM Page Object/                # Page Object classes
│   ├── login_page.py               # LoginPage — locators & actions for /sign-in
│   └── cex_connection_page.py      # CexConnectionPage — locators & actions for exchange connect
│
├── DAM E2E/                        # Playwright / pytest test files
│   ├── test_login.py               # Login scenario tests (valid & invalid)
│   └── test_cex_connection.py      # CEX Connection scenario tests (Binance & BIT)
│
├── bit_breakdown_table_check.py    # BIT Breakdown Table acceptance criteria checker
├── matrixport_price.py             # Matrixport RFQ price fetcher (10 USDT pairs)
└── coingecko_price.py              # CoinGecko price fetcher with 24h stats (51 pairs)
```

---

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

### 2. Install dependencies

```bash
pip install -r requirement_login.txt
```

### 3. Install Playwright browsers

```bash
playwright install
```

---

## Running Tests

Run the full suite:

```bash
pytest
```

Run with a visible browser (headed mode):

```bash
pytest --headed
```

Run a specific test file:

```bash
pytest "DAM E2E/test_login.py"
pytest "DAM E2E/test_cex_connection.py"
```

Run a specific test class or test:

```bash
pytest "DAM E2E/test_login.py::TestLoginScenario1"
pytest "DAM E2E/test_cex_connection.py::TestCexConnectionScenario1"
```

Slow down execution for debugging:

```bash
pytest --headed --slowmo=500
```

---

## Standalone Scripts

### BIT Breakdown Table Checker — `bit_breakdown_table_check.py`

Validates all 10 acceptance criteria for the **BIT Breakdown Table** widget on the DAM portfolio page. Fetches balances from the Matrixport API, prices from Matrixport RFQ and CoinGecko, scrapes the portfolio table via Playwright, compares amounts/prices/values within 1% tolerance, and exports a colour-coded Excel report.

> Full requirements: [requirement_bit_breakdown.md](requirement_bit_breakdown.md)

```bash
# Run headless (default)
python bit_breakdown_table_check.py --portfolio-id <PORTFOLIO_ID>

# Run with visible browser
python bit_breakdown_table_check.py --portfolio-id <PORTFOLIO_ID> --headed

# Run with verbose API output
python bit_breakdown_table_check.py --portfolio-id <PORTFOLIO_ID> --verbose

# Custom output file
python bit_breakdown_table_check.py --portfolio-id <PORTFOLIO_ID> --out my_report.xlsx
```

Output: `bit_breakdown_table_report.xlsx` (5 sheets — wallet balance, Balance+, prices, portfolio rows, comparison results)

---

### Matrixport Price Fetcher — `matrixport_price.py`

Fetches live RFQ buy prices for 10 USDT pairs from the Matrixport API using direct HTTP (no ccxt).

```bash
# Fetch prices for the hardcoded pair list
python matrixport_price.py

# List all available USDT pairs on Matrixport
python matrixport_price.py --list-pairs
```

Output: `matrixport_prices.json`

---

### CoinGecko Price Fetcher — `coingecko_price.py`

Fetches current price and 24h stats (change %, high, low, volume) for 51 USDT-paired tokens from CoinGecko. No API key required.

```bash
# Fetch prices for all 51 coins
python coingecko_price.py

# Search CoinGecko for a coin ID
python coingecko_price.py --list-coins sol
```

Output: `coingecko_prices.json`

---

## Test Coverage

### Login — `DAM E2E/test_login.py`

> Full requirements: [requirement_login.md](requirement_login.md)

| Scenario | Test | Description |
|----------|------|-------------|
| Valid Login | `test_valid_login_redirects_away_from_sign_in` | User is redirected away from `/sign-in` |
| Valid Login | `test_valid_login_lands_on_portfolio_overview` | URL contains `/portfolio` after login |
| Valid Login | `test_valid_login_no_error_toast` | No error toast is displayed |
| Invalid Login | `test_invalid_login_stays_on_sign_in_page` | User stays on `/sign-in` |
| Invalid Login | `test_invalid_login_shows_error_toast` | Error toast becomes visible |
| Invalid Login | `test_invalid_login_error_message_content` | Error toast text is non-empty |

---

### CEX Connection — `DAM E2E/test_cex_connection.py`

> Full requirements: [requirement_cex_connection.md](requirement_cex_connection.md)

| Scenario | Test | Description |
|----------|------|-------------|
| Binance – Valid | `test_connect_binance_successfully` | Success toast visible and contains "Successfully connected CEX" |
| BIT – Valid | `test_connect_bit_successfully` | Success toast visible and contains "Successfully connected CEX" |

---

### BIT Breakdown Table — `bit_breakdown_table_check.py`

> Full requirements: [requirement_bit_breakdown.md](requirement_bit_breakdown.md)

| Step | Check | Description |
|------|-------|-------------|
| 1 | Wallet Balance | Fetch USDT/USDC/TRX available balance from Matrixport Wallet API |
| 2 | Balance+ | Fetch USDT/USDC/TRX balance from Matrixport Balance+ (flexi saving) |
| 3 | Matrixport Price | Fetch live RFQ buy price for USDC and TRX (USDT uses CoinGecko live rate) |
| 4 | CoinGecko Price | Fetch 24h market price for USDT, USDC, TRX from CoinGecko |
| 5 | DAM Login | Authenticate to DAM (session reuse via `dam_auth.json`) |
| 6 | Navigate to Portfolio | Load portfolio page by ID |
| 7 | Locate Table | Find "David BIT Account" section and wait for lazy-loaded table data |
| 8 | Scrape Table | Extract Token, Price(24H), Total Amount, Value for each row |
| 9 | Amount & Price Match | Compare API balance vs portfolio amount (≤1%), API price vs displayed price (≤1%) |
| 10 | Value & Total Match | Verify calculated value (amount × price) matches displayed value and total (≤1%) |

---

## Configuration

The base URL is defined in `conftest.py` as a session-scoped fixture:

```python
@pytest.fixture(scope="session")
def base_url():
    return "https://dam-sit.mqbc21.com"
```

To run tests against a different environment, override it via the CLI:

```bash
pytest --base-url https://dam-uat.mqbc21.com
```

---

## Adding New Tests

1. Create a **Page Object** in `DAM Page Object/` for the new page.
2. Add a **requirement `.md` file** documenting the test cases.
3. Add a **test file** under `DAM E2E/` following the `test_*.py` naming convention.
4. Register shared fixtures in `conftest.py` if needed.
