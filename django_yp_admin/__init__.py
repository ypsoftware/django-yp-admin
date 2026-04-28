"""django-yp-admin — htmx-powered theme + helpers for django.contrib.admin.

Top-level re-exports use lazy `__getattr__` so importing the package does not
force model class definition before Django's app registry is ready.

Re-export semantics
-------------------

`register` is re-exported directly from ``django.contrib.admin``. It decorates
models onto the **default** ``django.contrib.admin.site`` registry. This is the
recommended path for the package's primary positioning as a theme + helpers
layer that runs on top of the stock ``AdminSite``.

`site` is the **opt-in** ``YpAdminSite`` instance (``name="yp_admin"``). It is
NOT used by ``register``. Users only need ``site`` when they explicitly mount a
custom admin site (e.g. ``path("yp-admin/", django_yp_admin.site.urls)``); in
that case, register models with ``django_yp_admin.site.register(Model, Admin)``
directly. ``django_yp_admin.register`` and ``django_yp_admin.site`` are NOT a
paired API.
"""

from __future__ import annotations

__version__ = "0.1.0a2"

_LAZY = {
    "ModelAdmin": ("django_yp_admin.options", "ModelAdmin"),
    "StackedInline": ("django_yp_admin.options", "StackedInline"),
    "TabularInline": ("django_yp_admin.options", "TabularInline"),
    "YpAdminSite": ("django_yp_admin.sites", "YpAdminSite"),
    "site": ("django_yp_admin.sites", "site"),
    "register": ("django.contrib.admin", "register"),
    "OrderedModel": ("django_yp_admin.models", "OrderedModel"),
    "SingletonModel": ("django_yp_admin.models", "SingletonModel"),
    "Revision": ("django_yp_admin.history.models", "Revision"),
    "Version": ("django_yp_admin.history.models", "Version"),
    "VersionAdmin": ("django_yp_admin.history.admin", "VersionAdmin"),
    "HtmxAutocomplete": ("django_yp_admin.widgets", "HtmxAutocomplete"),
    "HtmxAutocompleteMultiple": ("django_yp_admin.widgets", "HtmxAutocompleteMultiple"),
    "SortableInline": ("django_yp_admin.widgets", "SortableInline"),
    "NestedInline": ("django_yp_admin.widgets", "NestedInline"),
}

__all__ = list(_LAZY.keys())


def __getattr__(name: str):
    if name in _LAZY:
        from importlib import import_module

        module_path, attr = _LAZY[name]
        return getattr(import_module(module_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
