import pytest

from common.allure_util import attach_screenshot
from common.logger import get_logger
from common.path_util import PathUtil
from core.exceptions import UnsupportedPlatformError


logger = get_logger(__name__)


def pytest_addoption(parser):
    parser.addoption(
        "--platform",
        action="store",
        choices=("android", "ios"),
        default="android",
        help="Mobile platform under test: android or ios.",
    )


@pytest.fixture(scope="session")
def platform(request):
    selected_platform = request.config.getoption("--platform")
    if selected_platform not in ("android", "ios"):
        raise UnsupportedPlatformError(f"Unsupported platform: {selected_platform}")
    return selected_platform


@pytest.fixture
def driver(request, platform):
    from core.driver_factory import DriverFactory

    logger.info("Creating Appium driver for platform: %s", platform)
    appium_driver = DriverFactory.create_driver(platform)

    yield appium_driver

    report = getattr(request.node, "rep_call", None)
    if report and report.failed:
        screenshot_path = PathUtil.screenshot_path(request.node.name)
        if DriverFactory.save_screenshot(appium_driver, screenshot_path):
            attach_screenshot(screenshot_path, name=f"{request.node.name} failure")

    DriverFactory.quit_driver(appium_driver)
    logger.info("Appium driver closed for platform: %s", platform)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

