"""Regression tests for template rendering on real admin pages.

These guard against bugs caught by the demo project run that the unit suite
otherwise misses: tests previously did not actually render a change_form or a
sortable inline through the admin, so:

- ``length_is`` filter usage broke the change_form on Django 5.1 (filter
  removed). Now rendered + asserted.
- ``inline_admin_formset.opts.model._meta.app_label`` underscore-prefix
  attribute access in the sortable inline template was rejected by the Django
  template engine on every render. Now exercised through the change_form.
"""

import pytest
from django.contrib import admin as django_admin
from django.contrib.auth import get_user_model
from django.test import Client

from django_yp_admin import ModelAdmin, SortableInline, TabularInline
from tests.testapp.models import Album, Article, Track


pytestmark = pytest.mark.django_db


class _TrackInline(SortableInline, TabularInline):
    model = Track
    sortable_field = "order"
    fields = ("title",)
    extra = 0


class _AlbumAdmin(ModelAdmin):
    inlines = [_TrackInline]


class _ArticleAdmin(ModelAdmin):
    list_display = ("title", "status")


@pytest.fixture
def superuser():
    User = get_user_model()
    return User.objects.create_superuser("root", "r@e.com", "x")


@pytest.fixture
def client_logged(superuser):
    c = Client()
    c.login(username="root", password="x")
    return c


def _reset_template_caches():
    """Force APP_DIRS loaders to drop cached template paths.

    Other tests (test_dropin) toggle INSTALLED_APPS via override_settings;
    the cached app-template-dir list can outlive those overrides, leaving
    stale resolutions for ``admin/yp_admin/edit_inline/tabular_sortable.html``.
    """
    from django.template import engines

    for engine in engines.all():
        for loader in engine.engine.template_loaders:
            if hasattr(loader, "reset"):
                loader.reset()
            for sub in getattr(loader, "loaders", []) or []:
                if hasattr(sub, "reset"):
                    sub.reset()
                if hasattr(sub, "get_dirs"):
                    try:
                        sub.get_dirs.cache_clear()
                    except AttributeError:
                        pass


def _clear_url_caches():
    """Force URL pattern rebuild so the admin re-reads ``site._registry``.

    AdminSite.get_urls() is memoized via the URL resolver. Re-registering
    a model in _registry between tests does NOT propagate to the resolver
    unless the URL caches are cleared.
    """
    from django.urls import clear_url_caches
    from importlib import reload

    clear_url_caches()
    from django.contrib import admin as django_admin_mod

    django_admin_mod.site._registry  # noqa: B018  (touch ensures init)
    # Drop the resolver cache for the test ROOT_URLCONF so admin urls rebuild.
    from django.conf import settings as _settings
    import sys

    mod_name = _settings.ROOT_URLCONF
    if mod_name in sys.modules:
        reload(sys.modules[mod_name])
    clear_url_caches()


@pytest.fixture(autouse=True)
def _register_admins():
    _reset_template_caches()
    site = django_admin.site
    re_register = []
    for model, admin_cls in [(Album, _AlbumAdmin), (Article, _ArticleAdmin)]:
        if site.is_registered(model):
            re_register.append((model, site._registry[model].__class__))
            site.unregister(model)
        site.register(model, admin_cls)
    _clear_url_caches()
    yield
    for model, _ in [(Album, None), (Article, None)]:
        if site.is_registered(model):
            site.unregister(model)
    for model, original_cls in re_register:
        site.register(model, original_cls)


def test_change_form_renders_under_django_51(client_logged):
    """Renders change_form which loads our ``admin/includes/fieldset.html``.

    On Django 5.1 the ``length_is`` filter was removed; if the template still
    used it, this would raise ``TemplateSyntaxError: Invalid filter``.
    """
    article = Article.objects.create(title="x", body="b")
    resp = client_logged.get(f"/admin/testapp/article/{article.pk}/change/")
    assert resp.status_code == 200
    assert b"errornote" in resp.content or b"form-row" in resp.content


def test_change_form_add_renders(client_logged):
    """Add form must also render — exercises fieldset rendering with no
    bound instance."""
    resp = client_logged.get("/admin/testapp/article/add/")
    assert resp.status_code == 200


def test_sortable_inline_renders_change_form(client_logged):
    """Renders the change_form for an Album with TrackInline using our
    sortable template. Catches the ``_meta`` underscore-attribute bug.
    """
    album = Album.objects.create(name="A")
    Track.objects.create(album=album, title="t1", order=0)
    resp = client_logged.get(f"/admin/testapp/album/{album.pk}/change/")
    assert resp.status_code == 200
    assert b"yp-sortable-group" in resp.content
    assert b'data-yp-sortable="true"' in resp.content
