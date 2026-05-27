# App Automation Framework Instructions

## Project Goal

Build a cross-platform mobile UI automation framework for Android and iOS.

This project is for mobile App UI automation testing. The framework should be maintainable, stable, and easy for QA engineers to extend.

The framework must support:

- Android App automation
- iOS App automation
- pytest test execution
- Appium driver management
- Allure report integration
- YAML-driven test data
- Page Object Model structure
- Clear separation between testcases, business flows, page objects, and base utilities

## Tech Stack

Use the following stack:

- Python 3.10+
- pytest
- Appium-Python-Client
- Selenium 4.x
- PyYAML
- allure-pytest
- standard logging

Do not introduce heavy or unnecessary dependencies.

## Target Directory Structure

The first version of the framework should use this structure:

```text
app_auto_framework/
├── AGENTS.md
├── README.md
├── requirements.txt
├── pytest.ini
├── conftest.py
├── config/
│   ├── android.yaml
│   └── ios.yaml
├── common/
│   ├── logger.py
│   ├── yaml_util.py
│   ├── path_util.py
│   └── allure_util.py
├── core/
│   ├── driver_factory.py
│   ├── base_page.py
│   └── exceptions.py
├── pages/
│   ├── android/
│   │   └── login_page.py
│   └── ios/
│       └── login_page.py
├── business/
│   └── login_flow.py
├── data/
│   └── login_cases.yaml
├── testcases/
│   └── test_login.py
└── reports/
    ├── allure-results/
    └── screenshots/