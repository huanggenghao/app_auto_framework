import time

from common.allure_util import step
from core.exceptions import LoginStateError, UnsupportedPlatformError
from pages.android.login_page import AndroidLoginPage
from pages.ios.login_page import IOSLoginPage


class LoginFlow:
    def __init__(self, driver, platform):
        self.platform = platform
        self.page = self._build_login_page(driver, platform)

    def login(
        self,
        login_type,
        account,
        password,
        auth_method="password",
        verification_code=None,
        use_prefilled_password=True,
        post_login=None,
    ):
        with step(f"Login with {login_type} and {auth_method}"):
            if self.platform == "android":
                self._login_android(
                    login_type,
                    account,
                    password,
                    auth_method,
                    verification_code,
                    use_prefilled_password,
                    post_login,
                )
                return

            self._login_ios(account, password)

    def is_login_successful(self, success_text):
        if (
            success_text
            and hasattr(self.page, "is_text_visible")
            and self.page.is_text_visible(success_text, timeout=5)
        ):
            return True
        if hasattr(self.page, "is_home_visible"):
            return self.page.is_home_visible(timeout=10)
        return False

    def get_error_message(self):
        return self.page.get_error_message()

    def _login_android(
        self,
        login_type,
        account,
        password,
        auth_method,
        verification_code,
        use_prefilled_password,
        post_login,
    ):
        self.page.enter_login_page()
        self.page.select_login_type(login_type)
        self._input_android_credentials(
            login_type,
            account,
            password,
            auth_method,
            verification_code,
            use_prefilled_password,
        )
        self.page.tap_login_button()
        self._handle_android_post_login(
            auth_method,
            verification_code,
            post_login or {},
        )

    def _input_android_credentials(
        self,
        login_type,
        account,
        password,
        auth_method,
        verification_code,
        use_prefilled_password,
    ):
        if auth_method == "password":
            self._input_android_password_login(
                login_type,
                account,
                password,
                use_prefilled_password,
            )
            return
        if auth_method == "verification_code":
            self._input_android_verification_code_login(
                login_type,
                account,
                verification_code,
            )
            return
        raise ValueError(f"Unsupported auth_method: {auth_method}")

    def _input_android_password_login(
        self,
        login_type,
        account,
        password,
        use_prefilled_password,
    ):
        self.page.switch_auth_method_if_needed("password")
        self.page.input_account(login_type, account)
        if login_type == "email" or not use_prefilled_password:
            self.page.input_password(password)
            return

        self.page.enable_prefilled_password()

    def _input_android_verification_code_login(
        self,
        login_type,
        account,
        verification_code,
    ):
        if login_type != "email":
            raise ValueError(
                "verification_code auth_method is currently supported for email login only"
            )

        self.page.switch_auth_method_if_needed("verification_code")
        self.page.input_account(login_type, account)
        self.page.request_verification_code()
        self.page.input_verification_code(
            verification_code or self.page.DEFAULT_VERIFICATION_CODE
        )
        self.page.hide_keyboard_if_open()

    def _handle_android_post_login(self, auth_method, verification_code, post_login):
        if auth_method == "password":
            self._complete_android_2fa_if_present(
                verification_code or self.page.DEFAULT_VERIFICATION_CODE
            )

        actual_landing = self._detect_android_post_login_state(post_login)
        self._ensure_expected_landing(actual_landing, post_login)

        if actual_landing == "home":
            return

        if actual_landing == "restriction_popup":
            self._handle_android_restriction_popup(post_login)
            return

        if actual_landing == "kyc":
            self._handle_android_kyc_landing(post_login)
            return

        self._raise_unexpected_login_state(
            f"Unsupported post-login landing state: {actual_landing}",
            post_login,
        )

    def _detect_android_post_login_state(self, post_login):
        timeout = post_login.get("timeout", 15)
        popup_texts = post_login.get("popup_texts", [])
        deadline = time.monotonic() + timeout

        with step("Detect Android post-login landing state"):
            while time.monotonic() < deadline:
                if self.page.is_home_visible(timeout=1):
                    return "home"

                if popup_texts and self.page.is_popup_visible(popup_texts, timeout=1):
                    return "restriction_popup"

                if self.page.is_kyc_entry_visible(timeout=1):
                    return "kyc"

                time.sleep(0.5)

        self._raise_unexpected_login_state(
            "Login did not land on home, configured restriction popup, or KYC page",
            post_login,
        )

    def _ensure_expected_landing(self, actual_landing, post_login):
        expected_landing = post_login.get("expected_landing")
        if not expected_landing or actual_landing == expected_landing:
            return

        self._raise_unexpected_login_state(
            f"Unexpected post-login landing: expected={expected_landing}, actual={actual_landing}",
            post_login,
        )

    def _complete_android_2fa_if_present(self, verification_code):
        if not self.page.is_2fa_page_visible(timeout=10):
            return False

        with step("Complete Android SMS verification"):
            self.page.input_verification_code(verification_code)
            self.page.hide_keyboard_if_open()
            self.page.submit_two_factor_code()
        return True

    def _leave_android_kyc_if_present(self):
        if self.page.is_home_visible(timeout=5):
            return False

        if not self.page.is_kyc_entry_visible(timeout=12):
            return False

        with step("Leave KYC onboarding after login"):
            self.page.close_kyc()
            if self.page.is_kyc_leave_confirmation_visible(timeout=5):
                self.page.confirm_leave_kyc()
            self._wait_for_android_home(timeout=15)
        return True

    def _handle_android_kyc_landing(self, post_login):
        if post_login.get("kyc_action", "stay") == "leave":
            self._leave_android_kyc_if_present()

    def _handle_android_restriction_popup(self, post_login):
        popup_texts = post_login.get("popup_texts", [])
        if isinstance(popup_texts, str):
            popup_texts = [popup_texts]

        with step("Verify Android restriction popup after login"):
            if not self.page.is_popup_visible(
                popup_texts,
                timeout=post_login.get("timeout", 15),
            ):
                self._raise_unexpected_login_state(
                    f"Restriction popup texts are not visible: {popup_texts}",
                    post_login,
                )

        button_text = post_login.get("popup_button_text")
        if button_text:
            with step(f"Close Android restriction popup with button: {button_text}"):
                self.page.tap_popup_button(button_text, timeout=5)

    def _wait_for_android_home(self, timeout):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.page.is_home_visible(timeout=1):
                return
            time.sleep(0.5)

        self._raise_unexpected_login_state(
            f"Home page not visible within {timeout}s after KYC handling",
            {"expected_landing": "home", "timeout": timeout},
        )

    def _raise_unexpected_login_state(self, message, post_login):
        diagnostics = self.page.capture_diagnostics("unexpected_login_state")
        raise LoginStateError(f"{message}. expected_config={post_login}. {diagnostics}")

    def _login_ios(self, account, password):
        self.page.input_account(account)
        self.page.input_password(password)
        self.page.tap_login_button()

    @staticmethod
    def _build_login_page(driver, platform):
        if platform == "android":
            return AndroidLoginPage(driver)
        if platform == "ios":
            return IOSLoginPage(driver)
        raise UnsupportedPlatformError(f"Unsupported platform: {platform}")
