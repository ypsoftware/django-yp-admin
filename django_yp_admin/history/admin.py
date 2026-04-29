"""Admin mixin that auto-snapshots saves and exposes a per-object history view."""

import json

from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import render
from django.urls import path


class VersionAdmin:
    """Mixin for ModelAdmin.

    Set ``versioning = True`` (default) to auto-snapshot on save and expose
    a per-object history view at ``<object_id>/yp-history/``.
    """

    versioning = True
    change_form_template = "admin/yp_admin/change_form_versioning.html"

    # ---- save hook -------------------------------------------------------

    def save_model(self, request, obj, form, change):
        if not getattr(self, "versioning", True):
            super().save_model(request, obj, form, change)
            return
        from django_yp_admin.history.models import Revision, Version

        # Wrap the model save and the snapshot creation in a single atomic
        # block: if the snapshot fails, the model save is rolled back so we
        # never have an un-snapshotted change in the database.
        with transaction.atomic():
            super().save_model(request, obj, form, change)
            revision = Revision.objects.create(
                user=request.user if request.user.is_authenticated else None,
                comment="Changed" if change else "Added",
            )
            serialized = serializers.serialize("json", [obj])
            Version.objects.create(
                revision=revision,
                content_type=ContentType.objects.get_for_model(obj.__class__),
                object_id=str(obj.pk),
                serialized_data=json.loads(serialized),
                object_repr=str(obj)[:255],
            )

    # ---- urls ------------------------------------------------------------

    def get_urls(self):
        urls = super().get_urls()
        opts = self.model._meta
        info = (opts.app_label, opts.model_name)
        custom = [
            path(
                "<str:object_id>/yp-history/",
                self.admin_site.admin_view(self.history_view),
                name="%s_%s_yp_history" % info,
            ),
        ]
        return custom + urls

    # ---- view ------------------------------------------------------------

    def history_view(self, request, object_id, extra_context=None):
        from django_yp_admin.history.models import Version

        opts = self.model._meta
        obj = self.get_object(request, object_id)
        # Permission gate: callers must have view perm on this specific
        # object. Without this an attacker could enumerate the snapshot
        # history (including serialized field values) of any object.
        if not self.has_view_permission(request, obj):
            raise PermissionDenied
        ct = ContentType.objects.get_for_model(self.model)
        versions = (
            Version.objects.filter(content_type=ct, object_id=object_id)
            .select_related("revision", "revision__user")
            .order_by("-revision__created_at")
        )
        revert_url_name = "%s:yp_revert" % self.admin_site.name
        context = {
            **self.admin_site.each_context(request),
            "opts": opts,
            "app_label": opts.app_label,
            "module_name": opts.model_name,
            "object_id": object_id,
            "original": obj,
            "versions": versions,
            "title": "History: %s" % (obj or object_id),
            "revert_url_name": revert_url_name,
            **(extra_context or {}),
        }
        return render(request, "admin/yp_admin/history.html", context)
