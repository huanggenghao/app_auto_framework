# App Automation Framework

Python + pytest + Appium + Allure + YAML based mobile UI automation framework skeleton.

This first version focuses on framework structure and a login example. The sample locators and capabilities are placeholders and must be adjusted for a real Android or iOS app before running end-to-end tests.

## Requirements

- Python 3.10+
- Appium Server 2.x+
- Android SDK / Xcode environment as required by the target platform
- Allure CLI, optional, for generating HTML reports

## Install

```bash
python -m pip install -r requirements.txt
```

## Configuration

Platform Appium server and capabilities are stored in:

- `config/android.yaml`
- `config/ios.yaml`

Update these files with the device, app, package, bundle id, and automation settings for the target test environment.

## Run Tests

Collect Android tests:

```bash
python -m pytest --platform=android --collect-only
```

Collect iOS tests:

```bash
python -m pytest --platform=ios --collect-only
```

Run Android login example:

```bash
python -m pytest testcases/test_login.py --platform=android --alluredir=reports/allure-results
```

Run iOS login example:

```bash
python -m pytest testcases/test_login.py --platform=ios --alluredir=reports/allure-results
```

Generate Allure report:

```bash
allure generate reports/allure-results -o reports/allure-report --clean
```

## Account-driven Scenarios

Reusable accounts are stored in `data/accounts.yaml`. Keep only account-owned
attributes there, such as `account`, `password`, `login_type`, `kyc_status`,
`user_type`, and `region`.

Scenario expectations belong in the matching case file, such as
`data/au_pro_cases.yaml` or `data/login_cases.yaml`.

```yaml
cases:
  - case_id: "kyc_restricted_login"
    title: "未完成KYC账号登录后出现限制弹窗"
    account_key: "kyc_pending_user_example"
    auth_method: "password"
    verification_code: "123456"
    post_login:
      expected_landing: "restriction_popup"
      popup_texts:
        - "Complete identity verification"
      popup_button_text: "OK"
    expected:
      success: true
```

Supported Android post-login case fields:

- `post_login.expected_landing`: `home`, `kyc`, or `restriction_popup`
- `post_login.kyc_action`: `stay` or `leave`, used when landing on KYC
- `post_login.popup_texts`: text that must be visible in a restriction popup
- `post_login.popup_button_text`: optional button text to close the popup

Login flow decides from the actual page state first. If home, configured popup,
or KYC is not detected within the case timeout, the framework saves screenshot
and page source under `reports/` before raising a clear error.

## Project Layout

```text
app_auto_framework/
├── config/          # Platform Appium configuration
├── common/          # Logging, YAML, path, and Allure helpers
├── core/            # Driver factory, BasePage, and framework exceptions
├── pages/           # Platform-specific Page Objects
├── business/        # Business flows composed from Page Objects
├── data/            # YAML-driven test data
├── testcases/       # pytest test cases and assertions
└── reports/         # Allure results and screenshots
```
