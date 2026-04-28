# django-yp-admin

**An htmx-powered theme + helpers for `django.contrib.admin`. Two dependencies. Zero jQuery.**

`django-yp-admin` is an **htmx-powered admin theme plus a small set of helpers** for `django.contrib.admin`. It ships template overrides (Picnic CSS, native HTML5 widgets, htmx) and a handful of reusable abstract models and admin mixins (OrderedModel, SingletonModel, lightweight history, htmx widgets). It is **not** a full drop-in replacement for `django.contrib.admin` — it layers on top of the stock `AdminSite`.

> **Status: v0.1, pre-alpha.** ~19 tests in the suite. We have **not** yet validated against custom `AdminSite` subclasses or third-party admin packages (django-cms, wagtail, allauth, django-guardian, django-polymorphic, etc.). API will change.

## What you get

- **htmx-powered theme.** Template overrides for changelist/change form/login. Picnic CSS base, themable via CSS custom properties. Dark mode via `prefers-color-scheme`.
- **No jQuery.** ~62KB gzipped of total JS instead of ~250KB of jQuery + Select2 + xregexp.
- **Two mandatory deps.** Django + `django-htmx`. Optional extras when you want them.
- **Native HTML5.** `<input type="date">`, `<dialog>`, `<details>` instead of jQuery widgets.
- **Helpers (opt-in).** Abstract models and admin mixins you can mix into your own code:
  - `OrderedModel` + drag-and-drop admin
  - `SingletonModel` + admin
  - Lightweight history (Revision/Version)
  - htmx-native filters (Dropdown, DateRange, DateTimeRange, NumericRange)
  - htmx + Tom Select autocomplete widget
  - htmx-native nested/sortable inlines

## What is NOT yet supported / tested

This is v0.1. The following are **roadmap, not promises**:

- Custom `AdminSite` subclasses — untested.
- **django-cms**, **wagtail**, **allauth** admin integrations — untested.
- **django-guardian** (`GuardedModelAdmin`), **django-polymorphic** (`PolymorphicChildModelAdmin`), **django-reversion** (`VersionAdmin`), **django-import-export** (`ImportExportModelAdmin`) — not yet validated end-to-end.
- Third-party themes that target legacy admin CSS classes — selectors are preserved as DOM hooks but not regression-tested.
- Legacy admin JS extensions that depend on `django.jQuery` — will break.

If you depend on any of the above, **stay on `django.contrib.admin` for now** and watch this project.

## Optional extras

```bash
pip install django-yp-admin[history]        # django-simple-history
pip install django-yp-admin[import-export]  # django-import-export
pip install django-yp-admin[full]           # all of the above
```

When the optional package is installed, the matching admin integration in `django_yp_admin.contrib` activates automatically via `importlib.util.find_spec`. These integrations are exercised by the test suite at a basic level — production hardening pending.

## Quickstart

```bash
pip install django-yp-admin
```

```python
INSTALLED_APPS = [
    "django_yp_admin",        # before django.contrib.admin
    "django.contrib.admin",
    "django_htmx",
    # ...
]

MIDDLEWARE = [
    # ...
    "django_htmx.middleware.HtmxMiddleware",
]
```

Open `/admin/`. Stock admins keep working with the new theme. To opt into htmx-native filters/widgets per model, switch your `ModelAdmin` base class to `django_yp_admin.options.ModelAdmin`.

## Browser support

Modern browsers only — last 3 years of releases.

| Browser | Minimum |
|---|---|
| Firefox | 115 (ESR, July 2023) |
| Chrome | 115 (July 2023) |
| Safari | 16.4 (March 2023) |
| Edge | 115 (Chromium) |

This unlocks native `<dialog>`, `:has()`, CSS nesting, container queries, reliable date inputs, and ES2022 — which is why the JS bundle is so small.

If you need legacy browser support, stick with `django.contrib.admin`.

## Stack

| Layer | Tool | Size (gzip) |
|---|---|---:|
| AJAX | htmx | ~14KB |
| Local UI state (optional) | Alpine.js | ~15KB |
| Autocomplete | Tom Select | ~25KB |
| CSS base | Picnic CSS | ~10KB |
| Our code | TypeScript bundled with Bun | ~8KB |
| **Total** | | **~62KB** |

vs the default admin's ~250KB of jQuery + Select2 + xregexp + custom JS.

## Status

**v0.1, pre-alpha.** ~19 tests. API will change. Star the repo, file issues, send PRs. Real-world compat reports against custom `AdminSite` and third-party admin packages are especially welcome.

## License

MIT. © Yp Software <info@ypsoftware.com.py>.

## Links

- Source: https://github.com/ypsoftware/django-yp-admin
- Docs: https://django-yp-admin.readthedocs.io/
- Issues: https://github.com/ypsoftware/django-yp-admin/issues
