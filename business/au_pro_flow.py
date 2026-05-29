from common.allure_util import step
from common.logger import get_logger
from core.exceptions import ElementOperationError, UnsupportedPlatformError
from business.app_state_flow import AppStateFlow
from pages.android.appropriateness_assessment_page import AndroidAppropriatenessAssessmentPage
from pages.android.home_page import AndroidHomePage
from pages.android.instrument_detail_page import AndroidInstrumentDetailPage
from pages.android.mine_page import AndroidMinePage
from pages.android.order_page import AndroidOrderPage
from pages.android.pro_account_intro_page import AndroidProAccountIntroPage
from pages.android.trade_page import AndroidTradePage


logger = get_logger(__name__)


class AuProFlow:
    def __init__(self, driver, platform):
        if platform != "android":
            raise UnsupportedPlatformError(f"AU PRO flow is not implemented for platform: {platform}")

        self.app_state_flow = AppStateFlow(driver, platform)
        self.home_page = AndroidHomePage(driver)
        self.mine_page = AndroidMinePage(driver)
        self.trade_page = AndroidTradePage(driver)
        self.instrument_detail_page = AndroidInstrumentDetailPage(driver)
        self.order_page = AndroidOrderPage(driver)
        self.pro_account_intro_page = AndroidProAccountIntroPage(driver)
        self.appropriateness_page = AndroidAppropriatenessAssessmentPage(driver)

    def login_as(self, account_data, case_data):
        with step("Login as AU PRO scenario account"):
            self.app_state_flow.ensure_logged_in(account_data, case_data)

    def assert_au_pro_case(self, case_data, ensure_login=True):
        if ensure_login:
            self.login_as(case_data["account"], case_data)

        case_id = case_data.get("case_id")
        scenario = case_data.get("scenario") or self._scenario_from_case_id(case_id)
        logger.info("当前 case_id: %s", case_id)
        logger.info("当前 scenario: %s", scenario)

        case_completed = False
        try:
            if scenario == "card_visible":
                self.assert_card_visible_scenario(case_data)
                case_completed = True
                return

            if scenario == "leverage_entry_visible":
                self.assert_leverage_entry_visible_scenario(case_data)
                case_completed = True
                return

            if scenario == "leverage_entry_opens_assessment":
                self.assert_leverage_entry_opens_assessment_scenario(case_data)
                case_completed = True
                return

            raise ValueError(f"Unsupported AU PRO scenario: case_id={case_id}, scenario={scenario}")
        finally:
            try:
                self._teardown_recover_to_main_tab_area(scenario, case_id)
            except Exception as exc:
                diagnostics = self.home_page.capture_diagnostics("au_pro_teardown_recover_failed")
                if case_completed:
                    logger.warning(
                        "[TEARDOWN][WARNING] 页面恢复失败但业务断言已完成: %s. %s",
                        exc,
                        diagnostics,
                    )
                else:
                    logger.warning(
                        "[TEARDOWN][WARNING] 页面恢复失败，业务异常将继续抛出: %s. %s",
                        exc,
                        diagnostics,
                    )

    def assert_au_pro_card(self, case_data):
        self.login_as(case_data["account"], case_data)
        self.assert_au_pro_card_visible(case_data["expected"])

    def assert_au_pro_card_visible(self, expect_data):
        if isinstance(expect_data, dict) and not expect_data.get("au_pro_card_visible", True):
            return

        if isinstance(expect_data, dict):
            expected_texts = expect_data.get("texts", expect_data)
        else:
            expected_texts = expect_data

        with step("Assert AU PRO card content is visible"):
            assert self.is_au_pro_card_visible(expected_texts), (
                "Expected AU PRO card content to be visible"
            )

    def assert_card_visible_scenario(self, case_data):
        logger.info("[CASE] au_pro_card_visible: start Mine -> assert AU Pro card visible -> finish case")
        self.open_mine_page()
        self.assert_au_pro_card_visible(case_data["expected"])
        logger.info("[CASE] au_pro_card_visible: finish case")

    def is_au_pro_card_visible(self, expected_texts):
        if not self.mine_page.is_loaded(timeout=3):
            self._open_home_from_any_authenticated_page()
            self.home_page.open_personal_center()
        return self.mine_page.is_au_pro_card_visible(expected_texts)

    def assert_leverage_entry_visible_scenario(self, case_data):
        expected = case_data["expected"]
        trade_data = case_data["trade"]
        instrument_name = trade_data.get("instrument", "Gold")
        leverage = trade_data.get("leverage", "20X")
        expected_text = expected["leverage_pro_text"]

        logger.info(
            "[CASE] au_pro_leverage_entry_visible: start Trade -> %s -> Buy -> %s -> assert %s -> finish case",
            instrument_name,
            leverage,
            expected_text,
        )
        with step("Assert AU PRO leverage entry is visible"):
            self.open_leverage_selector(instrument_name, leverage)
            assert self.order_page.is_pro_leverage_entry_visible(
                expected_text,
                timeout=10,
            ), f"Expected leverage selector to show PRO entry text: {expected_text}"
        logger.info("[CASE] au_pro_leverage_entry_visible: finish case")
        return

    def assert_leverage_entry_opens_assessment_scenario(self, case_data):
        expected = case_data["expected"]
        trade_data = case_data["trade"]
        instrument_name = trade_data.get("instrument", "Gold")
        leverage = trade_data.get("leverage", "20X")
        expected_entry_text = expected["leverage_pro_text"]

        logger.info(
            "[CASE] au_pro_leverage_entry_opens_assessment: start Trade -> %s -> Buy -> %s -> click AU Pro entry -> assert H5 -> finish case",
            instrument_name,
            leverage,
        )
        with step("Assert AU PRO assessment page is opened from leverage entry"):
            self.open_leverage_selector(instrument_name, leverage)
            assert self.order_page.is_pro_leverage_entry_visible(
                expected_entry_text,
                timeout=10,
            ), f"Expected leverage selector to show PRO entry text: {expected_entry_text}"

            self.order_page.tap_pro_leverage_entry(timeout=5)
            self._continue_from_optional_pro_account_intro(expected)
            self.appropriateness_page.assert_assessment_visible(
                expected.get("assessment_texts", []),
                timeout=15,
            )
        logger.info("[CASE] au_pro_leverage_entry_opens_assessment: finish case")

    def assert_leverage_pro_entry_visible(self, case_data):
        self.assert_leverage_entry_visible_scenario(case_data)

    def assert_appropriateness_assessment_visible(self, case_data):
        self.assert_leverage_entry_opens_assessment_scenario(case_data)

    def _continue_from_optional_pro_account_intro(self, expected):
        for _ in range(10):
            if self.appropriateness_page.is_loaded(timeout=1):
                return

            if self.pro_account_intro_page.is_loaded(timeout=1):
                self.pro_account_intro_page.assert_intro_visible(
                    expected.get("optional_pro_account_intro_texts", []),
                    timeout=10,
                )
                self.pro_account_intro_page.tap_open_pro_account(timeout=5)
                return

    def open_leverage_selector(self, instrument_name, leverage_text="20X"):
        logger.info("start Trade -> %s -> Buy -> %s -> AU Pro", instrument_name, leverage_text)
        self.trade_page.open_trade_tab(timeout=5)
        self.open_full_order_page(instrument_name)
        self.order_page.tap_current_leverage(timeout=5)
        self.order_page.select_leverage(leverage_text, timeout=5)
        self.order_page.tap_current_leverage(timeout=5)

    def open_full_order_page(self, instrument_name):
        with step(f"Open full order page for instrument: {instrument_name}"):
            self.open_instrument_detail(instrument_name)
            self.instrument_detail_page.tap_buy(timeout=5)
            self.instrument_detail_page.tap_expand_order(timeout=5)
            self.order_page.wait_for_loaded(timeout=10)

    def open_mine_page(self):
        with step("Open Mine page"):
            if self.mine_page.is_loaded(timeout=2):
                return
            self._open_home_from_any_authenticated_page()
            self.home_page.open_personal_center()
            self.mine_page.wait_for_loaded(timeout=10)

    def open_instrument_detail(self, instrument_name):
        if not self.trade_page.is_loaded(timeout=2):
            self._return_to_main_tab_area()
            self.trade_page.open_trade_tab(timeout=5)
        self.trade_page.open_instrument(instrument_name, timeout=10)
        self.instrument_detail_page.wait_for_loaded(instrument_name, timeout=10)

    def _is_authenticated_area_visible(self):
        return (
            self.home_page.is_loaded(timeout=3)
            or self.mine_page.is_loaded(timeout=1)
            or self.trade_page.is_loaded(timeout=1)
            or self.instrument_detail_page.is_loaded(timeout=1)
            or self.order_page.is_loaded(timeout=1)
            or self.order_page.is_leverage_selector_visible(timeout=1)
            or self.pro_account_intro_page.is_loaded(timeout=1)
            or self.appropriateness_page.is_loaded(timeout=1)
        )

    def _return_to_main_tab_area(self):
        for _ in range(8):
            if self.home_page.is_loaded(timeout=1) or self.trade_page.is_loaded(timeout=1):
                return
            if self.pro_account_intro_page.is_loaded(timeout=1):
                self.pro_account_intro_page.close(timeout=5)
            elif self.appropriateness_page.is_loaded(timeout=1):
                self.appropriateness_page.close(timeout=5)
            elif self.order_page.is_leverage_selector_visible(timeout=1):
                self.order_page.close_leverage_selector(timeout=5)
            elif self.order_page.is_loaded(timeout=1):
                self.order_page.close_full_order(timeout=5)
            elif self.instrument_detail_page.is_loaded(timeout=1):
                self.instrument_detail_page.close(timeout=5)
            elif self.mine_page.is_loaded(timeout=1):
                self.mine_page.close(timeout=5)
            else:
                self.home_page.press_back()

        assert self.home_page.is_loaded(timeout=1) or self.trade_page.is_loaded(timeout=1), (
            "Failed to recover to Home or Trade tab"
        )

    def _teardown_recover_to_main_tab_area(self, scenario, case_id=None):
        prefix = f"[TEARDOWN][{case_id or scenario or 'unknown'}]"
        logger.info("%s start recover app state", prefix)

        if scenario == "card_visible":
            self._teardown_card_visible(prefix)
            return

        if scenario == "leverage_entry_visible":
            self._teardown_leverage_entry_visible(prefix)
            return

        if scenario == "leverage_entry_opens_assessment":
            self._teardown_leverage_entry_opens_assessment(prefix)
            return

        raise ElementOperationError(f"{prefix} unsupported teardown scenario: {scenario}")

    def _teardown_card_visible(self, prefix):
        if self.mine_page.is_loaded(timeout=1):
            logger.info("%s close mine page if exists", prefix)
            self._teardown_close_mine_page(prefix, timeout=5)

        if self.home_page.is_loaded(timeout=1) or self.trade_page.is_loaded(timeout=1):
            logger.info("%s finish recover app state", prefix)
            return

        raise ElementOperationError(f"{prefix} recover app state failed")

    def _teardown_leverage_entry_visible(self, prefix):
        for _ in range(8):
            if self.order_page.is_leverage_selector_visible(timeout=1):
                logger.info("%s close leverage selector if exists", prefix)
                self._teardown_close_leverage_selector(prefix, timeout=5)
                continue

            if self.order_page.is_loaded(timeout=1):
                logger.info("%s close order page if exists", prefix)
                self._teardown_close_order_page(prefix, timeout=5)
                continue

            if self.instrument_detail_page.is_loaded(timeout=1):
                logger.info("%s close detail page if exists", prefix)
                self._teardown_close_detail_page(prefix, timeout=5)
                continue

            if self.home_page.is_loaded(timeout=1) or self.trade_page.is_loaded(timeout=1):
                logger.info("%s finish recover app state", prefix)
                return

            logger.info("%s press back for unknown non-H5 page", prefix)
            self.home_page.press_back()

        raise ElementOperationError(f"{prefix} recover app state failed")

    def _teardown_leverage_entry_opens_assessment(self, prefix):
        for _ in range(10):
            if self.appropriateness_page.is_loaded(timeout=1):
                logger.info("%s close H5 appropriateness assessment if exists", prefix)
                self.appropriateness_page.close(timeout=5)
                continue

            if self.pro_account_intro_page.is_loaded(timeout=1):
                logger.info("%s close H5 pro account intro if exists", prefix)
                self.pro_account_intro_page.close(timeout=5)
                continue

            if self._teardown_leave_confirm_visible():
                logger.info("%s close H5 leave confirm if exists", prefix)
                self._teardown_confirm_leave(prefix)
                continue

            if self._teardown_h5_visible():
                logger.info("%s close H5 if exists", prefix)
                self.home_page.press_back()
                self._teardown_confirm_leave(prefix)
                continue

            if self.order_page.is_leverage_selector_visible(timeout=1):
                logger.info("%s close leverage selector if exists", prefix)
                self._teardown_close_leverage_selector(prefix, timeout=5)
                continue

            if self.order_page.is_loaded(timeout=1):
                logger.info("%s close order page if exists", prefix)
                self._teardown_close_order_page(prefix, timeout=5)
                continue

            if self.instrument_detail_page.is_loaded(timeout=1):
                logger.info("%s close detail page if exists", prefix)
                self._teardown_close_detail_page(prefix, timeout=5)
                continue

            if self.home_page.is_loaded(timeout=1) or self.trade_page.is_loaded(timeout=1):
                logger.info("%s finish recover app state", prefix)
                return

            logger.info("%s close unknown popup if exists", prefix)
            self.home_page.close_common_popups_if_exists(rounds=2, name="au_pro_teardown_popup")
            if self.home_page.is_loaded(timeout=1) or self.trade_page.is_loaded(timeout=1):
                logger.info("%s finish recover app state", prefix)
                return

            logger.info("%s press back for unknown page", prefix)
            self.home_page.press_back()

        if self.home_page.is_loaded(timeout=1) or self.trade_page.is_loaded(timeout=1):
            logger.info("%s finish recover app state", prefix)
            return

        raise ElementOperationError(f"{prefix} recover app state failed")

    def _teardown_close_leverage_selector(self, prefix, timeout=5):
        self.home_page.press_back()
        self.order_page.wait_until(
            lambda: not self.order_page.is_leverage_selector_visible(timeout=1),
            timeout=timeout,
            message=f"{prefix} leverage selector should be closed",
        )

    def _teardown_close_order_page(self, prefix, timeout=5):
        self.home_page.press_back()
        self.order_page.wait_until(
            lambda: not self.order_page.is_loaded(timeout=1),
            timeout=timeout,
            message=f"{prefix} order page should be closed",
        )

    def _teardown_close_detail_page(self, prefix, timeout=5):
        self.home_page.press_back()
        self.instrument_detail_page.wait_until(
            lambda: not self.instrument_detail_page.is_loaded(timeout=1),
            timeout=timeout,
            message=f"{prefix} detail page should be closed",
        )

    def _teardown_close_mine_page(self, prefix, timeout=5):
        self.home_page.press_back()
        self.mine_page.wait_until(
            lambda: not self.mine_page.is_loaded(timeout=1),
            timeout=timeout,
            message=f"{prefix} mine page should be closed",
        )

    def _teardown_h5_visible(self):
        source = self.home_page._safe_page_source()
        current_context = self.home_page.current_context()
        return "x.mitrade.dev:id/webViewLty" in source or (
            current_context is not None and current_context != "NATIVE_APP"
        )

    def _teardown_leave_confirm_visible(self):
        source = self.home_page._safe_page_source()
        return "Do you wish to leave?" in source or "您确定要离开吗？" in source

    def _teardown_confirm_leave(self, prefix):
        leave_buttons = (
            ("xpath", "//android.widget.Button[@text='Leave']"),
            ("xpath", "//android.widget.TextView[@text='Leave']"),
            ("xpath", "//android.widget.Button[@text='离开']"),
            ("xpath", "//android.widget.TextView[@text='离开']"),
        )
        for locator in leave_buttons:
            if not self.home_page.is_element_visible(locator, timeout=1):
                continue
            logger.info("%s click Leave on H5 leave confirm", prefix)
            self.home_page.click(locator, timeout=3)
            return True
        return False

    def _open_home_from_any_authenticated_page(self):
        self._return_to_main_tab_area()
        if not self.home_page.is_loaded(timeout=1):
            self.home_page.open_home_tab(timeout=5)
        self.home_page.wait_for_loaded(timeout=10)

    @staticmethod
    def _scenario_from_case_id(case_id):
        mapping = {
            "au_pro_card_visible": "card_visible",
            "au_pro_leverage_entry_visible": "leverage_entry_visible",
            "au_pro_leverage_entry_opens_assessment": "leverage_entry_opens_assessment",
        }
        return mapping.get(case_id)
