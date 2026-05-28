from common.allure_util import step
from core.base_page import BasePage


class AndroidTradePage(BasePage):
    TRADE_TAB = ("id", "x.mitrade.dev:id/rbTabTrade")
    MARKET_TITLE = ("id", "x.mitrade.dev:id/tvMarket")
    TRADE_LIST = ("id", "x.mitrade.dev:id/recycler_view")

    def open_trade_tab(self, timeout=5):
        with step("Open Trade tab"):
            self.click(self.TRADE_TAB, timeout=timeout)

    def wait_for_loaded(self, timeout=10):
        self.wait_for_visible(self.MARKET_TITLE, timeout=timeout)
        self.wait_for_visible(self.TRADE_LIST, timeout=timeout)

    def is_loaded(self, timeout=3):
        return self.is_element_visible(self.MARKET_TITLE, timeout=timeout) or self.is_element_visible(
            self.TRADE_LIST,
            timeout=1,
        )

    def open_instrument(self, instrument_name, timeout=10):
        with step(f"Open instrument from Trade list: {instrument_name}"):
            self.wait_for_loaded(timeout=timeout)
            self.click(self._instrument_locator(instrument_name), timeout=timeout)

    @classmethod
    def _instrument_locator(cls, instrument_name):
        return (
            "xpath",
            "//*[@resource-id='x.mitrade.dev:id/tv_symbol' "
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
