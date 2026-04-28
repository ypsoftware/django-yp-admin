"""Minimal Django settings for running the test suite."""

SECRET_KEY = "test"
DEBUG = False
USE_TZ = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# NOTE: `django_yp_admin` MUST come BEFORE `django.contrib.admin` so that
# APP_DIRS template resolution picks up our `admin/base.html`, `admin/base_site.html`,
# and `admin/login.html` overrides first (these live at the root admin/ path
# precisely to shadow Django's globally).
#
# Per-ModelAdmin overrides (change_list, change_form) live under
# `admin/yp_admin/` and are wired via `change_list_template` /
# `change_form_template` defaults on `django_yp_admin.options.ModelAdmin`,
# so they can `{% extends "admin/change_list.html" %}` (Django's) without
# self-recursion regardless of INSTALLED_APPS order.
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "django_htmx",
    "django_yp_admin",
    "django.contrib.admin",
    "tests.testapp",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ]
        },
    }
]

ROOT_URLCONF = "tests.urls"
STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
