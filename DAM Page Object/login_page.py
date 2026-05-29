from playwright.sync_api import Page


class LoginPage:
    URL_PATH = "/sign-in"

    def __init__(self, page: Page):
        self.page = page
        self.email_input = page.locator('[data-testid="input-email"]')
        self.password_input = page.locator('[data-testid="input-password"]')
        self.sign_in_button = page.locator('[data-testid="sign-in-btn"]')
        # Toastify error toast uses role="alert" with the error theme class
        self.error_toast = page.locator('[role="alert"].Toastify__toast--error')

    def navigate(self, base_url: str):
        self.page.goto(f"{base_url}{self.URL_PATH}")
        self.page.wait_for_load_state("domcontentloaded")
        # Allow JS to mount and the Turnstile widget to resolve
        self.page.wait_for_timeout(3000)

    def login(self, email: str, password: str):
        self.email_input.fill(email)
        self.password_input.fill(password)
        self.sign_in_button.click()

    def get_current_url(self) -> str:
        return self.page.url

    def is_error_toast_visible(self) -> bool:
        return self.error_toast.is_visible()

    def get_error_text(self) -> str:
        return self.error_toast.inner_text()
