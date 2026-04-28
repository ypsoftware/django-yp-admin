import django
from django.conf import settings


def pytest_configure():
    pass  # settings already loaded via DJANGO_SETTINGS_MODULE in pyproject.toml
