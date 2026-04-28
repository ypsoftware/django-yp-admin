# Installation

!!! warning "v0.1, pre-alpha"
    `django-yp-admin` is a **theme + helpers** layered on top of `django.contrib.admin`, not a full drop-in replacement. Custom `AdminSite` subclasses and third-party admin packages (django-cms, wagtail, allauth, etc.) are **not yet tested**. See [Compatibility](compatibility.md).

## Requirements

- Python 3.10+
- Django 4.2+
- `django-htmx` 1.17+

## Install

```bash
pip install django-yp-admin
```

## Settings

Add `django_yp_admin` to `INSTALLED_APPS` **before** `django.contrib.admin`. Template resolution is order-sensitive — our package must come first so its `admin/base_site.html`, `admin/change_list.html`, etc. take precedence.

```python
INSTALLED_APPS = [
    # ...
    "django_htmx",
    "django_yp_admin",        # before django.contrib.admin
    "django.contrib.admin",
    # ...
]

MIDDLEWARE = [
    # ...
    "django_htmx.middleware.HtmxMiddleware",
]
```

No URL changes required — keep `path("admin/", admin.site.urls)`. We use the stock `admin.site`; we do **not** ship our own `AdminSite`.

## Optional extras

```bash
pip install django-yp-admin[history]        # adds django-simple-history
pip install django-yp-admin[import-export]  # adds django-import-export
pip install django-yp-admin[full]           # both
```

When the optional package is installed, the matching admin integration in `django_yp_admin.contrib` activates automatically via `importlib.util.find_spec`. Basic test coverage exists; production-grade validation is pending. See [Optional extras](optional-extras.md).

## Verify

Run the dev server, visit `/admin/`. You should see the Picnic CSS styling and (on changelists registered with `django_yp_admin.options.ModelAdmin`) htmx-powered filters.

## What is NOT yet supported

If your project uses any of the following, **stay on `django.contrib.admin` for now** — we have not yet validated these:

- A custom `AdminSite` subclass (your own `admin.AdminSite(...)`).
- **django-cms**, **wagtail**, **allauth** admin pages.
- **django-guardian** (`GuardedModelAdmin`), **django-polymorphic** (`PolymorphicChildModelAdmin`).
- End-to-end use of **django-reversion** `VersionAdmin` or **django-import-export** `ImportExportModelAdmin`.
- Legacy JS extensions that call `django.jQuery` — these will break.
