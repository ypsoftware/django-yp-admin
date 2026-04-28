from django.contrib import admin
from django.urls import path

from django_yp_admin.sites import site as yp_site
from tests.testapp.models import Article

# Register Article on both Django admin (for change-form redirect target)
# and on the YpAdminSite (which exposes the yp_revert URL).
if not admin.site.is_registered(Article):
    admin.site.register(Article)
if not yp_site.is_registered(Article):
    yp_site.register(Article)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("yp-admin/", yp_site.urls),
]
