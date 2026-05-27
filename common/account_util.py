from common.path_util import PathUtil
from common.yaml_util import load_yaml


def load_accounts():
    return load_yaml(PathUtil.accounts_path()).get("accounts", {})


def resolve_account(account_key):
    accounts = load_accounts()
    if account_key not in accounts:
        raise KeyError(f"Account key not found in accounts.yaml: {account_key}")
    return dict(accounts[account_key])


def merge_account_into_case(case_data):
    if "account_key" not in case_data:
        return dict(case_data)

    resolved_case = dict(resolve_account(case_data["account_key"]))
    resolved_case.update(case_data)
    return resolved_case
