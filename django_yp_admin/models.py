"""Abstract model bases shipped with django-yp-admin.

Replaces:
    - django-solo (SingletonModel)
    - django-ordered-model lite (OrderedModel)
"""

from __future__ import annotations

from typing import ClassVar

from django.db import models, transaction
from django.db.models import Max, ProtectedError, QuerySet


class SingletonQuerySet(QuerySet):
    """QuerySet for SingletonModel — refuses bulk delete."""

    def delete(self):
        raise ProtectedError(
            "Singleton instance cannot be deleted",
            protected_objects=list(self),
        )


class SingletonModel(models.Model):
    """Abstract — instance with pk=1 enforced. Replaces django-solo."""

    objects = SingletonQuerySet.as_manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Singletons cannot be deleted — fail loudly.
        raise ProtectedError(
            "Singleton instance cannot be deleted",
            protected_objects=[self],
        )

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class OrderedModel(models.Model):
    """Abstract ordered model. Atomic move_to(n). Replaces django-ordered-model lite.

    Concurrency note
    ----------------
    `move_to()` shifts siblings under `select_for_update()`, but to guarantee
    that two concurrent transactions cannot produce duplicate `(group, order)`
    rows you MUST declare a `UniqueConstraint` on your concrete subclass over
    the `order_with_respect_to` fields plus `order`.

    Example::

        from django.db.models import UniqueConstraint
        from django_yp_admin.models import OrderedModel


        class Track(OrderedModel):
            title = models.CharField(max_length=100)
            album = models.ForeignKey(Album, on_delete=models.CASCADE)
            order_with_respect_to = "album"

            class Meta(OrderedModel.Meta):
                constraints = [
                    UniqueConstraint(
                        fields=["album", "order"],
                        name="track_album_order_uniq",
                    )
                ]

    For models without `order_with_respect_to`, declare a UniqueConstraint on
    `["order"]` alone (or use `unique=True` on the field).
    """

    order = models.PositiveIntegerField(editable=False, db_index=True)

    # Optional grouping: name of FK field, or tuple of FK field names.
    # Subclasses override with a class attribute, e.g.
    #     order_with_respect_to = "category"
    #     order_with_respect_to = ("category", "tenant")
    order_with_respect_to: ClassVar[str | tuple[str, ...] | None] = None

    class Meta:
        abstract = True
        ordering = ("order",)

    # ------------------------------------------------------------------ helpers

    def _wrt_fields(self) -> tuple[str, ...]:
        wrt = self.order_with_respect_to
        if wrt is None:
            return ()
        if isinstance(wrt, str):
            return (wrt,)
        return tuple(wrt)

    def _wrt_filter_kwargs(self) -> dict:
        """Build a filter kwargs dict for sibling lookups.

        For FK fields, prefer the `_id` attname so we don't force a related
        lookup. For non-FK fields (e.g. a CharField status used as part of
        the grouping key), filter by the bare field name.
        """
        kwargs = {}
        meta = type(self)._meta
        for name in self._wrt_fields():
            # Caller may have already passed the `_id` form.
            base_name = name[:-3] if name.endswith("_id") else name
            try:
                field = meta.get_field(base_name)
            except Exception:
                field = None
            is_relation = bool(getattr(field, "is_relation", False) and getattr(field, "many_to_one", False))
            if is_relation:
                attname = f"{base_name}_id"
                kwargs[attname] = getattr(self, attname, None)
            else:
                kwargs[base_name] = getattr(self, base_name, None)
        return kwargs

    def _sibling_qs(self):
        """Return queryset filtered by `order_with_respect_to` keys."""
        qs = type(self)._default_manager.all()
        if self._wrt_fields():
            qs = qs.filter(**self._wrt_filter_kwargs())
        return qs

    def _wrt_changed(self) -> bool:
        """Return True if any wrt-field changed vs DB. False on new instances."""
        if self.pk is None:
            return False
        fields = self._wrt_fields()
        if not fields:
            return False
        meta = type(self)._meta

        def _attname(name: str) -> str:
            base = name[:-3] if name.endswith("_id") else name
            try:
                field = meta.get_field(base)
            except Exception:
                return base
            if getattr(field, "is_relation", False) and getattr(field, "many_to_one", False):
                return f"{base}_id"
            return base

        attnames = [_attname(f) for f in fields]
        try:
            db_obj = type(self)._default_manager.only(*attnames).get(pk=self.pk)
        except type(self).DoesNotExist:
            return False
        for attname in attnames:
            if getattr(self, attname, None) != getattr(db_obj, attname, None):
                return True
        return False

    def _next_order(self) -> int:
        agg = self._sibling_qs().aggregate(_m=Max("order"))
        m = agg["_m"]
        return 0 if m is None else m + 1

    # ------------------------------------------------------------------- save

    def save(self, *args, **kwargs):
        if self.order is None or self._wrt_changed():
            self.order = self._next_order()
        super().save(*args, **kwargs)

    # --------------------------------------------------------------- move_to

    def move_to(self, new_order: int) -> None:
        """Move this row to position `new_order` atomically.

        Shifts siblings between the old and new positions by ±1 using
        an F-expression update, then writes the new order on self.

        ``new_order`` is clamped to ``[0, max(order_in_group)]`` so callers
        can't open gaps in the sequence by passing an out-of-range index.
        """
        new_order = int(new_order)
        with transaction.atomic():
            # Lock siblings (and self) for the duration of the transaction.
            locked = list(self._sibling_qs().select_for_update().values_list("pk", "order"))
            current = dict(locked).get(self.pk)
            if current is None:
                # Not yet persisted in this group; fall back to plain save.
                # Clamp to non-negative to avoid IntegrityError on the
                # PositiveIntegerField CHECK constraint.
                self.order = max(0, new_order)
                self.save(update_fields=["order"])
                return
            # Clamp into [0, max_existing_order]. The current row already
            # occupies one slot, so max_existing_order is the highest valid
            # destination index.
            max_order = max((o for _, o in locked), default=0)
            if new_order < 0:
                new_order = 0
            elif new_order > max_order:
                new_order = max_order
            if new_order == current:
                return

            qs = self._sibling_qs()
            mgr = type(self)._default_manager

            # Park self at a sentinel order so the sibling shift cannot
            # collide with the UniqueConstraint on (group, order). We use
            # max(order)+pk+1, guaranteed positive and unique per row, and
            # outside the range any sibling shift will touch.
            max_order = self._sibling_qs().aggregate(_m=Max("order"))["_m"] or 0
            sentinel = max_order + len(locked) + 1
            mgr.filter(pk=self.pk).update(order=sentinel)

            if new_order > current:
                # Moving down: shift items in (current, new_order] DOWN by 1.
                # Walk in ascending order so each row's target is just-vacated.
                rows = list(
                    qs.filter(order__gt=current, order__lte=new_order).order_by("order").values_list("pk", "order")
                )
                for pk, ordv in rows:
                    mgr.filter(pk=pk).update(order=ordv - 1)
            else:
                # Moving up: shift items in [new_order, current) UP by 1.
                # Walk in descending order so each row's target is just-vacated.
                rows = list(
                    qs.filter(order__gte=new_order, order__lt=current).order_by("-order").values_list("pk", "order")
                )
                for pk, ordv in rows:
                    mgr.filter(pk=pk).update(order=ordv + 1)

            mgr.filter(pk=self.pk).update(order=new_order)
            self.order = new_order
