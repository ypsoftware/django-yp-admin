# Referencia de ModelAdmin

`django_yp_admin.options.ModelAdmin` extiende `django.contrib.admin.ModelAdmin`. Todas las opciones upstream siguen disponibles. Los campos de abajo son agregados por nosotros.

## Flags de ModelAdmin

| Campo | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `htmx_changelist` | `bool` | `False` | Activa swaps de htmx para filtros de lista, búsqueda y paginación. La changelist se vuelve a renderizar en el lugar. |
| `htmx_inline_save` | `bool` | `False` | Guarda formularios inline mediante swap estilo PATCH de htmx; sin recarga completa de página. |
| `versioning` | `bool` | `False` | Cuando es True, el `save_model` del admin toma un snapshot de la instancia en la tabla `Version`. Consulta [Versionado](versioning.md). |

## Opciones de inline

`StackedInline` y `TabularInline` de `django_yp_admin.options` agregan:

| Campo | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `htmx_lazy` | `bool` | `False` | Las filas inline se cargan bajo demanda vía htmx la primera vez que se expande la sección. |
| `sortable_field` | `str \| None` | `None` | Nombre de un campo entero que controla el orden de filas. Cuando se establece, las filas se renderizan con HTML5 Drag & Drop y llaman al endpoint de reordenamiento vía htmx. |

## Ejemplo

```python
from django_yp_admin.options import ModelAdmin, TabularInline


class TrackInline(TabularInline):
    model = Track
    htmx_lazy = True
    sortable_field = "order"


@admin.register(Album)
class AlbumAdmin(ModelAdmin):
    htmx_changelist = True
    versioning = True
    inlines = [TrackInline]
```

## Media

`ModelAdmin.media` agrega automáticamente `yp_admin/js/yp-admin.js` y `yp_admin/css/yp-admin.css`. No necesitas declararlos manualmente.
