from datetime import datetime
from pathlib import Path


class PathUtil:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    CONFIG_DIR = PROJECT_ROOT / "config"
    DATA_DIR = PROJECT_ROOT / "data"
    REPORTS_DIR = PROJECT_ROOT / "reports"
    ALLURE_RESULTS_DIR = REPORTS_DIR / "allure-results"
    SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"
    PAGE_SOURCES_DIR = REPORTS_DIR / "page-sources"

    @classmethod
    def config_path(cls, platform):
        return cls.CONFIG_DIR / f"{platform}.yaml"

    @classmethod
    def login_cases_path(cls):
        return cls.DATA_DIR / "login_cases.yaml"

    @classmethod
    def accounts_path(cls):
        return cls.DATA_DIR / "accounts.yaml"

    @classmethod
    def au_pro_cases_path(cls):
        return cls.DATA_DIR / "au_pro_cases.yaml"

    @classmethod
    def ensure_report_dirs(cls):
        cls.ALLURE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.PAGE_SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def screenshot_path(cls, test_name):
        cls.ensure_report_dirs()
        safe_name = "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in test_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return cls.SCREENSHOTS_DIR / f"{safe_name}_{timestamp}.png"

    @classmethod
    def page_source_path(cls, name):
        cls.ensure_report_dirs()
        safe_name = "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return cls.PAGE_SOURCES_DIR / f"{safe_name}_{timestamp}.xml"
