from common.allure_util import step
from core.exceptions import UnsupportedPlatformError
from business.login_flow import LoginFlow
from pages.android.home_page import AndroidHomePage
from pages.android.mine_page import AndroidMinePage


class AuProFlow:
    def __init__(self, driver, platform):
        if platform != "android":
            raise UnsupportedPlatformError(f"AU PRO flow is not implemented for platform: {platform}")

        self.login_flow = LoginFlow(driver, platform)
        self.home_page = AndroidHomePage(driver)
        self.mine_page = AndroidMinePage(driver)

    def login_as(self, account_data, case_data):
        with step("Login as AU PRO scenario account"):
            if self._is_authenticated_area_visible():
                return

            self.login_flow.login(
                account_data["login_type"],
                account_data["account"],
                account_data.get("password", ""),
                auth_method=case_data.get("auth_method", "password"),
                verification_code=case_data.get("verification_code"),
                use_prefilled_password=case_data.get("use_prefilled_password", False),
                post_login=case_data.get("post_login"),
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

    def is_au_pro_card_visible(self, expected_texts):
        if not self.mine_page.is_loaded(timeout=3):
            self.home_page.open_personal_center()
        return self.mine_page.is_au_pro_card_visible(expected_texts)

    def _is_authenticated_area_visible(self):
        return self.home_page.is_loaded(timeout=3) or self.mine_page.is_loaded(timeout=1)
