"""Admin integration for OrderedModel — drag-handle column + htmx reorder."""

from __future__ import annotations

from django.urls import NoReverseMatch, reverse
from django.utils.html import format_html

from django_yp_admin.options import ModelAdmin


class OrderedAdmin(ModelAdmin):
    """Adds drag handle column + reorder via htmx. Set sortable_field='order'."""

    sortable_field: str = "order"
    drag_handle_column: str = "_yp_drag_handle"

    def get_list_display(self, request):
        list_display = list(super().get_list_display(request))
        if self.drag_handle_column not in list_display:
            list_display.insert(0, self.drag_handle_column)
        return tuple(list_display)

    def _yp_reorder_url(self, obj) -> str:
        """Resolve the yp_reorder URL for this model. Empty string if not registered."""
        meta = obj._meta
        site_name = getattr(self.admin_site, "name", "admin")
        try:
            return reverse(
                f"{site_name}:yp_reorder",
                args=(meta.app_label, meta.model_name),
            )
        except NoReverseMatch:
            return ""

    def _yp_drag_handle(self, obj):
        url = self._yp_reorder_url(obj)
        url_attr = format_html(' data-yp-reorder-url="{}"', url) if url else ""
        return format_html(
            '<span class="yp-drag-handle" data-pk="{}"{}'
            ' role="button" aria-label="Reorder row" tabindex="0"'
            ' data-yp-drag-handle>&#x22EE;&#x22EE;</span>',
            obj.pk,
            url_attr,
        )

    _yp_drag_handle.short_description = ""  # type: ignore[attr-defined]
    _yp_drag_handle.allow_tags = True  # type: ignore[attr-defined]

    def get_ordering(self, request):
        if self.ordering:
            return self.ordering
        return (self.sortable_field,)
