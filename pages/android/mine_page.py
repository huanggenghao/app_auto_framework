from common.allure_util import step
from core.base_page import BasePage


class AndroidMinePage(BasePage):
    MINE_ROOT = ("id", "x.mitrade.dev:id/flMineRoot")
    ACCOUNT_VIEW = ("id", "x.mitrade.dev:id/mavAccountView")

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
