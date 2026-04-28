"""Verify drop-in compatibility: ModelAdmin subclass, template resolution."""
from django.contrib import admin as django_admin
from django.contrib.admin import ModelAdmin as DjangoModelAdmin
from django.template.loader import get_template
from django.test import override_settings

import django_yp_admin
from django_yp_admin.options import ModelAdmin
from django_yp_admin.sites import site as yp_site


def test_modeladmin_is_django_subclass():
    assert issubclass(ModelAdmin, DjangoModelAdmin)


def test_base_site_template_resolves_to_yp_admin():
    tpl = get_template("admin/base_site.html")
    # Our package is listed before django.contrib.admin in INSTALLED_APPS,
    # so APP_DIRS resolution should pick up our override first.
    origin = tpl.origin.name
    assert "django_yp_admin" in origin, f"got {origin}"


def test_modeladmin_has_htmx_flags():
    assert hasattr(ModelAdmin, "htmx_changelist")
    assert hasattr(ModelAdmin, "htmx_inline_save")
    assert hasattr(ModelAdmin, "versioning")


def test_modeladmin_default_templates_point_to_yp_admin_subfolder():
    assert ModelAdmin.change_list_template == "admin/yp_admin/change_list.html"
    assert ModelAdmin.change_form_template == "admin/yp_admin/change_form.html"


def test_change_list_template_renders_without_recursion():
    """Regression for FIX-12: our change_list at admin/yp_admin/ extends
    Django's admin/change_list.html. Loading and rendering must not blow the
    template recursion stack regardless of INSTALLED_APPS order."""
    from django.template import Context, Template

    tpl = get_template("admin/yp_admin/change_list.html")
    # Must resolve to our package, not Django's.
    assert "django_yp_admin" in tpl.origin.name, tpl.origin.name
    # Render a stub — we just need to confirm no infinite recursion. Errors
    # from missing context vars are fine; a RecursionError is the failure mode.
    try:
        tpl.render({})
    except RecursionError:
        raise AssertionError("change_list.html recurses into itself")
    except Exception:
        pass

    # Same for change_form.
    tpl2 = get_template("admin/yp_admin/change_form.html")
    assert "django_yp_admin" in tpl2.origin.name, tpl2.origin.name
    try:
        tpl2.render({})
    except RecursionError:
        raise AssertionError("change_form.html recurses into itself")
    except Exception:
        pass

    # And the bare Django path should now resolve to Django's stock template
    # (since we no longer shadow it at admin/change_list.html).
    bare = get_template("admin/change_list.html")
    assert "django_yp_admin" not in bare.origin.name, bare.origin.name


def test_register_uses_default_site():
    """FIX-13: ``django_yp_admin.register`` is re-exported from
    ``django.contrib.admin`` and decorates onto the default contrib admin site,
    NOT onto the opt-in ``YpAdminSite`` exposed as ``django_yp_admin.site``."""
    from tests.testapp.models import Album

    # Clean up any prior registration so the test is order-independent.
    if django_admin.site.is_registered(Album):
        django_admin.site.unregister(Album)
    if yp_site.is_registered(Album):
        yp_site.unregister(Album)

    # Sanity: the re-exported callable IS Django's.
    assert django_yp_admin.register is django_admin.register

    @django_yp_admin.register(Album)
    class AlbumAdmin(ModelAdmin):
        pass

    try:
        assert Album in django_admin.site._registry
        assert Album not in yp_site._registry
    finally:
        django_admin.site.unregister(Album)


# --- INSTALLED_APPS ordering coverage --------------------------------------

_APPS_AFTER = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "django_htmx",
    "django.contrib.admin",
    "django_yp_admin",
    "tests.testapp",
]

_APPS_BEFORE = [
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


def _clear_template_caches():
    """Force APP_DIRS loaders to forget their cached app-template-dir list."""
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
                        sub.get_dirs.cache_clear()  # type: ignore[attr-defined]
                    except AttributeError:
                        pass


def test_templates_resolve_with_yp_admin_before_contrib_admin():
    """Default ordering: our overrides at admin/base_site.html win."""
    with override_settings(INSTALLED_APPS=_APPS_BEFORE):
        _clear_template_caches()
        try:
            tpl = get_template("admin/base_site.html")
            assert "django_yp_admin" in tpl.origin.name, tpl.origin.name
            yp_tpl = get_template("admin/yp_admin/change_list.html")
            assert "django_yp_admin" in yp_tpl.origin.name
        finally:
            _clear_template_caches()


def test_templates_resolve_with_yp_admin_after_contrib_admin():
    """Reversed ordering: yp_admin/* still resolves to us (we own that path
    exclusively); admin/change_list.html falls through to Django. Neither
    should infinite-recurse."""
    with override_settings(INSTALLED_APPS=_APPS_AFTER):
        _clear_template_caches()
        try:
            yp_tpl = get_template("admin/yp_admin/change_list.html")
            assert "django_yp_admin" in yp_tpl.origin.name, yp_tpl.origin.name
            try:
                yp_tpl.render({})
            except RecursionError:
                raise AssertionError("yp_admin/change_list.html recurses")
            except Exception:
                pass

            bare = get_template("admin/change_list.html")
            try:
                bare.render({})
            except RecursionError:
                raise AssertionError("admin/change_list.html recurses")
            except Exception:
                pass
            assert bare is not None
        finally:
            _clear_template_caches()


def test_modeladmin_change_list_template_default_is_yp_admin_subfolder():
    assert ModelAdmin.change_list_template == "admin/yp_admin/change_list.html"


def test_modeladmin_change_form_template_default_is_yp_admin_subfolder():
    assert ModelAdmin.change_form_template == "admin/yp_admin/change_form.html"
