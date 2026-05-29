from contextlib import contextmanager
import time

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from common.allure_util import attach_screenshot, attach_text, step
from common.logger import get_logger
from common.path_util import PathUtil
from core.exceptions import ElementOperationError


logger = get_logger(__name__)


class BasePage:
    COMMON_PROMO_POPUP_KEYWORDS = (
        "粉丝专属特惠",
        "入金最高得",
        "去参加",
        "Bonus",
        "Join",
        "Participate",
        "恭喜",
        "奖励",
    )
    COMMON_POPUP_CLOSE_CANDIDATES = (
        ("id", "x.mitrade.dev:id/ivOperatorClose"),
        ("id", "x.mitrade.dev:id/ivClose"),
        ("id", "x.mitrade.dev:id/iv_close"),
        ("id", "x.mitrade.dev:id/btnClose"),
        ("id", "x.mitrade.dev:id/ivNegative"),
        ("id", "x.mitrade.dev:id/btnNegative"),
        ("xpath", "//*[@text='Close' or @text='关闭' or @text='Cancel' or @text='Not now' or @text='Later']"),
        (
            "xpath",
            "//*[contains(@resource-id, 'ivOperatorClose') "
            "or contains(@resource-id, 'ivClose') "
            "or contains(@resource-id, 'iv_close') "
            "or contains(@resource-id, 'btnClose') "
            "or contains(@resource-id, 'ivNegative') "
            "or contains(@resource-id, 'btnNegative')]",
        ),
    )
    COMMON_POPUP_CONTAINER_CANDIDATES = (
        (
            "xpath",
            "//*[contains(@resource-id, 'dialog') "
            "or contains(@resource-id, 'Dialog') "
            "or contains(@resource-id, 'popup') "
            "or contains(@resource-id, 'Popup') "
            "or contains(@resource-id, 'mask') "
            "or contains(@resource-id, 'Mask')]",
        ),
    )

    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.timeout = timeout

    def wait_for_visible(
        self,
        locator,
        timeout=None,
        capture_on_timeout=True,
        log_attempt=True,
    ):
        wait_time = timeout or self.timeout
        if log_attempt:
            logger.info("Waiting for element visible: %s", locator)
        else:
            logger.debug("Optional element visibility probe: %s", locator)
        try:
            return WebDriverWait(self.driver, wait_time).until(EC.visibility_of_element_located(locator))
        except TimeoutException as exc:
            diagnostics = (
                self.capture_diagnostics("wait_visible_timeout")
                if capture_on_timeout
                else "Diagnostics skipped for optional visibility check"
            )
            raise ElementOperationError(
                f"Element not visible within {wait_time}s: {locator}. {diagnostics}"
            ) from exc

    def wait_for_clickable(self, locator, timeout=None):
        wait_time = timeout or self.timeout
        logger.info("Waiting for element clickable: %s", locator)
        try:
            return WebDriverWait(self.driver, wait_time).until(EC.element_to_be_clickable(locator))
        except TimeoutException as exc:
            diagnostics = self.capture_diagnostics("wait_clickable_timeout")
            raise ElementOperationError(
                f"Element not clickable within {wait_time}s: {locator}. {diagnostics}"
            ) from exc

    def wait_until(self, condition, timeout=None, interval=0.5, message="Condition was not met"):
        wait_time = timeout or self.timeout
        end_time = time.time() + wait_time
        last_error = None

        while time.time() < end_time:
            try:
                if condition():
                    return True
            except Exception as exc:
                last_error = exc
            time.sleep(interval)

        diagnostics = self.capture_diagnostics("wait_condition_timeout")
        raise ElementOperationError(
            f"{message} within {wait_time}s. Last error={last_error}. {diagnostics}"
        )

    def find(self, locator, timeout=None):
        return self.wait_for_visible(locator, timeout)

    def click(self, locator, timeout=None):
        with step(f"Click element: {locator}"):
            try:
                self.wait_for_clickable(locator, timeout).click()
            except WebDriverException as exc:
                diagnostics = self.capture_diagnostics("click_failed")
                raise ElementOperationError(f"Failed to click element: {locator}. {diagnostics}") from exc

    def tap_coordinates(self, x, y):
        with step(f"Tap coordinates: ({x}, {y})"):
            try:
                self.driver.execute_script("mobile: clickGesture", {"x": int(x), "y": int(y)})
            except WebDriverException as exc:
                diagnostics = self.capture_diagnostics("tap_failed")
                raise ElementOperationError(
                    f"Failed to tap coordinates: ({x}, {y}). {diagnostics}"
                ) from exc

    def tap_relative(self, x_ratio, y_ratio):
        window_size = self.driver.get_window_size()
        x = window_size["width"] * x_ratio
        y = window_size["height"] * y_ratio
        self.tap_coordinates(x, y)

    def press_back(self):
        with step("Press back"):
            try:
                self.driver.back()
            except WebDriverException as exc:
                diagnostics = self.capture_diagnostics("press_back_failed")
                raise ElementOperationError(f"Failed to press back. {diagnostics}") from exc

    def input_text(self, locator, text, clear_first=True, timeout=None):
        with step(f"Input text into element: {locator}"):
            element = self.wait_for_visible(locator, timeout)
            try:
                if clear_first:
                    element.clear()
                element.send_keys(text)
            except WebDriverException as exc:
                diagnostics = self.capture_diagnostics("input_failed")
                raise ElementOperationError(
                    f"Failed to input text into element: {locator}. {diagnostics}"
                ) from exc

    def get_text(self, locator, timeout=None):
        with step(f"Get element text: {locator}"):
            return self.wait_for_visible(locator, timeout).text

    def is_element_visible(self, locator, timeout=1):
        try:
            self.wait_for_visible(
                locator,
                timeout,
                capture_on_timeout=False,
                log_attempt=False,
            )
            return True
        except ElementOperationError:
            return False

    def optional_exists(self, locator, timeout=0.5):
        return self.is_element_visible(locator, timeout=timeout)

    def close_common_popups_if_exists(self, rounds=3, timeout=0.5, name="common_popup"):
        closed_any = False
        for _ in range(rounds):
            popup_reason = self._common_blocking_popup_reason(timeout=timeout)
            if not popup_reason:
                return closed_any

            clicked = False
            for locator in self.COMMON_POPUP_CLOSE_CANDIDATES:
                if not self.optional_exists(locator, timeout=timeout):
                    continue
                logger.info("关闭阻塞型通用弹窗: reason=%s, locator=%s", popup_reason, locator)
                try:
                    self._tap_visible_direct(locator, timeout=1)
                    closed_any = True
                    clicked = True
                    break
                except ElementOperationError as exc:
                    logger.warning("关闭通用弹窗失败: locator=%s, error=%s", locator, exc)

            if clicked:
                time.sleep(0.3)
                continue

            logger.warning(
                "检测到阻塞型弹窗信号但未找到可点击关闭按钮，不做坐标兜底: %s",
                self._common_popup_keyword_state(),
            )
            self._log_common_popup_diagnostics(name)
            return closed_any
        return closed_any

    def _tap_visible_direct(self, locator, timeout=1):
        element = self.wait_for_visible(locator, timeout=timeout)
        try:
            element.click()
        except WebDriverException:
            rect = element.rect
            self.tap_coordinates(
                rect["x"] + rect["width"] / 2,
                rect["y"] + rect["height"] / 2,
            )

    def _common_blocking_popup_reason(self, timeout=0.5):
        if self._has_visible_common_popup_close(timeout=timeout):
            return "close_button"

        if self._has_visible_common_popup_container(timeout=timeout):
            return "popup_container"

        source = self._safe_page_source()
        if self._has_common_promo_text(source) and self._has_visible_common_popup_close(timeout=timeout):
            return "promo_with_close_button"

        return None

    def _has_visible_common_popup_close(self, timeout=0.5):
        return any(
            self.optional_exists(locator, timeout=timeout)
            for locator in self.COMMON_POPUP_CLOSE_CANDIDATES
        )

    def _has_visible_common_popup_container(self, timeout=0.5):
        return any(
            self.optional_exists(locator, timeout=timeout)
            for locator in self.COMMON_POPUP_CONTAINER_CANDIDATES
        )

    def _has_common_promo_text(self, source):
        return any(keyword in source for keyword in self.COMMON_PROMO_POPUP_KEYWORDS)

    def _common_popup_keyword_state(self):
        source = self._safe_page_source()
        return {
            keyword: keyword in source
            for keyword in (
                "粉丝专属特惠",
                "入金最高得",
                "去参加",
                "Close",
                "关闭",
                "ivClose",
                "btnClose",
                "ivNegative",
                "btnNegative",
            )
        }

    def _log_common_popup_diagnostics(self, name):
        logger.warning("%s 弹窗关键词命中: %s", name, self._common_popup_keyword_state())

    def _safe_page_source(self):
        try:
            return self.driver.page_source or ""
        except WebDriverException as exc:
            logger.debug("Failed to read page source: %s", exc)
            return ""

    @contextmanager
    def preserved_context(self):
        original_context = self.current_context()
        try:
            yield
        finally:
            if original_context and self.current_context() != original_context:
                self.switch_to_context(original_context)

    def current_context(self):
        try:
            return self.driver.current_context
        except WebDriverException:
            return None

    def available_contexts(self):
        try:
            return self.driver.contexts
        except WebDriverException:
            return []

    def switch_to_context(self, context_name):
        with step(f"Switch context: {context_name}"):
            try:
                self.driver.switch_to.context(context_name)
            except WebDriverException as exc:
                diagnostics = self.capture_diagnostics("switch_context_failed")
                raise ElementOperationError(
                    f"Failed to switch context: {context_name}. {diagnostics}"
                ) from exc

    def switch_to_native_context(self):
        self.switch_to_context("NATIVE_APP")

    def take_screenshot(self, name):
        screenshot_path = PathUtil.screenshot_path(name)
        if self.driver.save_screenshot(str(screenshot_path)):
            logger.info("Screenshot saved: %s", screenshot_path)
            return screenshot_path
        raise ElementOperationError(f"Failed to save screenshot: {screenshot_path}")

    def save_page_source(self, name):
        page_source_path = PathUtil.page_source_path(name)
        page_source = self.driver.page_source
        page_source_path.write_text(page_source, encoding="utf-8")
        logger.info("Page source saved: %s", page_source_path)
        attach_text(page_source, name=f"{name} page source")
        return page_source_path

    def capture_diagnostics(self, name):
        screenshot_path = None
        source_path = None

        try:
            screenshot_path = self.take_screenshot(name)
            attach_screenshot(screenshot_path, name=f"{name} screenshot")
        except Exception as exc:
            logger.warning("Failed to capture screenshot for %s: %s", name, exc)

        try:
            source_path = self.save_page_source(name)
        except Exception as exc:
            logger.warning("Failed to capture page source for %s: %s", name, exc)

        return f"Diagnostics: screenshot={screenshot_path}, page_source={source_path}"
