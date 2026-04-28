"""Smoke tests. Real coverage lands as features ship."""
from pathlib import Path

import django_yp_admin

PKG_ROOT = Path(django_yp_admin.__file__).resolve().parent
STATIC = PKG_ROOT / "static" / "yp_admin"


def test_version():
    assert django_yp_admin.__version__


def test_app_imports():
    from django_yp_admin import admin

    assert admin.YpAdminSite
    assert admin.ModelAdmin


def test_yp_admin_js_bundle_present():
    bundle = STATIC / "js" / "yp-admin.js"
    assert bundle.is_file(), f"missing bundle: {bundle}"
    assert bundle.stat().st_size > 0, "bundle is empty"


def test_yp_admin_alpine_bundle_present():
    bundle = STATIC / "js" / "yp-admin-alpine.js"
    assert bundle.is_file(), f"missing alpine bundle: {bundle}"
    assert bundle.stat().st_size > 0, "alpine bundle is empty"


def test_yp_admin_css_present():
    css = STATIC / "css" / "yp-admin.css"
    assert css.is_file(), f"missing css: {css}"
    assert css.stat().st_size > 0, "css is empty"


def test_modeladmin_media_includes_bundle():
    """Instantiated ModelAdmin should ship the yp-admin.js bundle in media."""
    from django.contrib import admin as django_admin

    from django_yp_admin.options import ModelAdmin
    from tests.testapp.models import Album

    class _AlbumAdmin(ModelAdmin):
        pass

    instance = _AlbumAdmin(Album, django_admin.site)
    js_paths = [str(p) for p in instance.media._js]
    assert any("yp_admin/js/yp-admin.js" in p for p in js_paths), js_paths
