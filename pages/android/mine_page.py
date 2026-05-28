from common.allure_util import step
from core.base_page import BasePage


class AndroidMinePage(BasePage):
    MINE_ROOT = ("id", "x.mitrade.dev:id/flMineRoot")
    ACCOUNT_VIEW = ("id", "x.mitrade.dev:id/mavAccountView")
    BACK_BUTTON = ("id", "x.mitrade.dev:id/leftBackView")

    def wait_for_loaded(self, timeout=10):
        self.wait_for_visible(self.MINE_ROOT, timeout=timeout)

    def is_loaded(self, timeout=3):
        return self.is_element_visible(self.MINE_ROOT, timeout=timeout) or self.is_element_visible(
            self.ACCOUNT_VIEW, timeout=1
        )

    def is_au_pro_card_visible(self, expected_texts):
        with step("Verify AU PRO card content in personal center"):
            self.wait_for_loaded(timeout=10)
            if not self.is_element_visible(self.ACCOUNT_VIEW, timeout=5):
                return False

            for text in expected_texts:
                if not self.is_element_visible(self._text_contains_locator(text), timeout=5):
                    return False
            return True

    def close(self, timeout=5):
        with step("Close personal center"):
            self.wait_for_loaded(timeout=timeout)
            if self.is_element_visible(self.BACK_BUTTON, timeout=1):
                self.click(self.BACK_BUTTON, timeout=timeout)
            else:
                self.press_back()
            self.wait_until(
                lambda: not self.is_loaded(timeout=1),
                timeout=timeout,
                message="Personal center should be closed",
            )

    def visible_texts(self):
        if not self.is_loaded(timeout=2):
            return []
        return [
            element.text
            for element in self.driver.find_elements("xpath", "//android.widget.TextView")
            if element.text
        ]

    @classmethod
    def _text_contains_locator(cls, text):
        return ("xpath", f"//*[contains(@text, {cls._xpath_literal(text)})]")

    @staticmethod
    def _xpath_literal(value):
        if "'" not in value:
            return f"'{value}'"
        if '"' not in value:
            return f'"{value}"'

        parts = value.split("'")
        return "concat(" + ', "\'", '.join(f"'{part}'" for part in parts) + ")"
