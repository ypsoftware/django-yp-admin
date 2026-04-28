"""Admin integration for SingletonModel."""

from __future__ import annotations

from django.http import HttpResponseRedirect
from django.urls import reverse

from django_yp_admin.options import ModelAdmin


class SingletonModelAdmin(ModelAdmin):
    """Admin for SingletonModel — no add, no delete, redirect changelist→change."""

    def has_add_permission(self, request):
        # Only allow add if no instance exists yet.
        if self.model._default_manager.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Ensure the singleton exists, then redirect to its change page.
        obj = self.model.get_solo()
        info = (self.model._meta.app_label, self.model._meta.model_name)
        url = reverse(f"admin:{info[0]}_{info[1]}_change", args=(obj.pk,))
        return HttpResponseRedirect(url)
