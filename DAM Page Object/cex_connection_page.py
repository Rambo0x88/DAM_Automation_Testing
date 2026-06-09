from playwright.sync_api import Page, expect


class CexConnectionPage:
    def __init__(self, page: Page):
        self.page = page
        # Avatar: the header menu trigger that is NOT the EN language selector
        self.avatar_button = page.locator(
            "button[aria-haspopup='menu'][class*='px-3 py-2.5']"
        ).filter(has_not_text="EN")
        self.profile_menu_item = page.locator("[role='menuitem']:has-text('Profile')")
        self.exchange_tab = page.locator("[role='tab']:has-text('Exchange')")
        self.connect_exchange_button = page.locator("button:has-text('Connect Exchange')")
        self.binance_button = page.locator("button:has-text('Binance')")
        self.bit_button = page.get_by_role("button", name="BIT", exact=True)
        self.display_name_input = page.locator('[data-testid="input-displayName"]')
        self.api_key_input = page.locator('[data-testid="input-apiKey"]')
        self.secret_key_input = page.locator('[data-testid="input-apiSecret"]')
        self.connect_button = page.locator("button[type='submit']:has-text('Connect')")
        self.success_toast = page.locator('[role="alert"].Toastify__toast--success')

    def _dismiss_any_dialog(self):
        overlay = self.page.locator("[data-slot='alert-dialog-overlay'], [role='alertdialog']")
        if overlay.count() > 0 and overlay.first.is_visible():
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(500)

    def open_profile(self):
        self._dismiss_any_dialog()
        self.avatar_button.wait_for(state="visible", timeout=15000)
        self.avatar_button.click()
        self.profile_menu_item.wait_for(state="visible", timeout=5000)
        self.profile_menu_item.click()
        self.page.wait_for_url("**/account-settings", timeout=10000)
        self.page.wait_for_load_state("networkidle")

    def go_to_exchange_tab(self):
        self.exchange_tab.wait_for(state="visible", timeout=10000)
        self.exchange_tab.click()
        self.connect_exchange_button.wait_for(state="visible", timeout=10000)

    def select_bit_exchange(self):
        self.bit_button.click()

    def click_connect_exchange(self):
        self.connect_exchange_button.click()
        self.display_name_input.wait_for(state="visible", timeout=5000)

    def fill_connection_form(self, display_name: str, api_key: str, secret_key: str):
        self.display_name_input.fill(display_name)
        self.api_key_input.fill(api_key)
        self.secret_key_input.fill(secret_key)

    def submit_connection(self):
        expect(self.connect_button).to_be_enabled(timeout=5000)
        self.connect_button.click()

    def is_success_toast_visible(self) -> bool:
        self.success_toast.wait_for(state="visible", timeout=15000)
        return self.success_toast.is_visible()

    def get_success_text(self) -> str:
        return self.success_toast.inner_text()

    def delete_exchange_by_name(self, display_name: str):
        """Navigate to the Exchange tab and delete a connection by display name. No-op if not found."""
        self.page.goto("https://dam-sit.mqbc21.com/account-settings")
        self.page.wait_for_load_state("networkidle")
        self.exchange_tab.wait_for(state="visible", timeout=10000)
        self.exchange_tab.click()
        # Wait for the exchange table rows to load
        self.page.locator("tr").first.wait_for(state="visible", timeout=10000)
        self.page.wait_for_timeout(500)

        row = self.page.locator("tr").filter(has_text=display_name)
        if row.count() == 0:
            return

        delete_btn = row.locator("button[aria-label='Delete Exchange Account']")
        delete_btn.click()
        # Confirmation uses an alert-dialog (Radix alertdialog role)
        confirm = self.page.get_by_role("alertdialog").get_by_role("button", name="Delete")
        confirm.wait_for(state="visible", timeout=5000)
        confirm.click()
        # Wait for the alert-dialog overlay to disappear before returning
        self.page.locator("[data-slot='alert-dialog-overlay']").wait_for(state="hidden", timeout=5000)
        self.page.wait_for_timeout(500)
