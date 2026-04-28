"""Tests for OrderedModel: order assignment, atomic move_to, wrt grouping."""
import threading

import pytest
from django.db import IntegrityError, connections, transaction

from django_yp_admin.contrib.ordered_admin import OrderedAdmin
from tests.testapp.models import Album, Track


pytestmark = pytest.mark.django_db


def _make_admin(cls=OrderedAdmin):
    from django.contrib.admin.sites import AdminSite
    return cls(Track, AdminSite())


def test_ordered_admin_respects_subclass_ordering():
    class MyAdmin(OrderedAdmin):
        ordering = ("title",)

    admin = _make_admin(MyAdmin)
    assert admin.get_ordering(request=None) == ("title",)


def test_ordered_admin_default_ordering_when_not_set():
    admin = _make_admin()
    assert admin.get_ordering(request=None) == ("order",)


def test_drag_handle_method_renamed():
    admin = _make_admin()
    assert hasattr(admin, "_yp_drag_handle")
    assert getattr(admin, "_yp_drag_handle", None) is not None
    assert not hasattr(admin, "__drag__")
    assert OrderedAdmin.drag_handle_column == "_yp_drag_handle"


def test_drag_handle_markup_has_aria_and_keyboard_attrs():
    """Drag handle must be keyboard-accessible per WCAG (FIX-19)."""
    album = Album.objects.create(name="A")
    track = Track.objects.create(title="t0", album=album)
    admin = _make_admin()
    markup = admin._yp_drag_handle(track)
    assert 'role="button"' in markup
    assert 'tabindex="0"' in markup
    assert 'aria-label="Reorder row"' in markup
    assert "data-yp-drag-handle" in markup


def test_save_assigns_next_order():
    album = Album.objects.create(name="A")
    t1 = Track.objects.create(title="t1", album=album)
    t2 = Track.objects.create(title="t2", album=album)
    assert t1.order == 0
    assert t2.order == 1


def test_move_to_atomic():
    album = Album.objects.create(name="A")
    tracks = [Track.objects.create(title=f"t{i}", album=album) for i in range(5)]
    last = tracks[-1]
    assert last.order == 4
    last.move_to(2)
    # Refresh all
    fresh = list(Track.objects.filter(album=album).order_by("order"))
    titles = [t.title for t in fresh]
    # original positions: t0=0, t1=1, t2=2, t3=3, t4=4
    # moving t4 -> 2: t2 and t3 shift up by 1
    # new order: t0=0, t1=1, t4=2, t2=3, t3=4
    assert titles == ["t0", "t1", "t4", "t2", "t3"]


def test_order_with_respect_to():
    a = Album.objects.create(name="A")
    b = Album.objects.create(name="B")
    a1 = Track.objects.create(title="a1", album=a)
    a2 = Track.objects.create(title="a2", album=a)
    b1 = Track.objects.create(title="b1", album=b)
    b2 = Track.objects.create(title="b2", album=b)
    assert (a1.order, a2.order) == (0, 1)
    assert (b1.order, b2.order) == (0, 1)


def test_unique_constraint_blocks_duplicate_order(transactional_db):
    """The (album, order) UniqueConstraint must reject duplicates at DB level."""
    album = Album.objects.create(name="A")
    Track.objects.create(title="t0", album=album)
    with pytest.raises(IntegrityError):
        # Bypass the auto-assign in save() by forcing a duplicate order.
        with transaction.atomic():
            Track.objects.create(title="dup", album=album, order=0)


def test_concurrent_move_to_no_duplicate_orders(transactional_db):
    """Two threads calling move_to concurrently must not produce duplicate
    (album, order) rows. The DB-level UniqueConstraint is the safety net.
    """
    album = Album.objects.create(name="A")
    tracks = [Track.objects.create(title=f"t{i}", album=album) for i in range(5)]
    barrier = threading.Barrier(2)
    errors = []

    def worker(track_pk, target):
        try:
            barrier.wait(timeout=5)
            t = Track.objects.get(pk=track_pk)
            t.move_to(target)
        except Exception as exc:  # IntegrityError on the loser is acceptable
            errors.append(exc)
        finally:
            connections.close_all()

    t1 = threading.Thread(target=worker, args=(tracks[0].pk, 4))
    t2 = threading.Thread(target=worker, args=(tracks[4].pk, 0))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Whatever happened, the invariant must hold: no duplicate (album, order).
    rows = list(Track.objects.filter(album=album).values_list("order", flat=True))
    assert len(rows) == len(set(rows)), f"duplicate orders: {rows}"
