from common.allure_util import step
from core.base_page import BasePage


class AndroidOrderPage(BasePage):
    FULL_ORDER_ROOT = ("id", "x.mitrade.dev:id/tvOpenPositionTitle")
    CURRENT_LEVERAGE = ("id", "x.mitrade.dev:id/tvCurrentLever")
    LEVERAGE_SELECTOR_TITLE = (
        "xpath",
        "//*[@resource-id='x.mitrade.dev:id/tvTitle' and @text='Select Leverage']",
    )
    PRO_ACCOUNT_ENTRY = ("id", "x.mitrade.dev:id/rlProAccount")
    PRO_ACCOUNT_TEXT = ("id", "x.mitrade.dev:id/tvProContent")
    LEVERAGE_LIST = ("id", "x.mitrade.dev:id/rvLeverages")

    def wait_for_loaded(self, timeout=10):
        self.wait_for_visible(self.FULL_ORDER_ROOT, timeout=timeout)
        self.wait_for_visible(self.CURRENT_LEVERAGE, timeout=timeout)

    def is_loaded(self, timeout=3):
        return self.is_element_visible(self.FULL_ORDER_ROOT, timeout=timeout)

    def is_leverage_selector_visible(self, timeout=3):
        return self.is_element_visible(
            self.LEVERAGE_SELECTOR_TITLE,
            timeout=timeout,
        ) or self.is_element_visible(self.LEVERAGE_LIST, timeout=1)

    def tap_current_leverage(self, timeout=5):
        with step("Open leverage selector"):
            self.wait_for_loaded(timeout=timeout)
            self.click(self.CURRENT_LEVERAGE, timeout=timeout)

    def wait_for_leverage_selector(self, timeout=10):
        self.wait_for_visible(self.LEVERAGE_SELECTOR_TITLE, timeout=timeout)
        self.wait_for_visible(self.LEVERAGE_LIST, timeout=timeout)

    def is_pro_leverage_entry_visible(self, expected_text, timeout=5):
        self.wait_for_leverage_selector(timeout=timeout)
        if not self.is_element_visible(self.PRO_ACCOUNT_ENTRY, timeout=timeout):
            return False
        return self.is_element_visible(self._text_locator(expected_text), timeout=timeout)

    def tap_pro_leverage_entry(self, timeout=5):
        with step("Open AU PRO leverage assessment"):
            self.wait_for_leverage_selector(timeout=timeout)
            self.click(self.PRO_ACCOUNT_ENTRY, timeout=timeout)

    def close_leverage_selector(self, timeout=5):
        with step("Close leverage selector"):
            self.wait_for_leverage_selector(timeout=timeout)
            self.press_back()
            self.wait_until(
                lambda: not self.is_leverage_selector_visible(timeout=1),
                timeout=timeout,
                message="Leverage selector should be closed",
            )

    def close_full_order(self, timeout=5):
        with step("Close full order page"):
            self.wait_for_loaded(timeout=timeout)
            self.press_back()
            self.wait_until(
                lambda: not self.is_loaded(timeout=1),
                timeout=timeout,
                message="Full order page should be closed",
            )

    @classmethod
    def _text_locator(cls, text):
        return ("xpath", f"//*[contains(@text, {cls._xpath_literal(text)})]")

    @staticmethod
    def _xpath_literal(value):
        if "'" not in value:
            return f"'{value}'"
        if '"' not in value:
            return f'"{value}"'

        parts = value.split("'")
        return "concat(" + ', "\'", '.join(f"'{part}'" for part in parts) + ")"
