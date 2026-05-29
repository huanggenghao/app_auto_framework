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
    if platform == "android":
        try:
            from pages.android.login_page import AndroidLoginPage

            AndroidLoginPage(appium_driver).close_common_popups_if_exists(
                rounds=2,
                name="driver_startup_popup",
            )
        except Exception as exc:
            logger.warning("Failed to close startup popup after driver creation: %s", exc)

    yield appium_driver

    report = getattr(request.node, "rep_call", None)
    if report and report.failed:
        screenshot_path = PathUtil.screenshot_path(request.node.name)
        if DriverFactory.save_screenshot(appium_driver, screenshot_path):
            attach_screenshot(screenshot_path, name=f"{request.node.name} failure")

    if platform == "android":
        try:
            from business.app_state_flow import AppStateFlow

            AppStateFlow(appium_driver, platform).recover_to_main_app()
        except Exception as exc:
            logger.warning("Failed to recover app after testcase: %s", exc)

    DriverFactory.quit_driver(appium_driver)
    logger.info("Appium driver closed for platform: %s", platform)


@pytest.fixture
def app_state(driver, platform):
    from business.app_state_flow import AppStateFlow

    return AppStateFlow(driver, platform)


@pytest.fixture
def ensure_logged_out(app_state):
    app_state.ensure_logged_out()


@pytest.fixture
def ensure_logged_in(app_state):
    from common.account_util import resolve_account_from_case

    def _ensure_logged_in(case_data, force_relogin=False):
        if force_relogin:
            logger.info(
                "根据 account_type 从 data/accounts.yaml 读取账号: %s",
                case_data.get("account_type") or case_data.get("account_key"),
            )
        account_data = (
            resolve_account_from_case(case_data)
            if force_relogin
            else case_data.get("account") or resolve_account_from_case(case_data)
        )
        app_state.ensure_logged_in(
            account_data,
            case_data,
            force_relogin=force_relogin,
        )

    return _ensure_logged_in


@pytest.fixture
def ensure_au_pro_logged_in(ensure_logged_in):
    def _ensure_au_pro_logged_in(case_data):
        ensure_logged_in(case_data, force_relogin=True)

    return _ensure_au_pro_logged_in


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
