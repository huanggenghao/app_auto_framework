from common.path_util import PathUtil
from common.yaml_util import load_yaml


def load_accounts():
    accounts = load_yaml(PathUtil.accounts_path()).get("accounts", {})
    if isinstance(accounts, list):
        return {
            account["account_type"]: account
            for account in accounts
            if account.get("account_type")
        }
    return accounts


def resolve_account(account_type):
    accounts = load_accounts()
    if account_type not in accounts:
        raise KeyError(f"Account type not found in accounts.yaml: {account_type}")
    return _normalize_account(account_type, accounts[account_type])


def resolve_account_from_case(case_data):
    account_type = case_data.get("account_type") or case_data.get("account_key")
    if not account_type:
        raise KeyError("Missing account_type in testcase data")
    return resolve_account(account_type)


def merge_account_into_case(case_data):
    if "account_type" not in case_data and "account_key" not in case_data:
        return dict(case_data)

    resolved_case = dict(resolve_account_from_case(case_data))
    resolved_case.update(case_data)
    return resolved_case


def _normalize_account(account_type, account_data):
    account = dict(account_data)
    account.setdefault("account_type", account_type)

    if "username" not in account and "account" in account:
        account["username"] = account["account"]
    if "account" not in account and "username" in account:
        account["account"] = account["username"]

    if not account.get("username"):
        raise KeyError(f"Missing username/account for account_type: {account_type}")
    if "password" not in account:
        raise KeyError(f"Missing password for account_type: {account_type}")

    return account
