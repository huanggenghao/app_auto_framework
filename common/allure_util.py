from contextlib import contextmanager
from pathlib import Path


try:
    import allure
except ImportError:
    allure = None


def _identity_decorator(func):
    return func


def title(name):
    return allure.title(name) if allure else _identity_decorator


def dynamic_title(name):
    if allure:
        allure.dynamic.title(name)


def feature(name):
    return allure.feature(name) if allure else _identity_decorator


def story(name):
    return allure.story(name) if allure else _identity_decorator


def severity(level):
    return allure.severity(level) if allure else _identity_decorator


def get_severity_level(name):
    if not allure:
        return name
    return getattr(allure.severity_level, name.upper())


@contextmanager
def step(name):
    if allure:
        with allure.step(name):
            yield
    else:
        yield


def attach_screenshot(file_path, name="screenshot"):
    if not allure:
        return

    path = Path(file_path)
    if path.exists():
        allure.attach.file(str(path), name=name, attachment_type=allure.attachment_type.PNG)


def attach_text(content, name="text"):
    if allure:
        allure.attach(str(content), name=name, attachment_type=allure.attachment_type.TEXT)
