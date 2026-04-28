"""htmx-powered admin widgets and inline mixins.

Replaces Django's Select2-based autocomplete with Tom Select + htmx and adds
sortable / nested inline mixins. JS wiring lives in
``yp_admin/static/yp_admin/js/yp-admin.js`` and reads ``data-yp-*`` attrs.
"""

from __future__ import annotations

from urllib.parse import urlencode

from django import forms
from django.urls import reverse


class _HtmxAutocompleteMixin:
    """Shared logic for Tom Select-backed autocomplete widgets.

    Mirrors the constructor and ``optgroups`` semantics of
    ``django.contrib.admin.widgets.AutocompleteMixin`` but emits ``data-yp-*``
    attributes the frontend bundle understands.
    """

    url_name = "%s:autocomplete"

    def __init__(self, field, admin_site, attrs=None, choices=(), using=None):
        self.field = field
        self.admin_site = admin_site
        self.db = using
        self.choices = choices
        self.attrs = {} if attrs is None else attrs.copy()

    def get_url(self):
        base = reverse(self.url_name % self.admin_site.name)
        params = {
            "app_label": self.field.model._meta.app_label,
            "model_name": self.field.model._meta.model_name,
            "field_name": self.field.name,
        }
        # Pass through ``to_field`` so AutocompleteJsonView filters on the
        # correct column when the FK declares a non-pk target field. Skip it
        # for plain pk-targeted FKs so URLs stay tidy.
        remote_field = getattr(self.field, "remote_field", None)
        to_field = getattr(remote_field, "field_name", None) if remote_field else None
        if to_field:
            try:
                related_pk_attname = remote_field.model._meta.pk.attname
            except Exception:
                related_pk_attname = None
            if to_field != related_pk_attname:
                params["to_field"] = to_field
        return f"{base}?{urlencode(params)}"

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs=extra_attrs)
        attrs["data-yp-autocomplete"] = "true"
        attrs["data-yp-autocomplete-url"] = self.get_url()
        if not self.is_required:
            attrs["data-yp-allow-clear"] = "true"
        return attrs

    def optgroups(self, name, value, attr=None):
        """Return only currently selected options. Tom Select fetches the rest."""
        default = (None, [], 0)
        groups = [default]
        has_selected = False
        selected_choices = {str(v) for v in value if str(v) not in self.choices.field.empty_values}
        if not self.is_required and not self.allow_multiple_selected:
            default[1].append(self.create_option(name, "", "", False, 0))
        remote_model_opts = self.field.remote_field.model._meta
        to_field_name = getattr(self.field.remote_field, "field_name", remote_model_opts.pk.attname)
        to_field_name = remote_model_opts.get_field(to_field_name).attname
        choices = (
            (getattr(obj, to_field_name), self.choices.field.label_from_instance(obj))
            for obj in self.choices.queryset.using(self.db).filter(**{"%s__in" % to_field_name: selected_choices})
        )
        for option_value, option_label in choices:
            selected = str(option_value) in value and (has_selected is False or self.allow_multiple_selected)
            has_selected |= selected
            index = len(default[1])
            subgroup = default[1]
            subgroup.append(self.create_option(name, option_value, option_label, selected, index))
        return groups


class HtmxAutocomplete(_HtmxAutocompleteMixin, forms.Select):
    """Replaces AutocompleteSelect (Select2). Uses Tom Select + htmx + native AutocompleteJsonView.

    Drop-in compatible: ModelAdmin.autocomplete_fields keeps working via override.
    """


class HtmxAutocompleteMultiple(_HtmxAutocompleteMixin, forms.SelectMultiple):
    """ManyToMany autocomplete using Tom Select multi mode."""


class SortableInline:
    """Inline mixin: enables HTML5 DnD reorder. Set ``sortable_field='order'``.

    Combine with ``TabularInline`` or ``StackedInline``.
    """

    sortable_field: str | None = "order"
    template = "admin/yp_admin/edit_inline/tabular_sortable.html"


class NestedInline:
    """Inline mixin: lazy htmx loading + add/remove via fragments.

    Set ``htmx_lazy=True`` (already on ``_InlineMixin``).
    """

    template = "admin/yp_admin/edit_inline/tabular_nested.html"


__all__ = [
    "HtmxAutocomplete",
    "HtmxAutocompleteMultiple",
    "SortableInline",
    "NestedInline",
]
