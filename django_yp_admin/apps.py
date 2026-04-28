from django.apps import AppConfig


class YpAdminConfig(AppConfig):
    name = "django_yp_admin"
    label = "yp_admin"
    verbose_name = "Yp Admin"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from django_yp_admin.history import models  # noqa: F401
