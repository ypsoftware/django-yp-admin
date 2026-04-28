"""Revert view for django-yp-admin versioning."""

from django.apps import apps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST


@require_POST
@login_required
def revert_view(request, app_label, model_name, object_id, version_id):
    """POST -> calls Version.revert(), redirects to change form."""
    from django_yp_admin.history.models import Version

    if len(object_id) > 255:
        raise Http404("object_id too long")

    try:
        model = apps.get_model(app_label, model_name)
    except LookupError as exc:
        raise Http404("Unknown model") from exc

    perm = "%s.change_%s" % (app_label, model_name)
    if not request.user.has_perm(perm):
        raise PermissionDenied

    version = get_object_or_404(
        Version,
        pk=version_id,
        content_type__app_label=app_label,
        content_type__model=model_name,
        object_id=str(object_id),
    )
    # Compute allowed_fields from the registered ModelAdmin so that revert
    # only restores fields the user can actually edit through the change
    # form. Without this, a non-superuser with change_* perm could rewrite
    # FKs (owner_id, created_by, ...) by reverting an old snapshot.
    from django.contrib import admin as django_admin

    model_admin = django_admin.site._registry.get(model)
    if model_admin is None:
        # Fall back to YpAdminSite singleton if user mounted only that.
        try:
            from django_yp_admin.sites import site as yp_site

            model_admin = yp_site._registry.get(model)
        except Exception:
            model_admin = None
    allowed_fields = None
    if model_admin is not None:
        try:
            fields = set(model_admin.get_fields(request) or [])
            readonly = set(model_admin.get_readonly_fields(request) or [])
            allowed_fields = fields - readonly
        except Exception:
            allowed_fields = None

    if allowed_fields is None and not request.user.is_superuser:
        raise PermissionDenied("Cannot determine safe field set for revert; superuser required.")

    restored = version.revert(allowed_fields=allowed_fields)
    messages.success(
        request,
        "Reverted %s to version saved on %s." % (version.object_repr, version.revision.created_at),
    )
    change_url = reverse(
        "admin:%s_%s_change" % (app_label, model_name),
        args=[restored.pk],
    )
    return redirect(change_url)
