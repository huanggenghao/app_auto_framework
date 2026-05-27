from selenium.common.exceptions import WebDriverException

from common.allure_util import step
from core.base_page import BasePage
from core.exceptions import ElementOperationError


class AndroidLoginPage(BasePage):
    DEFAULT_VERIFICATION_CODE = "123456"

    LOGIN_TITLE = ("id", "x.mitrade.dev:id/tvLoginTitle")
    ONBOARDING_LOGIN_TEXT = ("id", "x.mitrade.dev:id/tvLoginAccount")

    PHONE_TAB = (
        "xpath",
        "//*[@resource-id='x.mitrade.dev:id/llTabRoot' and .//*[@text='手机号码']]",
    )
    EMAIL_TAB = (
        "xpath",
        "//*[@resource-id='x.mitrade.dev:id/llTabRoot' and .//*[@text='邮箱']]",
    )

    PHONE_INPUT = ("id", "x.mitrade.dev:id/etPhone")
    EMAIL_INPUT_CANDIDATES = (
        ("id", "x.mitrade.dev:id/etCommonInput"),
        ("id", "x.mitrade.dev:id/etEmail"),
        ("id", "x.mitrade.dev:id/etEmailInput"),
        ("id", "x.mitrade.dev:id/etAccount"),
        ("id", "x.mitrade.dev:id/etPhone"),
        ("xpath", "//android.widget.EditText[@password='false']"),
    )
    PASSWORD_INPUT = ("id", "x.mitrade.dev:id/etPwdInput")
    PASSWORD_VISIBILITY_TOGGLE = ("id", "x.mitrade.dev:id/cbPwd")
    SWITCH_LOGIN_METHOD = ("id", "x.mitrade.dev:id/tvSwitchLoginMethod")
    GET_VERIFICATION_CODE_BUTTON = ("id", "x.mitrade.dev:id/tvGetPhoneCode")
    LOGIN_BUTTON = ("id", "x.mitrade.dev:id/btnLogin")
    ERROR_MESSAGE = ("xpath", "//*[contains(@resource-id, 'error') or contains(@text, '错误')]")

    VERIFY_TITLE = ("xpath", "//*[@resource-id='x.mitrade.dev:id/tvTitle' and @text='双重验证']")
    VERIFY_CODE_INPUT = ("id", "x.mitrade.dev:id/etVerifyCode")
    VERIFY_SUBMIT_BUTTON = ("id", "x.mitrade.dev:id/btnSubmit")

    KYC_WEBVIEW_CONTAINER = ("id", "x.mitrade.dev:id/webViewLty")
    KYC_PROFILE_TITLE = ("xpath", "//*[@text='个人资料']")
    KYC_CLOSE_BUTTON = (
        "xpath",
        "(//android.widget.TextView[@text='个人资料']/following::android.widget.Button)[2]",
    )
    KYC_CONFIRM_TITLE = ("xpath", "//*[@text='您确定要离开吗？']")
    KYC_LEAVE_BUTTON_CANDIDATES = (
        ("xpath", "//android.widget.Button[@text='离开']"),
        ("xpath", "//android.widget.TextView[@text='离开']"),
    )

    HOME_LOGO = ("id", "x.mitrade.dev:id/ivHomeLogo")
    HOME_TAB = ("id", "x.mitrade.dev:id/rbTabHome")

    def enter_login_page(self):
        with step("Enter Mitrade login page"):
            if self.is_on_login_page():
                return

            self._tap_onboarding_login_text()
            self.wait_for_visible(self.LOGIN_TITLE, timeout=10)

    def is_on_login_page(self, timeout=3):
        return self.is_element_visible(self.LOGIN_TITLE, timeout=timeout)

    def select_login_type(self, login_type, timeout=5):
        if login_type == "phone":
            self.click(self.PHONE_TAB, timeout=timeout)
            return
        if login_type == "email":
            self.click(self.EMAIL_TAB, timeout=timeout)
            return
        raise ValueError(f"Unsupported login_type: {login_type}")

    def input_account(self, login_type, account, timeout=5):
        if login_type == "phone":
            self.input_text(self.PHONE_INPUT, account, timeout=timeout)
            return
        if login_type == "email":
            self.input_text(
                self._resolve_email_input(timeout=timeout),
                account,
                timeout=timeout,
            )
            return
        raise ValueError(f"Unsupported login_type: {login_type}")

    def input_password(self, password, timeout=5):
        self.input_text(self.PASSWORD_INPUT, password, timeout=timeout)

    def enable_prefilled_password(self):
        with step("Enable demo prefilled password"):
            toggle = self.wait_for_visible(self.PASSWORD_VISIBILITY_TOGGLE, timeout=5)
            if toggle.get_attribute("checked") != "true":
                self.click(self.PASSWORD_VISIBILITY_TOGGLE, timeout=5)

    def tap_login_button(self, timeout=5):
        self.click(self.LOGIN_BUTTON, timeout=timeout)

    def tap_login(self, timeout=5):
        self.tap_login_button(timeout=timeout)

    def request_verification_code(self, timeout=5):
        self.click(self.GET_VERIFICATION_CODE_BUTTON, timeout=timeout)

    def input_verification_code(self, verification_code, timeout=5):
        self.input_text(self.VERIFY_CODE_INPUT, verification_code, timeout=timeout)

    def submit_two_factor_code(self, timeout=5):
        self.click(self.VERIFY_SUBMIT_BUTTON, timeout=timeout)

    def is_2fa_page_visible(self, timeout=3):
        return self.is_element_visible(self.VERIFY_CODE_INPUT, timeout=timeout) or self.is_element_visible(
            self.VERIFY_TITLE, timeout=1
        )

    def is_two_factor_page_visible(self, timeout=3):
        return self.is_2fa_page_visible(timeout=timeout)

    def is_kyc_entry_visible(self, timeout=3):
        return self.is_element_visible(self.KYC_PROFILE_TITLE, timeout=timeout) or self.is_element_visible(
            self.KYC_WEBVIEW_CONTAINER, timeout=1
        )

    def close_kyc(self, timeout=3):
        try:
            self.click(self.KYC_CLOSE_BUTTON, timeout=timeout)
        except ElementOperationError:
            self.tap_relative(0.93, 0.07)

    def is_kyc_leave_confirmation_visible(self, timeout=3):
        return self.is_element_visible(self.KYC_CONFIRM_TITLE, timeout=timeout)

    def confirm_leave_kyc(self):
        for locator in self.KYC_LEAVE_BUTTON_CANDIDATES:
            try:
                self.click(locator, timeout=2)
                return
            except ElementOperationError:
                continue
        self.tap_relative(0.50, 0.95)

    def get_error_message(self):
        return self.get_text(self.ERROR_MESSAGE, timeout=5)

    def is_home_visible(self, timeout=3):
        return self.is_element_visible(self.HOME_TAB, timeout=timeout) or self.is_element_visible(
            self.HOME_LOGO, timeout=1
        )

    def is_text_visible(self, text, timeout=3):
        return self.is_element_visible(self._text_contains_locator(text), timeout=timeout)

    def tap_text(self, text, timeout=5):
        self.click(self._text_contains_locator(text), timeout=timeout)

    def is_popup_visible(self, popup_texts, timeout=3):
        if isinstance(popup_texts, str):
            popup_texts = [popup_texts]
        return all(self.is_text_visible(text, timeout=timeout) for text in popup_texts)

    def tap_popup_button(self, button_text, timeout=5):
        self.tap_text(button_text, timeout=timeout)

    def _tap_onboarding_login_text(self):
        element = self.wait_for_visible(self.ONBOARDING_LOGIN_TEXT, timeout=5)

        try:
            rect = element.rect
            x = int(rect["x"] + rect["width"] * 0.82)
            y = int(rect["y"] + rect["height"] * 0.5)
            self.driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
        except WebDriverException:
            element.click()

    def _resolve_email_input(self, timeout=5):
        for locator in self.EMAIL_INPUT_CANDIDATES:
            try:
                self.wait_for_visible(
                    locator,
                    timeout=min(timeout, 2),
                    capture_on_timeout=False,
                )
                return locator
            except ElementOperationError:
                continue

        diagnostics = self.capture_diagnostics("email_input_not_found")
        raise ElementOperationError(
            f"No visible email input found after switching to email login. {diagnostics}"
        )

    def switch_auth_method_if_needed(self, auth_method):
        expected_switch_text = {
            "password": "密码登录",
            "verification_code": "验证码登录",
        }[auth_method]

        try:
            switch_button = self.wait_for_visible(
                self.SWITCH_LOGIN_METHOD,
                timeout=3,
                capture_on_timeout=False,
            )
        except ElementOperationError:
            return

        if switch_button.text == expected_switch_text:
            self.click(self.SWITCH_LOGIN_METHOD, timeout=5)

    def hide_keyboard_if_open(self):
        try:
            self.driver.hide_keyboard()
        except WebDriverException:
            pass

    def _hide_keyboard_if_open(self):
        self.hide_keyboard_if_open()

    @classmethod
    def _text_contains_locator(cls, text):
        return ("xpath", f"//*[contains(@text, {cls._xpath_literal(text)})]")

    @staticmethod
    def _xpath_literal(value):
        if "'" not in value:
            return f"'{value}'"
        if '"' not in value:
            return f'"{value}"'

        parts = value.split("'")
        return "concat(" + ', "\'", '.join(f"'{part}'" for part in parts) + ")"
