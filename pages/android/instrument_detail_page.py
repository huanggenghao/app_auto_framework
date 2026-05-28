from common.allure_util import step
from core.base_page import BasePage


class AndroidInstrumentDetailPage(BasePage):
    DETAIL_CONTENT = ("id", "x.mitrade.dev:id/flDetailContent")
    QUICK_ORDER_ROOT = ("id", "x.mitrade.dev:id/clOrderRoot")
    BUY_BUTTON = ("id", "x.mitrade.dev:id/ll_buy")
    EXPAND_ORDER_BUTTON = ("id", "x.mitrade.dev:id/ivAdvance")

    def wait_for_loaded(self, instrument_name, timeout=10):
        self.wait_for_visible(self.DETAIL_CONTENT, timeout=timeout)
        self.wait_for_visible(self._title_locator(instrument_name), timeout=timeout)

    def is_loaded(self, timeout=3):
        return self.is_element_visible(self.DETAIL_CONTENT, timeout=timeout)

    def tap_buy(self, timeout=5):
        with step("Tap Buy on instrument detail"):
            self.click(self.BUY_BUTTON, timeout=timeout)

    def wait_for_quick_order(self, timeout=10):
        self.wait_for_visible(self.QUICK_ORDER_ROOT, timeout=timeout)

    def tap_expand_order(self, timeout=5):
        with step("Expand quick order panel"):
            self.wait_for_quick_order(timeout=timeout)
            self.click(self.EXPAND_ORDER_BUTTON, timeout=timeout)

    def close(self, timeout=5):
        with step("Close instrument detail"):
            self.wait_for_visible(self.DETAIL_CONTENT, timeout=timeout)
            self.press_back()
            self.wait_until(
                lambda: not self.is_loaded(timeout=1),
                timeout=timeout,
                message="Instrument detail page should be closed",
            )

    @classmethod
    def _title_locator(cls, instrument_name):
        return (
            "xpath",
            "//*[@resource-id='x.mitrade.dev:id/tvTitle' "
            f"and @text={cls._xpath_literal(instrument_name)}]",
        )

    @staticmethod
    def _xpath_literal(value):
        if "'" not in value:
            return f"'{value}'"
        if '"' not in value:
            return f'"{value}"'

        parts = value.split("'")
        return "concat(" + ', "\'", '.join(f"'{part}'" for part in parts) + ")"
