# Modelos singleton

Reemplaza a `django-solo`. ~120 LOC, sin dependencia adicional.

![Formulario de cambio singleton](../screenshots/singleton-config.png)

## Modelo

`django_yp_admin.models.SingletonModel` es una base abstracta que fija `pk=1` al guardar y convierte `delete()` en una operación nula.

```python
from django.db import models
from django_yp_admin.models import SingletonModel


class SiteConfig(SingletonModel):
    site_name = models.CharField(max_length=100, default="My Site")
    primary_color = models.CharField(max_length=7, default="#000000")

    def __str__(self):
        return self.site_name
```

## Acceso

```python
config = SiteConfig.get_solo()
config.site_name = "New Name"
config.save()  # still pk=1
```

`get_solo()` es equivalente a `get_or_create(pk=1)` y es idempotente.

## Admin

Usa el admin consciente de singletons para redirigir las URLs de "add" y "changelist" a la única instancia:

```python
from django_yp_admin.contrib.solo_admin import SingletonModelAdmin


@admin.register(SiteConfig)
class SiteConfigAdmin(SingletonModelAdmin):
    pass
```

## Migración desde django-solo

`SingletonModel` tiene la misma semántica de `pk=1`. Quita la dependencia `django-solo`, cambia la ruta de import, no corras migraciones (los datos son idénticos).
