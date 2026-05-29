import pytest


VALID_EMAIL = "roninx688@gmail.com"
VALID_PASSWORD = "0987654321a@A"
INVALID_PASSWORD = "0987654321a@a"


class TestLoginScenario1:
    """Scenario 1: Valid Login"""

    def test_valid_login_redirects_away_from_sign_in(self, login_page):
        """User is redirected away from /sign-in after a valid login."""
        login_page.login(VALID_EMAIL, VALID_PASSWORD)

        login_page.page.wait_for_url(
            lambda url: "/sign-in" not in url, timeout=15000
        )

        assert "/sign-in" not in login_page.get_current_url(), (
            "Expected to be redirected away from /sign-in after valid login"
        )

    def test_valid_login_lands_on_portfolio_overview(self, login_page):
        """User lands on the Portfolio / Overview page after valid login."""
        login_page.login(VALID_EMAIL, VALID_PASSWORD)

        login_page.page.wait_for_url(
            lambda url: "/sign-in" not in url, timeout=15000
        )

        current_url = login_page.get_current_url()
        assert "/portfolio" in current_url, (
            f"Expected /portfolio in URL after login, got: {current_url}"
        )

    def test_valid_login_no_error_toast(self, login_page):
        """No error toast is displayed after a successful login."""
        login_page.login(VALID_EMAIL, VALID_PASSWORD)

        login_page.page.wait_for_url(
            lambda url: "/sign-in" not in url, timeout=15000
        )

        assert not login_page.is_error_toast_visible(), (
            "Error toast should not be visible after a successful login"
        )


class TestLoginScenario2:
    """Scenario 2: Invalid Login"""

    def test_invalid_login_stays_on_sign_in_page(self, login_page):
        """User with invalid credentials remains on the /sign-in page."""
        login_page.login(VALID_EMAIL, INVALID_PASSWORD)

        login_page.page.wait_for_timeout(5000)

        assert "/sign-in" in login_page.get_current_url(), (
            "User should remain on /sign-in after invalid credentials"
        )

    def test_invalid_login_shows_error_toast(self, login_page):
        """An error toast is displayed after a failed login attempt."""
        login_page.login(VALID_EMAIL, INVALID_PASSWORD)

        login_page.error_toast.wait_for(state="visible", timeout=10000)

        assert login_page.is_error_toast_visible(), (
            "An error toast should be visible after invalid credentials"
        )

    def test_invalid_login_error_message_content(self, login_page):
        """Error toast contains a meaningful message about the failed login."""
        login_page.login(VALID_EMAIL, INVALID_PASSWORD)

        login_page.error_toast.wait_for(state="visible", timeout=10000)

        error_text = login_page.get_error_text()
        assert error_text.strip(), "Error toast text should not be empty"
