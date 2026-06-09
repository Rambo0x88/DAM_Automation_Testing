# DAM AI — Web Automation Testing

End-to-end test suite for the **DAM (Digital Asset Management)** web application, built with [Playwright](https://playwright.dev/python/) and [pytest](https://pytest.org/). Tests are structured using the **Page Object Model (POM)** pattern to keep locator logic separate from test scenarios.

---

## Tech Stack

| Tool | Version |
|------|---------|
| Python | 3.14+ |
| pytest | 9.0.3 |
| Playwright (Python) | 1.60.0 |
| pytest-playwright | 0.8.0 |

---

## Project Structure

```
DAM_AI_MCP_Web_Automation_Testing/
├── conftest.py                     # Shared pytest fixtures
├── requirement_login.txt           # Python dependencies
│
├── requirement_login.md            # Login test case requirements
├── requirement_cex_connection.md   # CEX Connection test case requirements
│
├── DAM Page Object/                # Page Object classes
│   ├── login_page.py               # LoginPage — locators & actions for /sign-in
│   └── cex_connection_page.py      # CexConnectionPage — locators & actions for exchange connect
│
└── DAM E2E/                        # Test files
    ├── test_login.py               # Login scenario tests (valid & invalid)
    └── test_cex_connection.py      # CEX Connection scenario tests (Binance & BIT)
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
