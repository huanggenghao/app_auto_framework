import pytest

from business.login_flow import LoginFlow
from common.account_util import merge_account_into_case
from common.allure_util import dynamic_title, feature, get_severity_level, severity, story
from common.path_util import PathUtil
from common.yaml_util import load_yaml


def load_login_cases():
    data = load_yaml(PathUtil.login_cases_path())
    return [merge_account_into_case(case_data) for case_data in data.get("cases", [])]


@feature("Login")
@story("Cross-platform login example")
@severity(get_severity_level("critical"))
@pytest.mark.login
@pytest.mark.parametrize("case_data", load_login_cases(), ids=lambda case: case["case_id"])
def test_login(driver, platform, case_data):
    login_flow = LoginFlow(driver, platform)

    dynamic_title(case_data["title"])
    login_flow.login(
        case_data["login_type"],
        case_data["account"],
        case_data.get("password", ""),
        auth_method=case_data.get("auth_method", "password"),
        verification_code=case_data.get("verification_code"),
        use_prefilled_password=case_data.get("use_prefilled_password", True),
        post_login=case_data.get("post_login"),
    )

    expected = case_data["expected"]
    if expected["success"]:
        post_login = case_data.get("post_login") or {}
        expected_landing = post_login.get("expected_landing")
        if expected_landing in ("kyc", "restriction_popup") and post_login.get("kyc_action") != "leave":
            return

        assert login_flow.is_login_successful(expected.get("success_text", "")), "Expected login to succeed"
    else:
        actual_message = login_flow.get_error_message()
        assert expected["message"] in actual_message
