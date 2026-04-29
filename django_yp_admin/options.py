"""ModelAdmin extension. Stays API-compatible with django.contrib.admin.ModelAdmin.

Adds opt-in flags for htmx behavior. All default False so subclassing existing
admins keeps current behavior.
"""

from __future__ import annotations

from django.contrib.admin import ModelAdmin as DjangoModelAdmin
from django.contrib.admin import StackedInline as DjangoStackedInline
from django.contrib.admin import TabularInline as DjangoTabularInline
from django_yp_admin.widgets import HtmxAutocomplete, HtmxAutocompleteMultiple


class ModelAdmin(DjangoModelAdmin):
    htmx_changelist: bool = False
    htmx_inline_save: bool = False
    versioning: bool = False

    # Per-ModelAdmin template overrides live under templates/admin/yp_admin/ so
    # they can {% extends "admin/change_list.html" %} (Django's) without
    # self-recursion regardless of INSTALLED_APPS order.
    change_list_template = "admin/yp_admin/change_list.html"
    change_form_template = "admin/yp_admin/change_form.html"

    @property
    def media(self):
        base = super().media
        from django.forms import Media
        extra = Media(
            js=("yp_admin/js/yp-admin.js",),
            css={"all": ("yp_admin/css/yp-admin.css",)},
        )
        return base + extra

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Swap Django's AutocompleteSelect for HtmxAutocomplete.

        Mirrors the upstream method but injects our widget; other branches
        (raw_id_fields, radio_fields) still go through ``super()``.
        """
        if "widget" not in kwargs and db_field.name in self.get_autocomplete_fields(request):
            kwargs["widget"] = HtmxAutocomplete(
                db_field, self.admin_site, using=kwargs.get("using")
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Swap AutocompleteSelectMultiple for HtmxAutocompleteMultiple."""
        if "widget" not in kwargs and db_field.name in self.get_autocomplete_fields(request):
            kwargs["widget"] = HtmxAutocompleteMultiple(
                db_field, self.admin_site, using=kwargs.get("using")
            )
        formfield = super().formfield_for_manytomany(db_field, request, **kwargs)
        # Django's super() appends a "Hold down Control..." help text when the
        # widget isn't in its built-in allowlist. Strip it for our widget.
        if formfield is not None and isinstance(formfield.widget, HtmxAutocompleteMultiple):
            from django.utils.translation import gettext_lazy as _
            msg = str(_("Hold down “Control”, or “Command” on a Mac, to select more than one."))
            help_text = str(formfield.help_text or "")
            if help_text.endswith(msg):
                formfield.help_text = help_text[: -len(msg)].rstrip()
        return formfield


class _InlineMixin:
    htmx_lazy: bool = False
    sortable_field: str | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.sortable_field and not hasattr(self, "template"):
            self.template = "admin/yp_admin/edit_inline/tabular_sortable.html"


class StackedInline(_InlineMixin, DjangoStackedInline):
    pass


class TabularInline(_InlineMixin, DjangoTabularInline):
    pass


__all__ = ["ModelAdmin", "StackedInline", "TabularInline"]
