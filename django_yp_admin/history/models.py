"""In-house lightweight versioning for django-yp-admin.

Replaces the snapshot+revert use case of django-reversion.

Trade-offs accepted in v0.1:
    - No follow-FK on revert (related objects are not snapshotted/restored).
    - No M2M tracking.
    - No soft-delete recovery (deletes purge Versions via CASCADE on the
      original via GFK -- actually GFK does not cascade, but we do not
      attempt to restore deleted objects).
    - No diff/compare between Versions.

If those features are needed, install django-reversion instead.
"""

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.db import models, transaction


class Revision(models.Model):
    """Group of Versions saved together. One Revision per save() call."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    comment = models.CharField(max_length=255, blank=True)

    class Meta:
        app_label = "yp_admin"
        ordering = ("-created_at",)

    def __str__(self):
        return f"Revision #{self.pk} @ {self.created_at:%Y-%m-%d %H:%M}"


class Version(models.Model):
    """Snapshot of one model instance at one point in time. GFK to original."""

    revision = models.ForeignKey(
        Revision,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255, db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")
    serialized_data = models.JSONField()
    object_repr = models.CharField(max_length=255)

    class Meta:
        app_label = "yp_admin"
        indexes = [models.Index(fields=["content_type", "object_id"])]

    def __str__(self):
        return self.object_repr

    @transaction.atomic
    def revert(self, allowed_fields=None):
        """Restore the snapshot onto the original instance.

        Security: by default (``allowed_fields=None``), reverting restores
        ALL fields of the snapshot, including foreign keys such as
        ``owner_id`` or ``created_by``. To prevent privilege escalation by
        users who only have ``change_*`` permission, callers must pass
        ``allowed_fields`` (an iterable of field names) to scope the
        restore. When ``allowed_fields`` is ``None`` this method refuses to
        run unless explicitly invoked with ``allowed_fields=...``; the
        caller (typically the revert view) is expected to compute the safe
        set from the ModelAdmin (e.g. ``get_fields() - get_readonly_fields()``)
        or to require superuser.

        Returns the restored object.
        """
        import json

        payload = json.dumps(self.serialized_data)
        deserialized = list(serializers.deserialize("json", payload))
        if not deserialized:
            raise ValueError("Version has empty serialized_data")
        deserialized_obj = deserialized[0]
        snapshot = deserialized_obj.object

        if allowed_fields is None:
            raise PermissionError(
                "Version.revert() called without allowed_fields; refusing "
                "to mass-assign all fields. Pass allowed_fields=<set> or "
                "require superuser at the caller."
            )

        allowed = set(allowed_fields)
        # Load the current live object and only overwrite the allowed
        # fields from the snapshot. This prevents an attacker with mere
        # change_* perms from rewriting FKs like owner_id / created_by.
        ModelClass = type(snapshot)
        current = ModelClass.objects.get(pk=snapshot.pk)
        for field in ModelClass._meta.concrete_fields:
            name = field.name
            if name == ModelClass._meta.pk.name:
                continue
            if name not in allowed and field.attname not in allowed:
                continue
            setattr(current, field.attname, getattr(snapshot, field.attname))
        current.save()
        return current
