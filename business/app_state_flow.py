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
    PAGE_LOGIN = "login"
    PAGE_MAIN_TAB = "main_tab"
    PAGE_PERMISSION_DIALOG = "permission_dialog"
    PAGE_BONUS_POPUP = "bonus_popup"
    PAGE_COUNTRY_PICKER = "country_picker"
    PAGE_PRO_ACCOUNT_INTRO = "pro_account_intro"
    PAGE_APPROPRIATENESS = "appropriateness_assessment"
    PAGE_LEAVE_CONFIRM = "leave_confirm"
    PAGE_LEVERAGE_SELECTOR = "leverage_selector"
    PAGE_ORDER = "order"
    PAGE_INSTRUMENT_DETAIL = "instrument_detail"
    PAGE_MINE = "mine"
    PAGE_H5 = "h5"
    PAGE_UNKNOWN = "unknown"

    SYSTEM_PERMISSION_DENY_BUTTONS = (
        ("xpath", "//android.widget.Button[@text='Don\u2019t allow']"),
        ("xpath", "//android.widget.Button[@text=\"Don't allow\"]"),
        ("xpath", "//android.widget.Button[@text='Deny']"),
        ("xpath", "//android.widget.Button[@text='拒绝']"),
    )
    H5_LEAVE_CONFIRM_TEXTS = (
        "Do you wish to leave?",
        "您确定要离开吗？",
    )
    H5_LEAVE_BUTTONS = (
        ("xpath", "//android.widget.Button[@text='Leave']"),
        ("xpath", "//android.widget.TextView[@text='Leave']"),
        ("xpath", "//android.widget.Button[@text='离开']"),
        ("xpath", "//android.widget.TextView[@text='离开']"),
    )

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

    def ensure_logged_in(self, account_data, case_data=None, force_relogin=False):
        case_data = case_data or {}
        login_type = account_data["login_type"]
        with step(f"Ensure logged in as account_type={account_data.get('account_type')}"):
            logger.info("当前 case_id: %s", case_data.get("case_id"))
            logger.info("当前用例 account_type: %s", account_data.get("account_type"))
            logger.info("登录模式: %s", login_type)
            logger.info("login_type=%s", login_type)
            logger.info("force_relogin=%s", force_relogin)
            if login_type == "phone":
                logger.info("使用的国家区号: %s", account_data.get("phone_country_code"))

            self._switch_native_safely()
            self.recover_to_main_app()
            recovered_page_type = self._classify_current_page()
            logger.info("当前页面类型: %s", recovered_page_type)

            logged_in = self.is_logged_in()
            logger.info("是否检测到未登录: %s", not logged_in)

            should_relogin = False
            if logged_in:
                if force_relogin:
                    logger.info("当前用例要求重新登录，先退出现有登录态")
                    should_relogin = True
                elif self.is_current_account(account_data):
                    logger.info("当前登录账号匹配 account_type=%s，复用登录态", account_data.get("account_type"))
                    logger.info("是否退出重登: %s", False)
                    logger.info("是否执行退出登录: %s", False)
                    self._log_current_main_page()
                    return
                else:
                    logger.info("无法确认当前账号匹配 account_type=%s，执行重新登录", account_data.get("account_type"))
                    should_relogin = True

            logger.info("是否退出重登: %s", should_relogin)
            logger.info("是否执行退出登录: %s", should_relogin)
            if should_relogin:
                logger.info("退出当前账号")
                self.logout_current_account()
                logger.info("退出当前账号或确认当前未登录: 已退出当前账号")
            else:
                logger.info("退出当前账号或确认当前未登录: 当前未登录")
            logger.info("回到登录页: %s", self.is_logged_out())

            country_code = account_data.get("phone_country_code") if login_type == "phone" else None
            country_name = account_data.get("phone_country_name") if login_type == "phone" else None
            self.login_flow.login(
                login_type,
                account_data["account"],
                account_data.get("password", ""),
                auth_method=case_data.get("auth_method", "password"),
                verification_code=case_data.get("verification_code"),
                use_prefilled_password=case_data.get("use_prefilled_password", False),
                post_login=case_data.get("post_login"),
                country_code=country_code,
                country_name=country_name,
                account_type=account_data.get("account_type"),
            )
            self.login_page.close_common_popups_if_exists(rounds=3, name="post_login_popup")
            self._log_current_main_page()

    def is_logged_out(self):
        return self._classify_current_page() == self.PAGE_LOGIN

    def is_on_login_page(self):
        return self.login_page.is_on_login_page(timeout=1)

    def is_main_tab_page(self):
        return self._classify_current_page() == self.PAGE_MAIN_TAB

    def is_logged_in(self):
        return self._classify_current_page() in (
            self.PAGE_MAIN_TAB,
            self.PAGE_MINE,
            self.PAGE_INSTRUMENT_DETAIL,
            self.PAGE_ORDER,
            self.PAGE_LEVERAGE_SELECTOR,
            self.PAGE_PRO_ACCOUNT_INTRO,
            self.PAGE_APPROPRIATENESS,
            self.PAGE_H5,
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
            self.dismiss_system_permission_dialog_if_visible(timeout=1)
            self.login_page.wait_until(
                self._is_logged_out_after_cleanup,
                timeout=25,
                message="App should be logged out after clearing login state",
            )

    def recover_to_main_app(self):
        with step("Recover app to login or main tab page"):
            self._switch_native_safely()
            last_page_type = None
            for _ in range(8):
                self.login_page.close_common_popups_if_exists(rounds=2, name="recover_popup")
                page_type = self._classify_current_page()
                if page_type != last_page_type:
                    logger.info("恢复前当前页面类型: %s", page_type)
                    last_page_type = page_type

                if page_type in (self.PAGE_LOGIN, self.PAGE_MAIN_TAB):
                    return

                if page_type == self.PAGE_PERMISSION_DIALOG:
                    if not self.dismiss_system_permission_dialog_if_visible(timeout=0.5):
                        self.home_page.press_back()
                    continue

                if page_type == self.PAGE_BONUS_POPUP:
                    self.login_page.close_bonus_popup_if_visible(timeout=3)
                    continue

                if page_type == self.PAGE_COUNTRY_PICKER:
                    self.login_page.close_country_picker_if_visible(timeout=3)
                    continue

                if page_type == self.PAGE_LEAVE_CONFIRM:
                    if not self._confirm_h5_leave_if_visible(timeout=1):
                        self.home_page.press_back()
                    continue

                if page_type == self.PAGE_PRO_ACCOUNT_INTRO:
                    self.pro_account_intro_page.close(timeout=5)
                    continue

                if page_type == self.PAGE_APPROPRIATENESS:
                    self.appropriateness_page.close(timeout=5)
                    continue

                if page_type == self.PAGE_LEVERAGE_SELECTOR:
                    self.order_page.close_leverage_selector(timeout=5)
                    continue

                if page_type == self.PAGE_ORDER:
                    self.order_page.close_full_order(timeout=5)
                    continue

                if page_type == self.PAGE_INSTRUMENT_DETAIL:
                    self.instrument_detail_page.close(timeout=5)
                    continue

                if page_type == self.PAGE_MINE:
                    self.mine_page.close(timeout=5)
                    continue

                if page_type == self.PAGE_H5:
                    self._close_unknown_h5_page()
                    continue

                self.login_page.close_common_popups_if_exists(rounds=2, name="unknown_page_popup")
                page_type = self._classify_current_page()
                if page_type in (self.PAGE_LOGIN, self.PAGE_MAIN_TAB):
                    return

                self.home_page.press_back()

            self.login_page.close_common_popups_if_exists(rounds=2, name="recover_final_popup")
            page_type = self._classify_current_page()
            if page_type not in (self.PAGE_LOGIN, self.PAGE_MAIN_TAB):
                diagnostics = self.login_page.capture_diagnostics("recover_unknown_page")
                raise ElementOperationError(
                    "Failed to recover app to login or main tab page. "
                    f"current_page_type={page_type}. {diagnostics}"
                )

    def _open_personal_center_from_main_tab(self):
        if not self.home_page.is_loaded(timeout=1):
            if not self.is_main_tab_page():
                self.recover_to_main_app()
            self.home_page.open_home_tab(timeout=5)
        self.home_page.wait_for_loaded(timeout=10)
        self.home_page.open_personal_center()
        self.mine_page.wait_for_loaded(timeout=10)

    def _classify_current_page(self):
        source = self._current_page_source()

        if self._source_contains(source, *self.H5_LEAVE_CONFIRM_TEXTS):
            return self.PAGE_LEAVE_CONFIRM
        if self._source_contains(source, "Don\u2019t allow", "Don't allow", "Deny", "拒绝"):
            return self.PAGE_PERMISSION_DIALOG
        if self._source_contains(source, "x.mitrade.dev:id/btnNegative", "恭喜您获得"):
            return self.PAGE_BONUS_POPUP
        if self._source_contains(source, "x.mitrade.dev:id/et_search", "选择国家/地区"):
            return self.PAGE_COUNTRY_PICKER
        if self._source_contains(source, "x.mitrade.dev:id/tvLoginTitle", "x.mitrade.dev:id/tvLoginAccount"):
            return self.PAGE_LOGIN
        if self._source_contains(source, "Open Pro Account", "Leverage up to 200:1"):
            return self.PAGE_PRO_ACCOUNT_INTRO
        if self._source_contains(source, "Appropriateness assessment", "Employment Status"):
            return self.PAGE_APPROPRIATENESS
        if self._source_contains(source, "Select Leverage", "x.mitrade.dev:id/rvLeverages"):
            return self.PAGE_LEVERAGE_SELECTOR
        if self._source_contains(source, "x.mitrade.dev:id/tvOpenPositionTitle"):
            return self.PAGE_ORDER
        if self._source_contains(source, "x.mitrade.dev:id/flDetailContent"):
            return self.PAGE_INSTRUMENT_DETAIL
        if self._source_contains(source, "x.mitrade.dev:id/flMineRoot", "x.mitrade.dev:id/mavAccountView"):
            return self.PAGE_MINE
        if self._source_contains(source, "x.mitrade.dev:id/webViewLty") or self._is_webview_context():
            return self.PAGE_H5
        if self._source_contains(
            source,
            "x.mitrade.dev:id/ivHomeLogo",
            "x.mitrade.dev:id/tvMarket",
            "x.mitrade.dev:id/rbTabHome",
            "x.mitrade.dev:id/rbTabTrade",
            "Market",
            "Popular",
            "Trade",
            "Home",
            "Positions",
            "Discover",
        ):
            return self.PAGE_MAIN_TAB
        return self.PAGE_UNKNOWN

    def _current_page_source(self):
        try:
            return self.driver.page_source or ""
        except WebDriverException as exc:
            logger.debug("Failed to read page source for page classification: %s", exc)
            return ""

    @staticmethod
    def _source_contains(source, *fragments):
        return any(fragment and fragment in source for fragment in fragments)

    def _is_webview_context(self):
        try:
            return self.driver.current_context != "NATIVE_APP"
        except WebDriverException:
            return False

    def _close_unknown_h5_page(self):
        logger.info("关闭未知 H5 页面")
        self.home_page.press_back()
        self._confirm_h5_leave_if_visible(timeout=1)

    def _confirm_h5_leave_if_visible(self, timeout=1):
        for locator in self.H5_LEAVE_BUTTONS:
            if not self.login_page.is_element_visible(locator, timeout=timeout):
                continue
            logger.info("确认离开 H5 页面: %s", locator)
            self.login_page.click(locator, timeout=3)
            return True
        return False

    def current_main_page_name(self):
        source = self._current_page_source()
        if self._source_contains(source, "x.mitrade.dev:id/ivHomeLogo", "x.mitrade.dev:id/rbTabHome"):
            return "Home"
        if self._source_contains(source, "x.mitrade.dev:id/tvMarket", "x.mitrade.dev:id/rbTabTrade"):
            return "Trade"
        if self._source_contains(source, "x.mitrade.dev:id/tvLoginTitle"):
            return "Login"
        if self._source_contains(source, "x.mitrade.dev:id/tvLoginAccount"):
            return "Onboarding"
        return "Unknown"

    def _log_current_main_page(self):
        logger.info("登录成功后进入的主页面: %s", self.current_main_page_name())

    def dismiss_system_permission_dialog_if_visible(self, timeout=1):
        for locator in self.SYSTEM_PERMISSION_DENY_BUTTONS:
            if not self.login_page.is_element_visible(locator, timeout=timeout):
                continue
            logger.info("关闭系统权限弹窗: %s", locator)
            self.login_page.click(locator, timeout=timeout)
            return True
        return False

    def _is_logged_out_after_cleanup(self):
        self.dismiss_system_permission_dialog_if_visible(timeout=1)
        return self.is_logged_out()

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
