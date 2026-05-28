import re
import time

from selenium.common.exceptions import WebDriverException

from business.login_flow import LoginFlow
from common.allure_util import step
from common.logger import get_logger
from core.exceptions import ElementOperationError, UnsupportedPlatformError
from pages.android.appropriateness_assessment_page import AndroidAppropriatenessAssessmentPage
from pages.android.home_page import AndroidHomePage
from pages.android.instrument_detail_page import AndroidInstrumentDetailPage
from pages.android.login_page import AndroidLoginPage
from pages.android.mine_page import AndroidMinePage
from pages.android.order_page import AndroidOrderPage
from pages.android.pro_account_intro_page import AndroidProAccountIntroPage
from pages.android.trade_page import AndroidTradePage


logger = get_logger(__name__)


class AppStateFlow:
    def __init__(self, driver, platform):
        if platform != "android":
            raise UnsupportedPlatformError(f"App state flow is not implemented for platform: {platform}")

        self.driver = driver
        self.platform = platform
        self.app_package = self._resolve_app_package()
        self.login_flow = LoginFlow(driver, platform)
        self.login_page = AndroidLoginPage(driver)
        self.home_page = AndroidHomePage(driver)
        self.trade_page = AndroidTradePage(driver)
        self.mine_page = AndroidMinePage(driver)
        self.instrument_detail_page = AndroidInstrumentDetailPage(driver)
        self.order_page = AndroidOrderPage(driver)
        self.pro_account_intro_page = AndroidProAccountIntroPage(driver)
        self.appropriateness_page = AndroidAppropriatenessAssessmentPage(driver)

    def ensure_logged_out(self):
        with step("Ensure app is logged out before login testcase"):
            self._switch_native_safely()
            self.login_page.close_country_picker_if_visible(timeout=3)
            if self.is_logged_out():
                return

            self.recover_to_main_app()
            if not self.is_logged_out():
                self.logout_current_account()

    def ensure_logged_in(self, account_data, case_data=None):
        case_data = case_data or {}
        with step(f"Ensure logged in as account_type={account_data.get('account_type')}"):
            self._switch_native_safely()
            self.recover_to_main_app()

            if self.is_logged_in():
                if self.is_current_account(account_data):
                    return
                self.logout_current_account()

            self.login_flow.login(
                account_data["login_type"],
                account_data["account"],
                account_data.get("password", ""),
                auth_method=case_data.get("auth_method", "password"),
                verification_code=case_data.get("verification_code"),
                use_prefilled_password=case_data.get("use_prefilled_password", False),
                post_login=case_data.get("post_login"),
                country_code=account_data.get("phone_country_code"),
                country_name=account_data.get("phone_country_name"),
            )

    def is_logged_out(self):
        return self.is_on_login_page() or self.login_page.is_on_onboarding_page(timeout=1)

    def is_on_login_page(self):
        return self.login_page.is_on_login_page(timeout=1)

    def is_main_tab_page(self):
        return self.home_page.is_loaded(timeout=1) or self.trade_page.is_loaded(timeout=1)

    def is_logged_in(self):
        return (
            self.is_main_tab_page()
            or self.mine_page.is_loaded(timeout=1)
            or self.instrument_detail_page.is_loaded(timeout=1)
            or self.order_page.is_loaded(timeout=1)
            or self.order_page.is_leverage_selector_visible(timeout=1)
            or self.pro_account_intro_page.is_loaded(timeout=1)
            or self.appropriateness_page.is_loaded(timeout=1)
        )

    def is_current_account(self, account_data):
        current_identifier = self.current_account_identifier()
        if not current_identifier:
            logger.info("Current account cannot be determined; relogin is required")
            return False

        expected = account_data.get("username") or account_data.get("account")
        return self._normalize_identifier(expected) in self._normalize_identifier(current_identifier)

    def current_account_identifier(self):
        if not self.is_logged_in():
            return None

        if not self.mine_page.is_loaded(timeout=1):
            self._open_personal_center_from_main_tab()

        texts = self.mine_page.visible_texts()
        if self.mine_page.is_loaded(timeout=1):
            self.mine_page.close(timeout=5)

        candidates = [
            text
            for text in texts
            if "@" in text or re.search(r"\d{4,}", text)
        ]
        return " ".join(candidates) or None

    def logout_current_account(self):
        with step("Clear current login state"):
            self._clear_app_data()
            self.login_page.wait_until(
                self.is_logged_out,
                timeout=25,
                message="App should be logged out after clearing login state",
            )

    def recover_to_main_app(self):
        with step("Recover app to login or main tab page"):
            self._switch_native_safely()
            for _ in range(10):
                if self.login_page.close_bonus_popup_if_visible(timeout=3):
                    continue

                if self.login_page.close_country_picker_if_visible(timeout=3):
                    continue

                if self.is_logged_out() or self.is_main_tab_page():
                    return

                if self.pro_account_intro_page.is_loaded(timeout=1):
                    self.pro_account_intro_page.close(timeout=5)
                    continue

                if self.appropriateness_page.is_loaded(timeout=1):
                    self.appropriateness_page.close(timeout=5)
                    continue

                if self.order_page.is_leverage_selector_visible(timeout=1):
                    self.order_page.close_leverage_selector(timeout=5)
                    continue

                if self.order_page.is_loaded(timeout=1):
                    self.order_page.close_full_order(timeout=5)
                    continue

                if self.instrument_detail_page.is_loaded(timeout=1):
                    self.instrument_detail_page.close(timeout=5)
                    continue

                if self.mine_page.is_loaded(timeout=1):
                    self.mine_page.close(timeout=5)
                    continue

                self.home_page.press_back()

            if not (self.is_logged_out() or self.is_main_tab_page()):
                raise ElementOperationError("Failed to recover app to login or main tab page")

    def _open_personal_center_from_main_tab(self):
        if not self.home_page.is_loaded(timeout=1):
            if not self.is_main_tab_page():
                self.recover_to_main_app()
            self.home_page.open_home_tab(timeout=5)
        self.home_page.wait_for_loaded(timeout=10)
        self.home_page.open_personal_center()
        self.mine_page.wait_for_loaded(timeout=10)

    def _clear_app_data(self):
        try:
            self.driver.terminate_app(self.app_package)
        except WebDriverException as exc:
            logger.info("terminate_app before clearApp failed, continuing: %s", exc)

        try:
            self.driver.execute_script("mobile: clearApp", {"appId": self.app_package})
        except WebDriverException:
            self.driver.execute_script(
                "mobile: shell",
                {"command": "pm", "args": ["clear", self.app_package]},
            )

        try:
            self.driver.activate_app(self.app_package)
        except WebDriverException:
            self.driver.launch_app()
        time.sleep(2)
        self._switch_native_safely()

    def _switch_native_safely(self):
        try:
            if self.driver.current_context != "NATIVE_APP":
                self.driver.switch_to.context("NATIVE_APP")
        except WebDriverException:
            pass

    def _resolve_app_package(self):
        capabilities = getattr(self.driver, "capabilities", {}) or {}
        return (
            capabilities.get("appium:appPackage")
            or capabilities.get("appPackage")
            or "x.mitrade.dev"
        )

    @staticmethod
    def _normalize_identifier(value):
        return re.sub(r"[^a-z0-9]+", "", (value or "").lower())
