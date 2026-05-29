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
