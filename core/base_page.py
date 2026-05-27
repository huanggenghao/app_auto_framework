from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from common.allure_util import attach_screenshot, attach_text, step
from common.logger import get_logger
from common.path_util import PathUtil
from core.exceptions import ElementOperationError


logger = get_logger(__name__)


class BasePage:
    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.timeout = timeout

    def wait_for_visible(self, locator, timeout=None, capture_on_timeout=True):
        wait_time = timeout or self.timeout
        logger.info("Waiting for element visible: %s", locator)
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

    def is_element_visible(self, locator, timeout=3):
        try:
            self.wait_for_visible(locator, timeout, capture_on_timeout=False)
            return True
        except ElementOperationError:
            return False

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
