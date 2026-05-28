from common.allure_util import step
from core.exceptions import UnsupportedPlatformError
from business.app_state_flow import AppStateFlow
from pages.android.appropriateness_assessment_page import AndroidAppropriatenessAssessmentPage
from pages.android.home_page import AndroidHomePage
from pages.android.instrument_detail_page import AndroidInstrumentDetailPage
from pages.android.mine_page import AndroidMinePage
from pages.android.order_page import AndroidOrderPage
from pages.android.pro_account_intro_page import AndroidProAccountIntroPage
from pages.android.trade_page import AndroidTradePage


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

    def assert_au_pro_case(self, case_data):
        self.login_as(case_data["account"], case_data)
        expected = case_data["expected"]

        try:
            if expected.get("au_pro_card_visible"):
                self.assert_au_pro_card_visible(expected)

            if expected.get("leverage_pro_entry_visible"):
                self.assert_leverage_pro_entry_visible(case_data)

            if expected.get("appropriateness_assessment_visible"):
                self.assert_appropriateness_assessment_visible(case_data)
        finally:
            self._return_to_main_tab_area()

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

    def is_au_pro_card_visible(self, expected_texts):
        if not self.mine_page.is_loaded(timeout=3):
            self._open_home_from_any_authenticated_page()
            self.home_page.open_personal_center()
        return self.mine_page.is_au_pro_card_visible(expected_texts)

    def assert_leverage_pro_entry_visible(self, case_data):
        expected = case_data["expected"]
        trade_data = case_data["trade"]
        instrument_name = trade_data.get("instrument", "Gold")
        expected_text = expected["leverage_pro_text"]

        with step("Assert AU PRO leverage entry is visible"):
            self.open_leverage_selector(instrument_name)
            assert self.order_page.is_pro_leverage_entry_visible(
                expected_text,
                timeout=10,
            ), f"Expected leverage selector to show PRO entry text: {expected_text}"

    def assert_appropriateness_assessment_visible(self, case_data):
        expected = case_data["expected"]
        trade_data = case_data["trade"]
        instrument_name = trade_data.get("instrument", "Gold")
        expected_entry_text = expected["leverage_pro_text"]

        with step("Assert AU PRO assessment page is opened from leverage entry"):
            self.open_leverage_selector(instrument_name)
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

    def open_leverage_selector(self, instrument_name):
        self.open_full_order_page(instrument_name)
        self.order_page.tap_current_leverage(timeout=5)

    def open_full_order_page(self, instrument_name):
        with step(f"Open full order page for instrument: {instrument_name}"):
            self.open_instrument_detail(instrument_name)
            self.instrument_detail_page.tap_buy(timeout=5)
            self.instrument_detail_page.tap_expand_order(timeout=5)
            self.order_page.wait_for_loaded(timeout=10)

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

    def _open_home_from_any_authenticated_page(self):
        self._return_to_main_tab_area()
        if not self.home_page.is_loaded(timeout=1):
            self.home_page.open_home_tab(timeout=5)
        self.home_page.wait_for_loaded(timeout=10)
