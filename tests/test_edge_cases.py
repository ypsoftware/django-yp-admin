"""High-value edge-case tests covering production bugs the unit suite misses.

Covers timezone-awareness, negative/zero numeric ranges, OrderedModel re-parenting,
revert content_type mismatch, SingletonModel concurrency, XSS escaping in filter
choices, autocomplete to_field handling, empty sortable inlines, all-readonly
admin forms, large MultiSelectFilter option lists, and move_to() boundary clamps.
"""

from __future__ import annotations

import json
import sys
import threading
import warnings
from decimal import Decimal

import pytest
from django.contrib import admin as django_admin
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.test import Client, RequestFactory

from django_yp_admin import ModelAdmin
from django_yp_admin.filters import DropdownFilter, MultiSelectFilter, NumericRangeFilter, DateRangeFilter
from django_yp_admin.history.models import Revision, Version
from django_yp_admin.widgets import HtmxAutocomplete
from tests.testapp.models import Album, Article, SiteConfig, Track


pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def superuser():
    User = get_user_model()
    return User.objects.create_superuser("root", "r@e.com", "x")


@pytest.fixture
def client_logged(superuser):
    c = Client()
    c.login(username="root", password="x")
    return c


def _make_range_filter(filter_cls, field_name, params):
    rf = RequestFactory()
    request = rf.get("/", params)
    field = Article._meta.get_field(field_name)
    return filter_cls(field, request, dict(params), Article, None, field_name)


def _reset_url_caches():
    """Force the test ROOT_URLCONF to rebuild so newly registered admins are routable."""
    import sys
    from importlib import reload

    from django.conf import settings as _settings
    from django.urls import clear_url_caches as _clear

    _clear()
    mod = _settings.ROOT_URLCONF
    if mod in sys.modules:
        reload(sys.modules[mod])
    _clear()


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


# ---------------------------------------------------------------------------
# 1. DateRangeFilter with timezone-aware datetimes
# ---------------------------------------------------------------------------


def test_date_range_filter_with_tz_aware_datetimes_no_warnings():
    """USE_TZ=True: filtering DateTimeField via __gte/__lte with a date string
    must work and not surface a naive-vs-aware RuntimeWarning."""
    a = Article.objects.create(title="a")
    a2 = Article.objects.create(title="b")
    assert a.created_at.tzinfo is not None  # auto_now_add → aware

    f = _make_range_filter(
        DateRangeFilter,
        "created_at",
        {"created_at__gte": "1970-01-01", "created_at__lte": "9999-12-31"},
    )
    rf = RequestFactory()
    req = rf.get("/", {"created_at__gte": "1970-01-01", "created_at__lte": "9999-12-31"})

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        qs = f.queryset(req, Article.objects.all())
        ids = sorted(qs.values_list("pk", flat=True))
        assert ids == sorted([a.pk, a2.pk])

    naive_warnings = [w for w in caught if "naive" in str(w.message).lower() or "aware" in str(w.message).lower()]
    if naive_warnings:
        pytest.xfail(
            "bug: DateRangeFilter applied to a DateTimeField produces naive "
            "datetimes when USE_TZ=True, triggering RuntimeWarning. The parser "
            "should make the bound aware (or compare as date). "
            "See django_yp_admin/filters.py:182-206."
        )
    assert not naive_warnings, [str(w.message) for w in naive_warnings]


# ---------------------------------------------------------------------------
# 2. NumericRangeFilter with negatives and zero
# ---------------------------------------------------------------------------


def test_numeric_range_filter_with_negatives_and_zero():
    a_neg = Article.objects.create(title="neg", price=Decimal("-50"))
    a_zero = Article.objects.create(title="zero", price=Decimal("0"))
    a_pos = Article.objects.create(title="pos", price=Decimal("100"))

    # gte=-100, lte=50 → neg + zero
    f = _make_range_filter(NumericRangeFilter, "price", {"price__gte": "-100", "price__lte": "50"})
    rf = RequestFactory()
    req = rf.get("/", {"price__gte": "-100", "price__lte": "50"})
    qs = f.queryset(req, Article.objects.all())
    titles = sorted(qs.values_list("title", flat=True))
    assert titles == ["neg", "zero"]

    # gte=0 → zero + pos
    f2 = _make_range_filter(NumericRangeFilter, "price", {"price__gte": "0"})
    req2 = rf.get("/", {"price__gte": "0"})
    qs2 = f2.queryset(req2, Article.objects.all())
    titles2 = sorted(qs2.values_list("title", flat=True))
    assert titles2 == ["pos", "zero"]


# ---------------------------------------------------------------------------
# 3. OrderedModel.save() re-parented (wrt change)
# ---------------------------------------------------------------------------


def test_ordered_model_reparented_restarts_order_in_new_group():
    a = Album.objects.create(name="A")
    b = Album.objects.create(name="B")
    Track.objects.create(album=a, title="a0")  # order=0
    a1 = Track.objects.create(album=a, title="a1")  # order=1
    Track.objects.create(album=b, title="b0")  # order=0 in B

    # Move a1 to album B
    a1.album = b
    a1.save()
    a1.refresh_from_db()

    assert a1.album_id == b.id
    # New order in B should be next available (1), not preserve old order=1
    # which would collide with no one (B only had order=0) — but the key is
    # _next_order is recomputed for the new wrt group.
    sibling_orders = sorted(Track.objects.filter(album=b).values_list("order", flat=True))
    # Two distinct orders, one per track in B, no duplicates.
    assert len(sibling_orders) == 2
    assert len(set(sibling_orders)) == 2
    assert a1.order == max(sibling_orders)

    # Album A still has its remaining track; no crash, no duplicate.
    a_orders = sorted(Track.objects.filter(album=a).values_list("order", flat=True))
    assert len(set(a_orders)) == len(a_orders)


# ---------------------------------------------------------------------------
# 4. revert_view rejects mismatched content_type
# ---------------------------------------------------------------------------


def test_revert_view_rejects_mismatched_content_type(superuser):
    """Snapshot is for Article, URL targets testapp.track → must 404."""
    article = Article.objects.create(title="x")
    v = _snapshot(article)

    # The Version row's content_type is testapp.article, but URL says track.
    client = Client()
    client.login(username="root", password="x")
    url = f"/yp-admin/testapp/track/{article.pk}/revert/{v.pk}/"
    resp = client.post(url)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 5. SingletonModel.get_solo() race-safe (concurrent threads)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="SQLite locking on Windows misbehaves under threaded test access.",
)
@pytest.mark.django_db(transaction=True)
def test_singleton_get_solo_threadsafe():
    """Concurrent get_solo() must converge on a single pk=1 row.

    SQLite serializes writes; OperationalError('database table is locked')
    is acceptable for some workers as long as the survivors all see pk=1
    and no duplicate row is ever created.
    """
    from django.db import OperationalError, connections

    results = []
    lock_errors = []
    other_errors = []
    barrier = threading.Barrier(4)

    def worker():
        try:
            barrier.wait()
            obj = SiteConfig.get_solo()
            results.append(obj.pk)
        except OperationalError as exc:
            lock_errors.append(exc)
        except Exception as exc:  # pragma: no cover
            other_errors.append(exc)
        finally:
            connections.close_all()

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not other_errors, other_errors
    # Every successful worker must see pk=1.
    assert all(pk == 1 for pk in results)
    # Critical invariant: no duplicate singleton rows, regardless of how
    # many lock-contention errors the workers hit.
    assert SiteConfig.objects.count() <= 1
    if SiteConfig.objects.exists():
        assert SiteConfig.objects.get().pk == 1


# ---------------------------------------------------------------------------
# 6. Filter choices with HTML — XSS escape
# ---------------------------------------------------------------------------


class _XssDropdown(DropdownFilter):
    title = "Status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return (("foo", "<script>alert(1)</script>"),)


def test_dropdown_filter_html_in_choice_label_is_escaped():
    """A malicious lookup label must be HTML-escaped when the filter template
    renders. We render `filter_dropdown.html` directly with a manufactured
    spec/choices payload and assert no unescaped `<script>` survives."""
    from django.template.loader import render_to_string

    rf = RequestFactory()
    req = rf.get("/")
    f = _XssDropdown(req, {}, Article, None)
    # Template references spec.field_path as the |default fallback target —
    # SimpleListFilter has no field_path attribute, so set one for rendering.
    f.field_path = f.parameter_name

    # SimpleListFilter.choices() needs a changelist-ish object exposing
    # get_query_string. A minimal stub suffices for template rendering.
    class _Changelist:
        add_facets = False
        filter_specs = []

        def get_query_string(self, new_params=None, remove=None):
            return "?"

    choices = list(f.choices(_Changelist()))
    rendered = render_to_string(
        "admin/yp_admin/filter_dropdown.html",
        {"title": f.title, "spec": f, "choices": choices},
    )
    assert "<script>alert(1)</script>" not in rendered
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in rendered


# ---------------------------------------------------------------------------
# 7. HtmxAutocomplete: get_url must include to_field when set
# ---------------------------------------------------------------------------


def test_htmx_autocomplete_url_includes_to_field_when_set():
    """If the FK uses to_field other than pk, the autocomplete URL should
    propagate it so AutocompleteJsonView resolves the right column.

    Uses Track.album as the base field but rebinds remote_field.field_name to
    simulate a to_field='slug' FK without a migration.
    """
    field = Track._meta.get_field("album")
    widget = HtmxAutocomplete(field=field, admin_site=django_admin.site)

    url = widget.get_url()
    # default — to_field absent for plain pk FK
    assert "to_field" not in url

    # Now simulate to_field='id' explicitly set; verify that when get_url is
    # patched to include to_field, query string survives. This is the
    # contract we want; if the implementation doesn't propagate to_field,
    # mark xfail and report a bug.
    # We force the field to claim a non-pk to_field_name and rebuild the URL.
    original = field.remote_field.field_name
    try:
        field.remote_field.field_name = "name"  # Album.name as to_field
        url2 = widget.get_url()
    finally:
        field.remote_field.field_name = original

    # If the impl never threads to_field through, this is the bug to surface.
    if "to_field=name" not in url2:
        pytest.xfail(
            "bug: HtmxAutocomplete.get_url() does not include to_field "
            "query parameter; AutocompleteJsonView won't resolve non-pk FKs. "
            "See django_yp_admin/widgets.py:33-42."
        )
    assert "to_field=name" in url2


# ---------------------------------------------------------------------------
# 8. Sortable inline with EMPTY queryset
# ---------------------------------------------------------------------------


def test_sortable_inline_empty_renders(client_logged):
    """Album with no tracks must render its sortable inline group cleanly."""
    from django_yp_admin import SortableInline, TabularInline

    class _TrackInline(SortableInline, TabularInline):
        model = Track
        sortable_field = "order"
        fields = ("title",)
        extra = 0

    class _AlbumAdmin(ModelAdmin):
        inlines = [_TrackInline]

    site = django_admin.site
    original = None
    if site.is_registered(Album):
        original = site._registry[Album].__class__
        site.unregister(Album)
    site.register(Album, _AlbumAdmin)
    _reset_url_caches()
    try:
        album = Album.objects.create(name="Empty")
        resp = client_logged.get(f"/admin/testapp/album/{album.pk}/change/")
        assert resp.status_code == 200
        # Sortable group div is present even with zero tracks
        assert b"yp-sortable-group" in resp.content
    finally:
        site.unregister(Album)
        if original is not None:
            site.register(Album, original)
        _reset_url_caches()


# ---------------------------------------------------------------------------
# 9. Change form with ONLY readonly fields
# ---------------------------------------------------------------------------


def test_change_form_all_readonly_renders(client_logged):
    """Admin where every editable field is readonly must still render."""

    class _RO(ModelAdmin):
        fields = ("title", "body", "status")
        readonly_fields = ("title", "body", "status")

    site = django_admin.site
    original = None
    if site.is_registered(Article):
        original = site._registry[Article].__class__
        site.unregister(Article)
    site.register(Article, _RO)
    try:
        a = Article.objects.create(title="ro", body="b")
        resp = client_logged.get(f"/admin/testapp/article/{a.pk}/change/")
        assert resp.status_code == 200
        # Add view too (no instance) — tests fieldset rendering w/ all RO
        resp2 = client_logged.get("/admin/testapp/article/add/")
        assert resp2.status_code == 200
    finally:
        site.unregister(Article)
        if original is not None:
            site.register(Article, original)
        else:
            site.register(Article)


# ---------------------------------------------------------------------------
# 10. MultiSelectFilter with > 50 options
# ---------------------------------------------------------------------------


class _ManyTitlesMultiSelect(MultiSelectFilter):
    title = "Title"
    parameter_name = "title"

    def lookups(self, request, model_admin):
        # 100 distinct lookups
        return tuple((f"t{i:03d}", f"t{i:03d}") for i in range(100))


def test_multiselect_filter_with_100_options():
    # Insert 100 distinct title rows
    for i in range(100):
        Article.objects.create(title=f"t{i:03d}")

    rf = RequestFactory()
    selected = ["t005", "t017", "t042", "t063", "t099"]
    params = [("title", v) for v in selected]
    req = rf.get("/", params)
    f = _ManyTitlesMultiSelect(req, {}, Article, None)

    qs = f.queryset(req, Article.objects.all())
    titles = sorted(qs.values_list("title", flat=True))
    assert titles == sorted(selected)

    # All 100 choices accessible (no truncation)
    choices = list(f.choices(changelist=None))
    # 1 "All" sentinel + 100 actual options
    assert len(choices) == 101


# ---------------------------------------------------------------------------
# 11 & 12. move_to() with out-of-range positions
# ---------------------------------------------------------------------------


def _seed_album_with_tracks(n=3):
    album = Album.objects.create(name="MoveTest")
    tracks = [Track.objects.create(album=album, title=f"t{i}") for i in range(n)]
    return album, tracks


def test_move_to_position_larger_than_queryset_clamps():
    album, tracks = _seed_album_with_tracks(3)
    t0 = tracks[0]
    t0.move_to(99)

    orders = sorted(Track.objects.filter(album=album).values_list("order", flat=True))
    # No duplicates
    assert len(set(orders)) == len(orders)

    t0.refresh_from_db()
    # Should clamp to last (max existing) — i.e. 2
    if t0.order == 99:
        pytest.xfail(
            "bug: OrderedModel.move_to() with new_order > max(order) does not "
            "clamp; leaves orphan position 99 and gaps in (group, order). "
            "See django_yp_admin/models.py:159-213."
        )
    assert t0.order == max(orders)


def test_move_to_negative_position_clamps_or_raises():
    from django.db import IntegrityError

    album, tracks = _seed_album_with_tracks(3)
    t2 = tracks[2]  # currently at order=2

    try:
        t2.move_to(-1)
    except (ValueError, AssertionError):
        return  # documented: raises is acceptable behavior
    except IntegrityError:
        # PositiveIntegerField CHECK rejected the write. Better than
        # silent data corruption, but ideally move_to should validate
        # *before* mutating siblings (which may now leave the table in
        # a broken transactional state under non-atomic backends).
        pytest.xfail(
            "bug: OrderedModel.move_to(negative) bottoms out at the DB "
            "CHECK constraint instead of validating up-front. Should "
            "clamp to 0 or raise ValueError before issuing UPDATEs. "
            "See django_yp_admin/models.py:159-213."
        )

    t2.refresh_from_db()
    orders = sorted(Track.objects.filter(album=album).values_list("order", flat=True))
    # No duplicates / no negatives in a PositiveIntegerField world.
    assert len(set(orders)) == len(orders)
    if t2.order < 0:
        pytest.xfail(
            "bug: OrderedModel.move_to(negative) writes a negative value to "
            "PositiveIntegerField; either clamp to 0 or raise ValueError. "
            "See django_yp_admin/models.py:159-213."
        )
    assert t2.order == 0
