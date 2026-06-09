# Requirement: Login

## Test Case 01: Valid Login – Valid Scenario

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Navigate to the DAM sign-in page (`/sign-in`) | Sign-in page is displayed |
| 2 | Enter a valid **Email** and **Password** | Fields accept input |
| 3 | Click the **Sign In** button | Login request is submitted |
| 4a | Verify redirect | User is redirected away from `/sign-in` |
| 4b | Verify landing page | URL contains `/portfolio` (Portfolio Overview page) |
| 4c | Verify no error | No error toast is displayed |

---

## Test Case 02: Invalid Login – Invalid Scenario

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Navigate to the DAM sign-in page (`/sign-in`) | Sign-in page is displayed |
| 2 | Enter a valid **Email** and an **incorrect Password** | Fields accept input |
| 3 | Click the **Sign In** button | Login request is submitted |
| 4a | Verify page | User remains on `/sign-in` page |
| 4b | Verify error toast | An error toast is displayed |
| 4c | Verify error message | Error toast contains a non-empty message |

---

## Automated Test Coverage

| Test Case | Test Method | Class |
|-----------|-------------|-------|
| TC01 – Redirect away from sign-in | `test_valid_login_redirects_away_from_sign_in` | `TestLoginScenario1` |
| TC01 – Lands on portfolio | `test_valid_login_lands_on_portfolio_overview` | `TestLoginScenario1` |
| TC01 – No error toast | `test_valid_login_no_error_toast` | `TestLoginScenario1` |
| TC02 – Stays on sign-in | `test_invalid_login_stays_on_sign_in_page` | `TestLoginScenario2` |
| TC02 – Shows error toast | `test_invalid_login_shows_error_toast` | `TestLoginScenario2` |
| TC02 – Error message content | `test_invalid_login_error_message_content` | `TestLoginScenario2` |

**Test file:** `DAM E2E/test_login.py`
**Page Object:** `DAM Page Object/login_page.py`
