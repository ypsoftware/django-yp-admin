"""Tests for in-house Version snapshot/revert."""

import json

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.http import Http404
from django.test import RequestFactory

from django_yp_admin.history.models import Revision, Version
from django_yp_admin.views.versioning import revert_view
from tests.testapp.models import Article


pytestmark = pytest.mark.django_db


def _snapshot(obj, comment=""):
    revision = Revision.objects.create(comment=comment)
    serialized = serializers.serialize("json", [obj])
    return Version.objects.create(
        revision=revision,
        content_type=ContentType.objects.get_for_model(obj.__class__),
        object_id=str(obj.pk),
        serialized_data=json.loads(serialized),
        object_repr=str(obj)[:255],
    )


def test_save_creates_version():
    article = Article.objects.create(title="hello", body="world")
    v = _snapshot(article, comment="Added")
    assert v.pk is not None
    assert v.object_repr == "hello"
    assert v.revision.comment == "Added"
    assert Version.objects.count() == 1


def test_revert_restores_data():
    article = Article.objects.create(title="original", body="v1")
    v = _snapshot(article)

    # Mutate
    article.title = "mutated"
    article.body = "v2"
    article.save()

    # Revert (must pass allowed_fields after FIX-1)
    restored = v.revert(allowed_fields={"title", "body"})
    assert restored.title == "original"
    assert restored.body == "v1"
    article.refresh_from_db()
    assert article.title == "original"
    assert article.body == "v1"


def test_revert_refuses_non_superuser_without_allowed_fields():
    """FIX-1: revert() must refuse to mass-assign all fields."""
    article = Article.objects.create(title="t", body="b")
    v = _snapshot(article)
    with pytest.raises(PermissionError):
        v.revert()
    with pytest.raises(PermissionError):
        v.revert(allowed_fields=None)


def test_revert_with_allowed_fields_only_restores_those():
    """FIX-1: only fields listed in allowed_fields are written back."""
    article = Article.objects.create(title="orig", body="orig-body", status="draft")
    v = _snapshot(article)

    article.title = "mutated"
    article.body = "mutated-body"
    article.status = "published"
    article.save()

    # Only allow title; body and status must remain mutated.
    v.revert(allowed_fields={"title"})
    article.refresh_from_db()
    assert article.title == "orig"
    assert article.body == "mutated-body"
    assert article.status == "published"


def test_save_model_atomic_rollback_on_snapshot_failure():
    """FIX-3: save_model must roll back the model save when snapshot fails."""
    from unittest.mock import patch

    from django.contrib.admin.sites import AdminSite
    from django.contrib.auth.models import AnonymousUser

    from django_yp_admin.history.admin import VersionAdmin

    class _Base:
        def save_model(self, request, obj, form, change):
            obj.save()

    class ArticleAdmin(VersionAdmin, _Base):
        pass

    admin_instance = ArticleAdmin()
    admin_instance.model = Article
    admin_instance.admin_site = AdminSite()

    request = RequestFactory().post("/")
    request.user = AnonymousUser()

    article = Article(title="should-not-persist", body="x")

    with patch.object(Version.objects, "create", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError):
            admin_instance.save_model(request, article, form=None, change=False)

    # Atomic rollback: nothing committed.
    assert not Article.objects.filter(title="should-not-persist").exists()
    assert Revision.objects.count() == 0
    assert Version.objects.count() == 0


def test_history_view_requires_view_permission():
    """FIX-4: history_view must call has_view_permission."""
    from django.contrib.admin.sites import AdminSite
    from django.contrib.auth.models import AnonymousUser
    from django.core.exceptions import PermissionDenied

    from django_yp_admin.history.admin import VersionAdmin

    class _Base:
        def get_object(self, request, object_id, from_field=None):
            return Article.objects.filter(pk=object_id).first()

        def has_view_permission(self, request, obj=None):
            return False

    class ArticleAdmin(VersionAdmin, _Base):
        pass

    admin_instance = ArticleAdmin()
    admin_instance.model = Article
    admin_instance.admin_site = AdminSite()

    article = Article.objects.create(title="t", body="b")
    request = RequestFactory().get("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        admin_instance.history_view(request, str(article.pk))


def test_revert_view_non_superuser_cannot_restore_readonly_fields():
    """revert_view must scope allowed_fields to (get_fields - get_readonly_fields).

    A non-superuser with change_* perm reverting against a ModelAdmin that
    marks `status` readonly must NOT see `status` rolled back, even though
    the snapshot contains it. This is the in-view analogue of FIX-1.
    """
    from django.contrib import admin as django_admin
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Permission
    from django.test import Client

    from django_yp_admin.options import ModelAdmin

    # The view computes allowed_fields by looking up the ModelAdmin on
    # `django.contrib.admin.site` (the default site). Re-register Article
    # there with a `status` readonly_fields so allowed_fields excludes it.
    class ArticleAdmin(ModelAdmin):
        fields = ("title", "body", "status")
        readonly_fields = ("status",)

    django_admin.site.unregister(Article)
    django_admin.site.register(Article, ArticleAdmin)
    try:
        User = get_user_model()
        user = User.objects.create_user(username="staffer", password="pw", is_staff=True)
        user.user_permissions.add(Permission.objects.get(content_type__app_label="testapp", codename="change_article"))
        client = Client()
        client.login(username="staffer", password="pw")

        article = Article.objects.create(title="orig", body="orig-body", status="draft")
        v = _snapshot(article)
        article.title = "mutated"
        article.body = "mutated-body"
        article.status = "published"
        article.save()

        url = f"/yp-admin/testapp/article/{article.pk}/revert/{v.pk}/"
        response = client.post(url)
        assert response.status_code == 302
        article.refresh_from_db()
        # title/body restored; status protected (readonly → not in allowed_fields).
        assert article.title == "orig"
        assert article.body == "orig-body"
        assert article.status == "published"
    finally:
        django_admin.site.unregister(Article)
        django_admin.site.register(Article)


def test_revert_view_non_superuser_blocked_when_no_modeladmin():
    """When no ModelAdmin is registered (allowed_fields stays None), the view
    refuses for non-superusers and requires superuser explicitly."""
    from django.contrib import admin as django_admin
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Permission
    from django.test import Client

    from django_yp_admin.sites import site as yp_site

    default_was = django_admin.site.is_registered(Article)
    yp_was = yp_site.is_registered(Article)
    if default_was:
        django_admin.site.unregister(Article)
    if yp_was:
        yp_site.unregister(Article)
    try:
        User = get_user_model()
        user = User.objects.create_user(username="halfop", password="pw", is_staff=True)
        user.user_permissions.add(Permission.objects.get(content_type__app_label="testapp", codename="change_article"))
        client = Client()
        client.login(username="halfop", password="pw")

        article = Article.objects.create(title="orig", body="v1")
        v = _snapshot(article)

        url = f"/yp-admin/testapp/article/{article.pk}/revert/{v.pk}/"
        response = client.post(url)
        # PermissionDenied → 403.
        assert response.status_code == 403
    finally:
        if default_was:
            django_admin.site.register(Article)
        if yp_was:
            yp_site.register(Article)


def test_revert_view_superuser_allowed_fields_full_set():
    """With a registered ModelAdmin and no readonly_fields, superuser revert
    pulls allowed_fields from get_fields() and restores all of them."""
    from django.contrib.auth import get_user_model
    from django.test import Client

    from django.contrib import admin as django_admin

    from django_yp_admin.options import ModelAdmin as YpModelAdmin

    class ArticleAdmin(YpModelAdmin):
        fields = ("title", "body", "status")
        readonly_fields = ()

    django_admin.site.unregister(Article)
    django_admin.site.register(Article, ArticleAdmin)
    try:
        User = get_user_model()
        User.objects.create_superuser(username="root", password="pw", email="r@r.com")
        client = Client()
        client.login(username="root", password="pw")

        article = Article.objects.create(title="orig", body="b1", status="draft")
        v = _snapshot(article)
        article.title = "mutated"
        article.body = "b2"
        article.status = "published"
        article.save()

        url = f"/yp-admin/testapp/article/{article.pk}/revert/{v.pk}/"
        response = client.post(url)
        assert response.status_code == 302
        article.refresh_from_db()
        assert article.title == "orig"
        assert article.body == "b1"
        assert article.status == "draft"
    finally:
        django_admin.site.unregister(Article)
        django_admin.site.register(Article)


def test_revert_object_id_too_long_returns_404():
    User = get_user_model()
    user = User.objects.create_user(username="staff", password="x", is_staff=True, is_superuser=True)
    rf = RequestFactory()
    request = rf.post("/ignored/")
    request.user = user

    long_id = "a" * 256
    with pytest.raises(Http404):
        revert_view(
            request,
            app_label="testapp",
            model_name="article",
            object_id=long_id,
            version_id=1,
        )
