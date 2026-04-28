# Singleton models

Replaces `django-solo`. ~120 LOC, no extra dep.

## Model

`django_yp_admin.models.SingletonModel` is an abstract base that pins `pk=1` on save and turns `delete()` into a no-op.

```python
from django.db import models
from django_yp_admin.models import SingletonModel


class SiteConfig(SingletonModel):
    site_name = models.CharField(max_length=100, default="My Site")
    primary_color = models.CharField(max_length=7, default="#000000")

    def __str__(self):
        return self.site_name
```

## Access

```python
config = SiteConfig.get_solo()
config.site_name = "New Name"
config.save()  # still pk=1
```

`get_solo()` is `get_or_create(pk=1)`-equivalent and idempotent.

## Admin

Use the singleton-aware admin to redirect "add" and "changelist" URLs to the single instance:

```python
from django_yp_admin.contrib.solo_admin import SingletonModelAdmin


@admin.register(SiteConfig)
class SiteConfigAdmin(SingletonModelAdmin):
    pass
```

## Migrating from django-solo

`SingletonModel` has the same `pk=1` semantics. Drop the `django-solo` dep, change the import path, run no migrations (the data is identical).
