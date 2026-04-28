"""Custom AdminSite. Adds htmx-only URLs (reorder, version revert).

Autocomplete reuses Django's native AutocompleteJsonView. Drop-in via
INSTALLED_APPS ordering — templates and static override django.contrib.admin.
"""

from __future__ import annotations

from django.contrib.admin import AdminSite
from django.urls import path


class YpAdminSite(AdminSite):
    site_title = "Yp Admin"
    site_header = "Yp Admin"
    index_title = "Dashboard"

    def get_urls(self):
        from django_yp_admin.views.reorder import reorder_view
        from django_yp_admin.views.versioning import revert_view

        urls = super().get_urls()
        extra = [
            path(
                "<str:app_label>/<str:model_name>/reorder/",
                self.admin_view(reorder_view),
                name="yp_reorder",
            ),
            path(
                "<str:app_label>/<str:model_name>/<str:object_id>/revert/<int:version_id>/",
                self.admin_view(revert_view),
                name="yp_revert",
            ),
        ]
        return extra + urls


site = YpAdminSite(name="yp_admin")
