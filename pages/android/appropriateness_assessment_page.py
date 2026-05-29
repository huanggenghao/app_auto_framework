from common.allure_util import step
from core.base_page import BasePage
from core.exceptions import ElementOperationError


class AndroidAppropriatenessAssessmentPage(BasePage):
    WEBVIEW_CONTAINER = ("id", "x.mitrade.dev:id/webViewLty")
    TITLE = ("xpath", "//*[@text='Appropriateness assessment']")
    EMPLOYMENT_STATUS = ("xpath", "//*[contains(@text, 'Employment Status')]")
    TOP_CLOSE_BUTTON = (
        "xpath",
        "(//android.widget.Button[@text='' and @clickable='true'])[last()]",
    )
    LEAVE_CONFIRM_TITLE = ("xpath", "//*[contains(@text, 'Do you wish to leave?')]")
    LEAVE_BUTTON = ("xpath", "//android.widget.Button[@text='Leave']")

    def wait_for_loaded(self, timeout=10):
        self.wait_for_visible(self.WEBVIEW_CONTAINER, timeout=timeout)
        self.wait_for_visible(self.TITLE, timeout=timeout)
        self.wait_for_visible(self.EMPLOYMENT_STATUS, timeout=timeout)

    def is_loaded(self, timeout=3):
        return self.is_element_visible(self.TITLE, timeout=timeout)

    def is_text_visible(self, text, timeout=3):
        return self.is_element_visible(self._text_locator(text), timeout=timeout)

    def assert_assessment_visible(self, expected_texts=None, timeout=10):
        with step("Verify appropriateness assessment page"):
            self.wait_for_loaded(timeout=timeout)
            for text in expected_texts or []:
                assert self.is_text_visible(text, timeout=5), (
                    f"Expected assessment page text to be visible: {text}"
                )

    def close(self, timeout=5):
        with step("Close appropriateness assessment"):
            self.wait_for_loaded(timeout=timeout)
            self._request_close(timeout=timeout)
            self._confirm_leave_if_needed(timeout=timeout)

            if self._wait_until_closed(timeout=timeout):
                return

            self.press_back()
            self._confirm_leave_if_needed(timeout=timeout)
            self.wait_until(
                lambda: not self.is_loaded(timeout=1),
                timeout=timeout,
                message="Appropriateness assessment page should be closed",
            )

    def _request_close(self, timeout=5):
        try:
            self.click(self.TOP_CLOSE_BUTTON, timeout=timeout)
        except ElementOperationError:
            self.tap_relative(0.93, 0.073)

    def _confirm_leave_if_needed(self, timeout=5):
        if self.is_element_visible(self.LEAVE_CONFIRM_TITLE, timeout=min(timeout, 1)):
            self.click(self.LEAVE_BUTTON, timeout=timeout)

    def _wait_until_closed(self, timeout=2):
        try:
            self.wait_until(
                lambda: not self.is_loaded(timeout=1),
                timeout=timeout,
                message="Appropriateness assessment page should be closed",
            )
            return True
        except ElementOperationError:
            return False

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
