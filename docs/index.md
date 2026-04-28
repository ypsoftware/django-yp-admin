# django-yp-admin

**An htmx-powered theme + helpers for `django.contrib.admin`. Two dependencies. Zero jQuery.**

`django-yp-admin` is an **htmx-powered admin theme plus a small set of helpers** for `django.contrib.admin`. It ships template overrides (Picnic CSS, native HTML5 widgets, htmx) and reusable abstract models and admin mixins (OrderedModel, SingletonModel, lightweight history, htmx widgets). It layers on top of the stock `AdminSite`; it is **not** a full drop-in replacement.

!!! note "v0.1"
    104 tests across Python 3.11–3.14 × Django 4.2 / 5.2 / 6.0. Custom `AdminSite` subclasses and third-party admin packages (**django-cms**, **wagtail**, **allauth**, **django-guardian**, **django-polymorphic**, **django-reversion**, **django-import-export** end-to-end) are **not yet validated**. See [Compatibility](compatibility.md).

## Visual tour

![Dashboard](screenshots/dashboard.png)

Changelist with filter sidebar, range filters, multi-select:

![Changelist](screenshots/changelist-blog.png)

## What you get

- **htmx-powered theme.** Template overrides for changelist/change form/login. Picnic CSS base, themable via CSS custom properties. Dark mode via `prefers-color-scheme`.
- **No jQuery.** ~62KB gzipped of total JS instead of ~250KB.
- **Two mandatory deps.** Django + `django-htmx`. Optional extras when you want them.
- **Native HTML5.** `<input type="date">`, `<dialog>`, `<details>` instead of jQuery widgets.
- **Helpers (opt-in).** `OrderedModel`, `SingletonModel`, lightweight history, htmx filters, htmx + Tom Select autocomplete, htmx-native nested/sortable inlines.

## Install

```bash
pip install django-yp-admin
```

## Quickstart

```python
INSTALLED_APPS = [
    "django_yp_admin",   # before django.contrib.admin
    "django.contrib.admin",
    "django_htmx",
    # ...
]
```

Open `/admin/`. Stock admins keep working with the new theme. To opt into htmx-native filters/widgets per model, switch your `ModelAdmin` base class to `django_yp_admin.options.ModelAdmin`.

## Next steps

- [Installation](installation.md)
- [Quickstart](quickstart.md)
- [ModelAdmin reference](modeladmin.md)
- [Filters](filters.md)
- [Singletons](singleton.md)
- [Ordered models](ordered.md)
- [Versioning](versioning.md)
- [Optional extras](optional-extras.md)
- [Browser support](browser-support.md)
- [Compatibility](compatibility.md)
