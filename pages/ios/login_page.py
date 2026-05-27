from core.base_page import BasePage


class IOSLoginPage(BasePage):
    ACCOUNT_INPUT = ("accessibility id", "usernameTextField")
    PASSWORD_INPUT = ("accessibility id", "passwordTextField")
    LOGIN_BUTTON = ("accessibility id", "loginButton")
    SUCCESS_MARKER = ("accessibility id", "homeView")
    ERROR_MESSAGE = ("accessibility id", "loginErrorMessage")

    def input_account(self, account, timeout=5):
        self.input_text(self.ACCOUNT_INPUT, account, timeout=timeout)

    def input_password(self, password, timeout=5):
        self.input_text(self.PASSWORD_INPUT, password, timeout=timeout)

    def tap_login_button(self, timeout=5):
        self.click(self.LOGIN_BUTTON, timeout=timeout)

    def tap_login(self, timeout=5):
        self.tap_login_button(timeout=timeout)

    def is_home_visible(self, timeout=5):
        return self.is_element_visible(self.SUCCESS_MARKER, timeout=timeout)

    def get_error_message(self):
        return self.get_text(self.ERROR_MESSAGE, timeout=5)
