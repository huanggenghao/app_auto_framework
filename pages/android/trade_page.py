from common.allure_util import step
from common.logger import get_logger
from core.base_page import BasePage
from core.exceptions import ElementOperationError


logger = get_logger(__name__)


class AndroidTradePage(BasePage):
    TRADE_TAB = ("id", "x.mitrade.dev:id/rbTabTrade")
    MARKET_TITLE = ("id", "x.mitrade.dev:id/tvMarket")
    MARKET_TEXT = ("xpath", "//*[@text='Market' or @text='市场' or contains(@text, 'Market')]")
    POPULAR_TEXT = ("xpath", "//*[@text='Popular' or @text='热门' or contains(@text, 'Popular')]")
    TRADE_LIST = ("id", "x.mitrade.dev:id/recycler_view")
    SEARCH_CANDIDATES = (
        ("id", "x.mitrade.dev:id/ivSearch"),
        ("id", "x.mitrade.dev:id/etSearch"),
        ("xpath", "//*[contains(@resource-id, 'search') or contains(@resource-id, 'Search')]"),
    )
    GOLD_TEXT = ("xpath", "//*[@text='Gold' or @text='黄金' or contains(@text, 'Gold') or contains(@text, '黄金')]")
    SILVER_TEXT = ("xpath", "//*[@text='Silver' or @text='白银' or contains(@text, 'Silver') or contains(@text, '白银')]")
    GOLD_ROW = ("xpath", "//*[@resource-id='x.mitrade.dev:id/tv_symbol' and @text='Gold']")
    SILVER_ROW = ("xpath", "//*[@resource-id='x.mitrade.dev:id/tv_symbol' and @text='Silver']")
    TRADE_POPUP_CLOSE_CANDIDATES = (
        ("id", "x.mitrade.dev:id/ivOperatorClose"),
        ("id", "x.mitrade.dev:id/ivClose"),
        ("id", "x.mitrade.dev:id/iv_close"),
        ("id", "x.mitrade.dev:id/btnClose"),
        ("id", "x.mitrade.dev:id/ivNegative"),
        ("id", "x.mitrade.dev:id/btnNegative"),
        ("xpath", "//*[@text='Close' or @text='关闭' or @text='Not now' or @text='Later' or @text='Cancel']"),
        ("xpath", "//*[contains(@resource-id, 'ivClose') or contains(@resource-id, 'btnNegative') or contains(@resource-id, 'ivNegative')]"),
    )
    DIAGNOSTIC_KEYWORDS = (
        "Gold",
        "黄金",
        "Close",
        "关闭",
        "ivOperatorClose",
        "ivClose",
        "btnClose",
        "btnNegative",
        "ivNegative",
        "粉丝专属特惠",
        "入金最高得",
        "去参加",
        "恭喜",
        "奖励",
    )

    def open_trade_tab(self, timeout=5):
        with step("Open Trade tab"):
            logger.info("点击 Trade tab")
            self.click(self.TRADE_TAB, timeout=timeout)
            logger.info("等待 rbTabTrade checked=true")
            self.wait_until(
                lambda: self.is_trade_tab_selected(timeout=0.5),
                timeout=timeout,
                interval=0.3,
                message="Trade tab should be selected",
            )
            logger.info("Trade tab 已选中")
            self.close_common_popups_if_exists(rounds=3, name="trade_entry_popup")
            self.wait_for_loaded(timeout=timeout)

    def close_trade_popups_if_exists(self, rounds=3):
        with step("Close optional Trade popups"):
            closed_common = self.close_common_popups_if_exists(
                rounds=rounds,
                name="trade_popup",
            )
            closed_any = False
            for _ in range(rounds):
                clicked = False
                for locator in self.TRADE_POPUP_CLOSE_CANDIDATES:
                    if not self.optional_exists(locator, timeout=0.5):
                        continue
                    logger.info("关闭 Trade 弹窗/引导: %s", locator)
                    self._tap_visible_element(locator, timeout=1)
                    closed_any = True
                    clicked = True
                    break
                if not clicked:
                    break
            return closed_any or closed_common

    def wait_for_loaded(self, timeout=10):
        if self._is_ready(timeout=1):
            logger.info("Trade 页面 ready")
            return

        try:
            if not self.is_trade_tab_selected(timeout=1):
                diagnostics = self.capture_diagnostics("trade_tab_not_selected")
                raise ElementOperationError(
                    "Trade page is not ready because rbTabTrade is not selected. "
                    f"current_page_type={self.current_page_type()}. {diagnostics}"
                )

            self.close_common_popups_if_exists(rounds=2, name="trade_ready_popup")
            self.wait_until(
                self._is_ready,
                timeout=timeout,
                interval=0.5,
                message="Trade page should be ready",
            )
            logger.info("Trade 页面 ready")
        except ElementOperationError as exc:
            self._log_trade_ready_diagnostics()
            diagnostics = self.capture_diagnostics("trade_page_not_ready")
            raise ElementOperationError(
                "Trade page is not ready after opening Trade tab. "
                f"current_page_type={self.current_page_type()}. {diagnostics}"
            ) from exc

    def is_loaded(self, timeout=3):
        return self._is_ready(timeout=timeout)

    def open_instrument(self, instrument_name, timeout=10):
        with step(f"Open instrument from Trade list: {instrument_name}"):
            self.wait_for_loaded(timeout=timeout)
            instrument_locator = self._instrument_locator(instrument_name)
            if not self.is_trade_tab_selected(timeout=1) or not self.is_element_visible(
                instrument_locator,
                timeout=timeout,
            ):
                diagnostics = self.capture_diagnostics("trade_instrument_not_ready")
                raise ElementOperationError(
                    "Cannot click instrument because current page is not ready for Trade. "
                    f"instrument={instrument_name}, "
                    f"trade_tab_selected={self.is_trade_tab_selected(timeout=1)}, "
                    f"current_page_type={self.current_page_type()}. {diagnostics}"
                )

            logger.info("点击 %s", instrument_name)
            self.click(instrument_locator, timeout=timeout)

    def _is_ready(self, timeout=0.5):
        if not self.is_trade_tab_selected(timeout=timeout):
            return False

        signals = (
            self.is_element_visible(self.MARKET_TITLE, timeout=timeout),
            self.is_element_visible(self.POPULAR_TEXT, timeout=0.5),
            self.is_element_visible(self.TRADE_LIST, timeout=0.5),
            self.is_element_visible(self.GOLD_ROW, timeout=0.5),
            self.is_element_visible(self.SILVER_ROW, timeout=0.5),
        )
        return sum(1 for matched in signals if matched) >= 1

    def is_trade_tab_selected(self, timeout=1):
        try:
            element = self.wait_for_visible(
                self.TRADE_TAB,
                timeout=timeout,
                capture_on_timeout=False,
                log_attempt=False,
            )
        except ElementOperationError:
            return False

        try:
            return (
                element.get_attribute("checked") == "true"
                or element.get_attribute("selected") == "true"
            )
        except Exception:
            return False

    def current_page_type(self):
        if self.is_trade_tab_selected(timeout=0.5):
            return "trade"

        source = self._safe_page_source()
        if (
            "x.mitrade.dev:id/ivHomeLogo" in source
            or ("x.mitrade.dev:id/rbTabHome" in source and "checked=\"true\"" in source)
        ):
            return "home"
        if "x.mitrade.dev:id/flMineRoot" in source or "x.mitrade.dev:id/mavAccountView" in source:
            return "mine"
        if "x.mitrade.dev:id/tvLoginTitle" in source:
            return "login"
        return "unknown"

    def _tap_visible_element(self, locator, timeout=1):
        element = self.wait_for_visible(locator, timeout=timeout)
        try:
            element.click()
        except Exception:
            rect = element.rect
            self.tap_coordinates(
                rect["x"] + rect["width"] / 2,
                rect["y"] + rect["height"] / 2,
            )

    def _log_trade_ready_diagnostics(self):
        try:
            source = self.driver.page_source or ""
        except Exception as exc:
            logger.warning("读取 Trade page_source 失败: %s", exc)
            return

        keyword_state = {
            keyword: keyword in source
            for keyword in self.DIAGNOSTIC_KEYWORDS
        }
        logger.warning("Trade 页面未 ready，page_source 关键词命中: %s", keyword_state)

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
