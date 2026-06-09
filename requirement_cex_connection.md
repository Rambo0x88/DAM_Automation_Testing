# Requirement: CEX Connection

## Test Case 01: Connect Binance Account Successfully – Valid Scenario

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Log in to DAM | User is authenticated and redirected to Portfolio |
| 2 | Click the Avatar icon > Select **Profile** | User is navigated to Account Settings page |
| 3 | Go to **Connected Wallet & Exchange** > Select the **Exchange** tab > Click the **Connect Exchange** button | Connect Exchange dialog is displayed |
| 3a | Enter **Display Name**: `David Binance Account X01` | Field accepts input |
| 3b | Enter **API Key**: _(Binance API key)_ | Field accepts input |
| 3c | Enter **Secret Key**: _(Binance Secret key)_ | Field accepts input |
| 3d | Click the **Connect** button | Connection request is submitted |
| 4 | Verify result | Success message **"Successfully connected CEX"** is displayed |

---

## Test Case 02: Connect BIT Account Successfully – Valid Scenario

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Log in to DAM | User is authenticated and redirected to Portfolio |
| 2 | Click the Avatar icon > Select **Profile** | User is navigated to Account Settings page |
| 3 | Go to **Connected Wallet & Exchange** > Select the **Exchange** tab > Select the **BIT** icon > Click the **Connect Exchange** button | Connect Exchange dialog is displayed with BIT selected |
| 3a | Enter **Display Name**: `Jeff BIT Account X01` | Field accepts input |
| 3b | Enter **API Key**: _(BIT API key)_ | Field accepts input |
| 3c | Enter **Secret Key**: _(BIT Secret key)_ | Field accepts input |
| 3d | Click the **Connect** button | Connection request is submitted |
| 4 | Verify result | Success message **"Successfully connected CEX"** is displayed |

---

## Automated Test Coverage

| Test Case | Test Method | Class |
|-----------|-------------|-------|
| TC01 – Binance success toast + message | `test_connect_binance_successfully` | `TestCexConnectionScenario1` |
| TC02 – BIT success toast + message | `test_connect_bit_successfully` | `TestCexConnectionScenario2` |

**Test file:** `DAM E2E/test_cex_connection.py`
**Page Object:** `DAM Page Object/cex_connection_page.py`
