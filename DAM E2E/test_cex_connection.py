import pytest

BINANCE_DISPLAY_NAME = "David Binance Account X01"
BINANCE_API_KEY = "svkUxyJnJsnTF7w7TepyYiJFuI2W9CURCwsWXI8DjmmeAVo9Fdb8BGs1yonxWgPF"
BINANCE_SECRET_KEY = "mPxuhbmZsB9AywgQPT6Yy04DyinVaRyVzlYk2f75tuFcYps2BWJdtrFnH3g6gH9F"

BIT_DISPLAY_NAME = "Jeff BIT Account X01"
BIT_API_KEY = "ak-5fc6e4f8-6509-45dd-ada5-858a539b9d58"
BIT_SECRET_KEY = "f4Mnb68zUVFSJWm8tXO62m5cjjbbApFjQQkZ1tudu4qg4PFyYFlTrElNPK7vnksz"

SUCCESS_MESSAGE = "Successfully connected CEX"


class TestCexConnectionScenario1:
    """Test Case 01: Connect Binance Account Successfully – Valid Scenario"""

    def test_connect_binance_successfully(self, cex_connection_page):
        """Success toast is visible and contains the expected message after connecting Binance."""
        cex_connection_page.open_profile()
        cex_connection_page.go_to_exchange_tab()
        cex_connection_page.click_connect_exchange()
        cex_connection_page.fill_connection_form(
            BINANCE_DISPLAY_NAME, BINANCE_API_KEY, BINANCE_SECRET_KEY
        )
        cex_connection_page.submit_connection()

        assert cex_connection_page.is_success_toast_visible(), (
            "A success toast should be visible after connecting a Binance account"
        )
        assert SUCCESS_MESSAGE in cex_connection_page.get_success_text(), (
            f"Expected toast to contain '{SUCCESS_MESSAGE}'"
        )


class TestCexConnectionScenario2:
    """Test Case 02: Connect BIT Account Successfully – Valid Scenario"""

    def test_connect_bit_successfully(self, cex_connection_page):
        """Success toast is visible and contains the expected message after connecting BIT."""
        cex_connection_page.open_profile()
        cex_connection_page.go_to_exchange_tab()
        cex_connection_page.click_connect_exchange()
        cex_connection_page.select_bit_exchange()
        cex_connection_page.fill_connection_form(
            BIT_DISPLAY_NAME, BIT_API_KEY, BIT_SECRET_KEY
        )
        cex_connection_page.submit_connection()

        assert cex_connection_page.is_success_toast_visible(), (
            "A success toast should be visible after connecting a BIT account"
        )
        assert SUCCESS_MESSAGE in cex_connection_page.get_success_text(), (
            f"Expected toast to contain '{SUCCESS_MESSAGE}'"
        )
