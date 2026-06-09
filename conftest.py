import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "DAM Page Object"))


@pytest.fixture(scope="session")
def base_url():
    return "https://dam-sit.mqbc21.com"


@pytest.fixture
def login_page(page, base_url):
    from login_page import LoginPage
    lp = LoginPage(page)
    lp.navigate(base_url)
    return lp


@pytest.fixture
def cex_connection_page(page, base_url):
    from login_page import LoginPage
    from cex_connection_page import CexConnectionPage
    lp = LoginPage(page)
    lp.navigate(base_url)
    lp.login("roninx688@gmail.com", "0987654321a@A")
    page.wait_for_url(lambda url: "/sign-in" not in url, timeout=15000)
    # Wait for portfolio page to fully render before interacting with the header
    page.wait_for_load_state("networkidle")
    cex_page = CexConnectionPage(page)
    # Pre-test cleanup: remove leftover exchanges so each test starts clean
    for name in ["David Binance Account X01", "Jeff BIT Account X01"]:
        try:
            cex_page.delete_exchange_by_name(name)
        except Exception:
            pass
    yield cex_page
    # Post-test cleanup: remove the exchange just connected
    for name in ["David Binance Account X01", "Jeff BIT Account X01"]:
        try:
            cex_page.delete_exchange_by_name(name)
        except Exception:
            pass
