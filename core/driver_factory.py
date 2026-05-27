from common.logger import get_logger
from common.path_util import PathUtil
from common.yaml_util import load_yaml
from core.exceptions import FrameworkConfigError, UnsupportedPlatformError


logger = get_logger(__name__)


class DriverFactory:
    @staticmethod
    def create_driver(platform):
        config = DriverFactory._load_platform_config(platform)
        server_url = config.get("server", {}).get("url")
        capabilities = config.get("capabilities", {})

        if not server_url:
            raise FrameworkConfigError(f"Missing Appium server url in {platform} config")
        if not capabilities:
            raise FrameworkConfigError(f"Missing capabilities in {platform} config")

        try:
            from appium import webdriver
            from appium.options.android import UiAutomator2Options
            from appium.options.ios import XCUITestOptions
        except ImportError as exc:
            raise FrameworkConfigError(
                "Appium-Python-Client is not installed. Run: python -m pip install -r requirements.txt"
            ) from exc

        if platform == "android":
            options = UiAutomator2Options().load_capabilities(capabilities)
        elif platform == "ios":
            options = XCUITestOptions().load_capabilities(capabilities)
        else:
            raise UnsupportedPlatformError(f"Unsupported platform: {platform}")

        logger.info("Connecting to Appium server: %s", server_url)
        return webdriver.Remote(command_executor=server_url, options=options)

    @staticmethod
    def quit_driver(driver):
        if driver:
            driver.quit()

    @staticmethod
    def save_screenshot(driver, file_path):
        if not driver:
            return False

        try:
            return driver.save_screenshot(str(file_path))
        except Exception as exc:
            logger.warning("Failed to save screenshot: %s", exc)
            return False

    @staticmethod
    def _load_platform_config(platform):
        if platform not in ("android", "ios"):
            raise UnsupportedPlatformError(f"Unsupported platform: {platform}")

        config_path = PathUtil.config_path(platform)
        return load_yaml(config_path)

