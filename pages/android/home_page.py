from common.allure_util import step
from core.base_page import BasePage


class AndroidHomePage(BasePage):
    HOME_LOGO = ("id", "x.mitrade.dev:id/ivHomeLogo")
    HOME_TAB = ("id", "x.mitrade.dev:id/rbTabHome")
    SIDEBAR_BUTTON = ("id", "x.mitrade.dev:id/ivStartSidebar")

    def wait_for_loaded(self, timeout=10):
        self.wait_for_visible(self.HOME_TAB, timeout=timeout)

    def is_loaded(self, timeout=3):
        return self.is_element_visible(self.HOME_TAB, timeout=timeout) or self.is_element_visible(
            self.HOME_LOGO, timeout=1
        )

    def open_personal_center(self):
        with step("Open personal center from home"):
            self.wait_for_loaded(timeout=10)
            sidebar_button = self.wait_for_visible(self.SIDEBAR_BUTTON, timeout=5)
            rect = sidebar_button.rect
            self.tap_coordinates(
                rect["x"] + rect["width"] / 2,
                rect["y"] + rect["height"] / 2,
            )
