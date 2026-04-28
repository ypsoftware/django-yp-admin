"""URL conf for testing HtmxAutocomplete against a custom-named AdminSite.

Used by ``tests/test_widgets.py::test_htmx_autocomplete_url_resolves_for_named_admin_site``.
"""

from django.urls import path

from django_yp_admin.sites import YpAdminSite
from tests.testapp.models import Article

custom_site = YpAdminSite(name="custom")
if not custom_site.is_registered(Article):
    custom_site.register(Article)

urlpatterns = [
    path("custom-admin/", custom_site.urls),
]
