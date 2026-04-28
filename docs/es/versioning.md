# Versionado

Snapshot/revert ligero hecho en casa, ~700 LOC, sin dependencia adicional.

## Modelos

`django_yp_admin.history` incluye dos modelos:

- `Revision` — una fila por cada `save()` (timestamp + usuario + comentario).
- `Version` — un snapshot de una instancia de modelo, vinculada a una `Revision` por FK y al original por GenericForeignKey. Almacena `serialized_data` como JSON.

## Admin

Agrega el mixin `VersionAdmin`, o simplemente establece `versioning = True`:

```python
from django_yp_admin.options import ModelAdmin
from django_yp_admin.history import VersionAdmin


@admin.register(Article)
class ArticleAdmin(VersionAdmin, ModelAdmin):
    pass  # versioning = True by default on VersionAdmin
```

Cada save hace un snapshot de la instancia. Una vista de historial queda expuesta en `<object_id>/yp-history/`. Haz clic en una `Version` y llama a `version.revert()` para restaurar.

## Revert

```python
from django_yp_admin.history.models import Version

v = Version.objects.filter(object_id="42").latest("revision__created_at")
v.revert()  # writes the snapshot back to the original row
```

## Cuándo usar esto vs django-simple-history

| Caso de uso | Elige |
|---|---|
| Snapshot + revert, auditoría de tabla única, sin configuración de app extra | `django_yp_admin.history` |
| Tabla de historial completa por modelo, tracking de M2M, follow-FK al revert, integraciones con DRF/filtros del admin | `django-simple-history` (instala `django-yp-admin[history]`) |

Los dos coexisten — puedes usar `simple_history` para algunos modelos y `VersionAdmin` para otros.
