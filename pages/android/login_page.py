from selenium.common.exceptions import WebDriverException

from common.allure_util import step
from common.logger import get_logger
from core.base_page import BasePage
from core.exceptions import ElementOperationError


logger = get_logger(__name__)


class AndroidLoginPage(BasePage):
    DEFAULT_VERIFICATION_CODE = "123456"

    LOGIN_TITLE = ("id", "x.mitrade.dev:id/tvLoginTitle")
    ONBOARDING_LOGIN_TEXT = ("id", "x.mitrade.dev:id/tvLoginAccount")

    PHONE_TAB = ("xpath", "//*[@text='手机号码' or @text='Phone' or @text='Mobile']")
    EMAIL_TAB = ("xpath", "//*[@text='邮箱' or @text='Email']")

    PHONE_INPUT = ("id", "x.mitrade.dev:id/etPhone")
    PHONE_COUNTRY_SELECTOR = ("id", "x.mitrade.dev:id/csSelectRegisterCountry")
    PHONE_COUNTRY_TEXT = ("id", "x.mitrade.dev:id/tvCountryText")
    PHONE_COUNTRY_ARROW = ("id", "x.mitrade.dev:id/ivArrow")
    COUNTRY_PICKER_SEARCH = ("id", "x.mitrade.dev:id/et_search")
    COUNTRY_PICKER_CLOSE = ("id", "x.mitrade.dev:id/ivCloseDialog")
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
    BONUS_POPUP_TITLE = ("xpath", "//*[@text='恭喜您获得']")
    BONUS_POPUP_CONFIRM = ("id", "x.mitrade.dev:id/btnNegative")
    SYSTEM_PERMISSION_DENY_BUTTONS = (
        ("xpath", "//android.widget.Button[@text='Don\u2019t allow']"),
        ("xpath", "//android.widget.Button[@text=\"Don't allow\"]"),
        ("xpath", "//android.widget.Button[@text='Deny']"),
        ("xpath", "//android.widget.Button[@text='拒绝']"),
    )

    HOME_LOGO = ("id", "x.mitrade.dev:id/ivHomeLogo")
    HOME_TAB = ("id", "x.mitrade.dev:id/rbTabHome")

    def prepare_for_login(self, login_type, account_type=None):
        self.dismiss_system_permission_dialog_if_visible(timeout=0.5)
        self.close_bonus_popup_if_visible(timeout=2)
        self.close_country_picker_if_visible(timeout=2)
        self.enter_login_page(login_type=login_type, account_type=account_type)

    def enter_login_page(self, login_type=None, account_type=None):
        with step("Enter Mitrade login page"):
            if self.is_on_login_page():
                self._log_login_page_state("已在登录页", login_type, account_type)
                return

            self._log_login_page_state("进入登录页", login_type, account_type)
            try:
                self._tap_onboarding_login_text()
                self.wait_for_visible(self.LOGIN_TITLE, timeout=10)
            except ElementOperationError as exc:
                diagnostics = self.capture_diagnostics("enter_login_page_failed")
                raise ElementOperationError(
                    "Failed to enter login page. "
                    f"current_page={self.current_page_name()}, "
                    f"login_type={login_type}, account_type={account_type}. {diagnostics}"
                ) from exc

    def is_on_login_page(self, timeout=3):
        return self.is_element_visible(self.LOGIN_TITLE, timeout=timeout)

    def is_on_onboarding_page(self, timeout=3):
        return self.is_element_visible(self.ONBOARDING_LOGIN_TEXT, timeout=timeout)

    def is_country_picker_visible(self, timeout=3):
        return self.is_element_visible(
            self.COUNTRY_PICKER_SEARCH,
            timeout=timeout,
        ) or self.is_element_visible(
            (
                "xpath",
                "//*[@resource-id='x.mitrade.dev:id/tvTitle' and @text='选择国家/地区']",
            ),
            timeout=1,
        )

    def close_country_picker_if_visible(self, timeout=3):
        if not self.is_country_picker_visible(timeout=1):
            return False

        with step("Close country picker"):
            if self.is_element_visible(self.COUNTRY_PICKER_CLOSE, timeout=1):
                self.click(self.COUNTRY_PICKER_CLOSE, timeout=timeout)
            else:
                self.press_back()
            self.wait_until(
                lambda: not self.is_country_picker_visible(timeout=1),
                timeout=timeout,
                message="Country picker should be closed",
            )
        return True

    def select_phone_country_if_needed(self, country_code=None, country_name=None, timeout=5):
        if not country_code:
            return

        expected_code = self._normalize_country_code(country_code)
        if self.is_element_visible(self.PHONE_COUNTRY_TEXT, timeout=1):
            current_code = self.get_text(self.PHONE_COUNTRY_TEXT, timeout=2)
            if current_code == expected_code:
                return

        with step(f"Select phone country: {country_name or expected_code} {expected_code}"):
            self.open_phone_country_picker(timeout=timeout)
            self.input_text(
                self.COUNTRY_PICKER_SEARCH,
                self._country_search_text(expected_code),
                timeout=timeout,
            )
            self.hide_keyboard_if_open()
            self.click(self._country_code_option_locator(expected_code), timeout=timeout)
            self.wait_until(
                lambda: self.get_text(self.PHONE_COUNTRY_TEXT, timeout=2) == expected_code,
                timeout=timeout,
                message=f"Phone country should be selected: {expected_code}",
            )

    def open_phone_country_picker(self, timeout=5):
        locators = (
            self.PHONE_COUNTRY_SELECTOR,
            self.PHONE_COUNTRY_TEXT,
            self.PHONE_COUNTRY_ARROW,
        )
        last_error = None
        for locator in locators:
            try:
                self.click(locator, timeout=timeout)
                if self.is_country_picker_visible(timeout=1):
                    self.wait_for_visible(self.COUNTRY_PICKER_SEARCH, timeout=timeout)
                    return
            except ElementOperationError as exc:
                last_error = exc

        raise ElementOperationError(
            f"Country picker did not open from country selector elements. Last error={last_error}"
        )

    def select_login_type(self, login_type, timeout=5, account_type=None):
        if login_type == "phone":
            self._tap_login_type_tab(
                login_type,
                self.PHONE_TAB,
                timeout=timeout,
                account_type=account_type,
            )
            return
        if login_type == "email":
            self._tap_login_type_tab(
                login_type,
                self.EMAIL_TAB,
                timeout=timeout,
                account_type=account_type,
            )
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

    def is_bonus_popup_visible(self, timeout=3):
        return self.is_element_visible(self.BONUS_POPUP_TITLE, timeout=timeout) or self.is_element_visible(
            self.BONUS_POPUP_CONFIRM, timeout=1
        )

    def close_bonus_popup_if_visible(self, timeout=3):
        if not self.is_bonus_popup_visible(timeout=1):
            return False

        with step("Close post-login bonus popup"):
            self.click(self.BONUS_POPUP_CONFIRM, timeout=timeout)
            self.wait_until(
                lambda: not self.is_bonus_popup_visible(timeout=1),
                timeout=timeout,
                message="Post-login bonus popup should be closed",
            )
        return True

    def dismiss_system_permission_dialog_if_visible(self, timeout=1):
        for locator in self.SYSTEM_PERMISSION_DENY_BUTTONS:
            if not self.is_element_visible(locator, timeout=timeout):
                continue
            logger.info("关闭系统权限弹窗: %s", locator)
            self.click(locator, timeout=3)
            return True
        return False

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

    def _tap_login_type_tab(self, login_type, locator, timeout=5, account_type=None):
        with step(f"Select login type tab: {login_type}"):
            logger.info(
                "点击%s tab: current_page=%s, login_type=%s, account_type=%s",
                self._login_type_label(login_type),
                self.current_page_name(),
                login_type,
                account_type,
            )
            try:
                self._tap_visible_or_parent(locator, timeout=timeout)
                return
            except ElementOperationError as exc:
                diagnostics = self.capture_diagnostics(f"{login_type}_login_tab_not_found")
                raise ElementOperationError(
                    "Failed to select login tab. "
                    f"current_page={self.current_page_name()}, "
                    f"login_type={login_type}, account_type={account_type}, "
                    f"locator={locator}. {diagnostics}"
                ) from exc

    def _tap_visible_or_parent(self, locator, timeout=5):
        element = self.wait_for_visible(locator, timeout=timeout)
        try:
            element.click()
            return
        except WebDriverException:
            logger.debug("Visible element click failed, fallback to coordinate tap: %s", locator)

        try:
            rect = element.rect
            self.tap_coordinates(
                rect["x"] + rect["width"] / 2,
                rect["y"] + rect["height"] / 2,
            )
            return
        except WebDriverException:
            logger.debug("Coordinate tap failed, fallback to parent click: %s", locator)

        parent_locator = (locator[0], f"({locator[1]})/..")
        parent = self.wait_for_visible(parent_locator, timeout=1)
        try:
            parent.click()
        except WebDriverException as exc:
            diagnostics = self.capture_diagnostics("tap_login_tab_parent_failed")
            raise ElementOperationError(
                f"Visible login tab cannot be clicked: {locator}. {diagnostics}"
            ) from exc

    def current_page_name(self):
        try:
            source = self.driver.page_source or ""
        except WebDriverException:
            return "Unknown"
        if "x.mitrade.dev:id/tvLoginTitle" in source:
            return "Login"
        if "x.mitrade.dev:id/tvLoginAccount" in source:
            return "Onboarding"
        if "x.mitrade.dev:id/et_search" in source or "选择国家/地区" in source:
            return "CountryPicker"
        if "x.mitrade.dev:id/btnNegative" in source or "恭喜您获得" in source:
            return "BonusPopup"
        if "x.mitrade.dev:id/ivHomeLogo" in source or "x.mitrade.dev:id/rbTabHome" in source:
            return "Home"
        if "x.mitrade.dev:id/tvMarket" in source or "x.mitrade.dev:id/rbTabTrade" in source:
            return "Trade"
        return "Unknown"

    def _log_login_page_state(self, action, login_type=None, account_type=None):
        logger.info(
            "%s: current_page=%s, login_type=%s, account_type=%s",
            action,
            self.current_page_name(),
            login_type,
            account_type,
        )

    @staticmethod
    def _login_type_label(login_type):
        return "手机号" if login_type == "phone" else "邮箱"

    def _resolve_email_input(self, timeout=5):
        for locator in self.EMAIL_INPUT_CANDIDATES:
            try:
                self.wait_for_visible(
                    locator,
                    timeout=min(timeout, 1),
                    capture_on_timeout=False,
                    log_attempt=False,
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
                timeout=1,
                capture_on_timeout=False,
                log_attempt=False,
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

    @classmethod
    def _country_code_option_locator(cls, country_code):
        return (
            "xpath",
            "//*[@resource-id='x.mitrade.dev:id/tvNumber' "
            f"and @text={cls._xpath_literal(country_code)}]/ancestor::android.widget.RelativeLayout[1]",
        )

    @staticmethod
    def _normalize_country_code(country_code):
        country_code = str(country_code).strip()
        if country_code.startswith("+"):
            return country_code
        return f"+{country_code}"

    @staticmethod
    def _country_search_text(country_code):
        return str(country_code).strip().lstrip("+")
