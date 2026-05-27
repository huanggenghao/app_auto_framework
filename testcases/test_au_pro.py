import pytest

from business.au_pro_flow import AuProFlow
from common.account_util import resolve_account
from common.allure_util import dynamic_title, feature, get_severity_level, severity, story
from common.path_util import PathUtil
from common.yaml_util import load_yaml


def load_au_pro_cases():
    data = load_yaml(PathUtil.au_pro_cases_path())
    cases = []

    for case_data in data.get("cases", []):
        resolved_case = dict(case_data)
        resolved_case["account"] = resolve_account(case_data["account_key"])
        cases.append(resolved_case)

    return cases


@feature("AU PRO")
@story("Personal center AU PRO card")
@severity(get_severity_level("critical"))
@pytest.mark.au_pro
@pytest.mark.parametrize("case_data", load_au_pro_cases(), ids=lambda case: case["case_id"])
def test_au_pro_card(driver, platform, case_data):
    if platform != "android":
        pytest.skip("AU PRO test is currently implemented for Android only")

    au_pro_flow = AuProFlow(driver, platform)

    dynamic_title(case_data["title"])
    au_pro_flow.assert_au_pro_card(case_data)
