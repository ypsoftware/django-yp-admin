"""Reorder endpoint for OrderedModel-backed admins."""

from __future__ import annotations

import json

from django.apps import apps
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotAllowed,
)
from django.views.decorators.http import require_POST

from django_yp_admin.models import OrderedModel


@require_POST
def reorder_view(request, app_label, model_name):
    """POST {pk: int, new_order: int} → 204. Atomic via OrderedModel.move_to()."""
    try:
        model = apps.get_model(app_label, model_name)
    except LookupError:
        # Use 404 rather than 400 to avoid leaking which app/model names
        # exist on the site (info disclosure).
        raise Http404("Unknown model")

    if model is None or not issubclass(model, OrderedModel):
        return HttpResponseBadRequest("Model is not an OrderedModel")

    perm = f"{model._meta.app_label}.change_{model._meta.model_name}"
    if not request.user.is_authenticated or not request.user.has_perm(perm):
        return HttpResponseForbidden("Permission denied")

    # Parse body: JSON or form-encoded.
    pk = None
    new_order = None
    content_type = (request.content_type or "").lower()
    if "application/json" in content_type:
        try:
            payload = json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")
        pk = payload.get("pk")
        new_order = payload.get("new_order")
    else:
        pk = request.POST.get("pk")
        new_order = request.POST.get("new_order")

    if pk is None or new_order is None:
        return HttpResponseBadRequest("Missing pk or new_order")

    try:
        new_order_int = int(new_order)
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Invalid new_order")

    try:
        obj = model._default_manager.get(pk=pk)
    except model.DoesNotExist:
        raise Http404("Object not found")
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Invalid pk")

    obj.move_to(new_order_int)
    return HttpResponse(status=204)
