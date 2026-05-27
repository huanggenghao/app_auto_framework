class AppAutoFrameworkError(Exception):
    """Base exception for the automation framework."""


class FrameworkConfigError(AppAutoFrameworkError):
    """Raised when framework configuration is missing or invalid."""


class UnsupportedPlatformError(AppAutoFrameworkError):
    """Raised when a platform is not supported."""


class ElementOperationError(AppAutoFrameworkError):
    """Raised when a page element operation fails."""


class LoginStateError(AppAutoFrameworkError):
    """Raised when login lands on an unexpected page state."""
