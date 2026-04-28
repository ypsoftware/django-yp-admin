"""Template tags for django-yp-admin."""

from django import template
from django.urls import NoReverseMatch, reverse

register = template.Library()


@register.simple_tag
def yp_inline_reorder_url(inline_admin_formset):
    """Return the reorder URL for a sortable inline.

    Templates cannot access ``model._meta`` directly because Django forbids
    leading-underscore attribute lookups. This tag wraps that lookup.
    Returns an empty string if the URL is not registered (e.g. when running
    under the stock contrib admin without YpAdminSite mounted).
    """
    model = inline_admin_formset.opts.model
    meta = model._meta
    try:
        return reverse(
            "admin:yp_reorder",
            args=[meta.app_label, meta.model_name],
        )
    except NoReverseMatch:
        return ""
