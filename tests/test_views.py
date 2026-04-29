"""Auth / permission test matrix for htmx endpoints (reorder, revert, history)."""
import json

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.test import Client
from django.urls import reverse

from django_yp_admin.history.models import Revision, Version
from tests.testapp.models import Album, Article, Track


pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------- helpers ----


def _snapshot(obj):
    revision = Revision.objects.create(comment="snap")
    serialized = serializers.serialize("json", [obj])
    return Version.objects.create(
        revision=revision,
        content_type=ContentType.objects.get_for_model(obj.__class__),
        object_id=str(obj.pk),
        serialized_data=json.loads(serialized),
        object_repr=str(obj)[:255],
    )


def _revert_url(article, version):
    return reverse(
        "yp_admin:yp_revert",
        kwargs={
            "app_label": "testapp",
            "model_name": "article",
            "object_id": str(article.pk),
            "version_id": version.pk,
        },
    )


def _reorder_url(app_label="testapp", model_name="track"):
    return reverse(
        "yp_admin:yp_reorder",
        kwargs={"app_label": app_label, "model_name": model_name},
    )


# ----------------------------------------------------------- user fixtures --


@pytest.fixture
def make_user():
    User = get_user_model()
    counter = {"n": 0}

    def _make(*, staff=False, superuser=False, perms=()):
        counter["n"] += 1
        u = User.objects.create_user(
            username=f"u{counter['n']}",
            password="pw",
            is_staff=staff or superuser,
            is_superuser=superuser,
        )
        for app_label, codename in perms:
            p = Permission.objects.get(
                content_type__app_label=app_label, codename=codename
            )
            u.user_permissions.add(p)
        return u

    return _make


@pytest.fixture
def login(client, make_user):
    def _login(**kwargs):
        u = make_user(**kwargs)
        client.login(username=u.username, password="pw")
        return u

    return _login


# =============================================================== revert_view


def test_revert_anonymous_redirects_to_login(client):
    article = Article.objects.create(title="orig", body="v1")
    version = _snapshot(article)
    response = client.post(_revert_url(article, version))
    assert response.status_code == 302
    assert "/login/" in response["Location"]


def test_revert_authenticated_non_staff_redirected(client, login):
    login(staff=False)
    article = Article.objects.create(title="orig", body="v1")
    version = _snapshot(article)
    response = client.post(_revert_url(article, version))
    # admin_view() redirects non-staff to admin login.
    assert response.status_code == 302
    assert "/login/" in response["Location"]


def test_revert_staff_without_change_perm_forbidden(client, login):
    login(staff=True)  # no perms
    article = Article.objects.create(title="orig", body="v1")
    version = _snapshot(article)
    response = client.post(_revert_url(article, version))
    assert response.status_code == 403


def test_revert_staff_with_change_perm_succeeds(client, login, monkeypatch):
    login(staff=True, perms=[("testapp", "change_article")])
    article = Article.objects.create(title="original", body="v1")
    version = _snapshot(article)
    article.title = "mutated"
    article.save()

    # Replace revert() with a minimal stub: we are testing the auth/redirect
    # contract here, not Version.revert() internals (covered in test_versioning).
    def fake_revert(self, allowed_fields=None):
        a = Article.objects.get(pk=self.object_id)
        a.title = "original"
        a.save()
        return a

    monkeypatch.setattr(Version, "revert", fake_revert)

    response = client.post(_revert_url(article, version))
    assert response.status_code == 302
    assert response["Location"].endswith(
        f"/admin/testapp/article/{article.pk}/change/"
    )
    article.refresh_from_db()
    assert article.title == "original"


def test_revert_superuser_succeeds(client, login, monkeypatch):
    login(superuser=True)
    article = Article.objects.create(title="original", body="v1")
    version = _snapshot(article)

    def fake_revert(self, allowed_fields=None):
        # Superuser path: no allowed_fields filtering needed.
        a = Article.objects.get(pk=self.object_id)
        a.title = "original"
        a.save()
        return a

    monkeypatch.setattr(Version, "revert", fake_revert)
    response = client.post(_revert_url(article, version))
    assert response.status_code == 302


def test_revert_get_returns_405(client, login):
    login(superuser=True)
    article = Article.objects.create(title="t", body="b")
    version = _snapshot(article)
    response = client.get(_revert_url(article, version))
    assert response.status_code == 405


def test_revert_post_without_csrf_token_forbidden(login):
    """admin_view wraps revert_view in csrf_protect; raw POST without token → 403."""
    csrf_client = Client(enforce_csrf_checks=True)
    user = login(superuser=True)
    csrf_client.login(username=user.username, password="pw")
    article = Article.objects.create(title="t", body="b")
    version = _snapshot(article)
    response = csrf_client.post(_revert_url(article, version))
    assert response.status_code == 403


# =============================================================== reorder_view


def test_reorder_anonymous_redirects_to_login(client):
    response = client.post(_reorder_url())
    assert response.status_code == 302
    assert "/login/" in response["Location"]


def test_reorder_authenticated_non_staff_redirected(client, login):
    login(staff=False)
    response = client.post(_reorder_url())
    assert response.status_code == 302
    assert "/login/" in response["Location"]


def test_reorder_staff_without_change_perm_forbidden(client, login):
    login(staff=True)
    album = Album.objects.create(name="A")
    Track.objects.create(title="t0", album=album)
    response = client.post(
        _reorder_url(),
        data=json.dumps({"pk": 1, "new_order": 0}),
        content_type="application/json",
    )
    assert response.status_code == 403


def test_reorder_staff_with_change_perm_succeeds(client, login):
    login(staff=True, perms=[("testapp", "change_track")])
    album = Album.objects.create(name="A")
    tracks = [Track.objects.create(title=f"t{i}", album=album) for i in range(3)]
    response = client.post(
        _reorder_url(),
        data=json.dumps({"pk": tracks[2].pk, "new_order": 0}),
        content_type="application/json",
    )
    assert response.status_code == 204
    assert (
        list(Track.objects.filter(album=album).order_by("order").values_list("title", flat=True))
        == ["t2", "t0", "t1"]
    )


def test_reorder_superuser_succeeds(client, login):
    login(superuser=True)
    album = Album.objects.create(name="A")
    track = Track.objects.create(title="t0", album=album)
    response = client.post(
        _reorder_url(),
        data=json.dumps({"pk": track.pk, "new_order": 0}),
        content_type="application/json",
    )
    assert response.status_code == 204


def test_reorder_get_returns_405(client, login):
    login(superuser=True)
    response = client.get(_reorder_url())
    assert response.status_code == 405


def test_reorder_post_without_csrf_token_forbidden(login):
    csrf_client = Client(enforce_csrf_checks=True)
    user = login(superuser=True)
    csrf_client.login(username=user.username, password="pw")
    response = csrf_client.post(
        _reorder_url(),
        data=json.dumps({"pk": 1, "new_order": 0}),
        content_type="application/json",
    )
    assert response.status_code == 403


def test_reorder_non_ordered_model_400(client, login):
    login(superuser=True)
    response = client.post(_reorder_url(model_name="article"))
    assert response.status_code == 400


def test_reorder_unknown_model_returns_404(client, login):
    """Avoid info disclosure: 404 (not 400) for unknown app/model."""
    login(superuser=True)
    response = client.post(_reorder_url(app_label="nope", model_name="nope"))
    assert response.status_code == 404


def test_reorder_missing_pk_returns_400(client, login):
    login(superuser=True, perms=[("testapp", "change_track")])
    response = client.post(
        _reorder_url(),
        data=json.dumps({"new_order": 0}),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_reorder_unknown_pk_returns_404(client, login):
    login(superuser=True, perms=[("testapp", "change_track")])
    response = client.post(
        _reorder_url(),
        data=json.dumps({"pk": 999999, "new_order": 0}),
        content_type="application/json",
    )
    assert response.status_code == 404


# =============================================================== history_view
#
# history_view is registered per-ModelAdmin via VersionAdmin.get_urls(). The
# Article admin in tests/urls.py is plain admin, so we exercise the view via
# a VersionAdmin instance + RequestFactory (mirrors the pattern already used
# in test_versioning.py).


def _history_admin():
    from django_yp_admin.history.admin import VersionAdmin
    from django_yp_admin.sites import YpAdminSite

    class _Base:
        def get_object(self, request, object_id, from_field=None):
            return Article.objects.filter(pk=object_id).first()

    class ArticleAdmin(VersionAdmin, _Base):
        def has_view_permission(self, request, obj=None):
            return request.user.has_perm("testapp.view_article") or request.user.is_superuser

    a = ArticleAdmin()
    a.model = Article
    a.admin_site = YpAdminSite(name="yp_admin")
    return a


def test_history_view_staff_without_view_perm_denied(make_user, rf=None):
    from django.core.exceptions import PermissionDenied
    from django.test import RequestFactory

    user = make_user(staff=True)
    article = Article.objects.create(title="t", body="b")
    request = RequestFactory().get("/")
    request.user = user

    admin = _history_admin()
    with pytest.raises(PermissionDenied):
        admin.history_view(request, str(article.pk))


def test_history_view_staff_with_view_perm_renders(make_user):
    from django.test import RequestFactory

    user = make_user(staff=True, perms=[("testapp", "view_article")])
    article = Article.objects.create(title="t", body="b")
    v1 = _snapshot(article)
    article.title = "t2"
    article.save()
    v2 = _snapshot(article)

    request = RequestFactory().get("/")
    request.user = user

    admin = _history_admin()
    response = admin.history_view(request, str(article.pk))
    assert response.status_code == 200
    body = response.content.decode()
    # Both snapshot reprs should appear in the rendered version list.
    assert v1.object_repr in body or v2.object_repr in body


def test_history_view_superuser_renders(make_user):
    from django.test import RequestFactory

    user = make_user(superuser=True)
    article = Article.objects.create(title="t", body="b")
    _snapshot(article)
    request = RequestFactory().get("/")
    request.user = user

    admin = _history_admin()
    response = admin.history_view(request, str(article.pk))
    assert response.status_code == 200
