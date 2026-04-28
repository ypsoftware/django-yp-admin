# Extras opcionales

Los paquetes pesados que afectan a toda la app se mantienen como opt-in. La integración del admin se activa automáticamente cuando la dependencia está instalada.

## Extras disponibles

```bash
pip install django-yp-admin[history]        # django-simple-history (>=3.5)
pip install django-yp-admin[import-export]  # django-import-export (>=4.0)
pip install django-yp-admin[full]           # both
```

## Semántica de activación

Cada módulo de integración consulta la dependencia opcional con `importlib.util.find_spec`:

```python
# django_yp_admin/contrib/history_admin.py
import importlib.util

if importlib.util.find_spec("simple_history") is not None:
    from simple_history.admin import SimpleHistoryAdmin

    class HistoryAdmin(SimpleHistoryAdmin):
        ...
else:
    HistoryAdmin = None
```

Si la dependencia falta, la clase wrapper es `None`. Puedes:

1. Proteger antes de heredar:
   ```python
   from django_yp_admin.contrib.history_admin import HistoryAdmin
   if HistoryAdmin is not None:
       class MyAdmin(HistoryAdmin, ModelAdmin):
           ...
   ```
2. Importar incondicionalmente y dejar que `pip install django-yp-admin[history]` sea la solución obvia cuando el import falla o la clase es `None`.

## Wrappers disponibles

| Módulo | Clase | Activado por |
|---|---|---|
| `django_yp_admin.contrib.history_admin` | `HistoryAdmin` | `pip install django-yp-admin[history]` |
| `django_yp_admin.contrib.import_export_admin` | `ImportExportAdmin` | `pip install django-yp-admin[import-export]` |

Ambos wrappers preservan la API upstream y agregan nuestros templates conscientes de htmx.

## Alpine.js: bundle opcional

Alpine es **opt-in**. El build del frontend emite dos artefactos bajo
`django_yp_admin/static/yp_admin/js/`:

| Archivo | Contenido | Tamaño minificado aprox. |
|---|---|---|
| `yp-admin.js` | htmx + Tom Select + nuestro TS. Alpine resuelto a un stub no-op. | ~124 KB (~40 KB gzip) |
| `yp-admin-alpine.js` | Lo mismo de arriba **más** Alpine.js. | ~171 KB (~55 KB gzip) |

`ModelAdmin.media` por defecto referencia `yp-admin.js`. Para activar el estado de UI local con Alpine en tu proyecto, intercambia el archivo en tu clase `Media`:

```python
class MyAdmin(admin.ModelAdmin):
    class Media:
        js = ("yp_admin/js/yp-admin-alpine.js",)
```

Está planeada una flag `Meta.use_alpine = True` en `ModelAdmin` para automatizar el cambio en una versión futura.

### Cómo funciona la división

`frontend/build.ts` corre `Bun.build` dos veces. La variante slim usa un plugin `onResolve` de Bun que redirige `import Alpine from "alpinejs"` a un pequeño stub proxy no-op, así los ~50 KB del fuente de Alpine nunca llegan al bundle slim. La variante full resuelve `alpinejs` normalmente. El define de build `__WITH_ALPINE__` también queda expuesto para futuros gates `if (__WITH_ALPINE__)` en código de usuario.

## Política de XSS en autocomplete

Las opciones de autocompletado se renderizan como **texto** por defecto. Los renderers `option`/`item` integrados de Tom Select escapan automáticamente el campo `text`, y el payload del popup de objeto relacionado (`event.detail.newRepr`) se sanitiza adicionalmente en `autocomplete.ts` antes de llegar a `addOption`.

Si personalizas Tom Select mediante una config `render` que devuelve un string HTML, **debes** escapar cada campo provisto por el usuario con el helper `escape()` exportado desde `frontend/src/autocomplete.ts`:

```ts
import { escape } from "./autocomplete";

new TomSelect(el, {
  render: {
    option: (data) => `<div class="opt">${escape(data.text)}</div>`,
    //                                    ^^^^^^^ required to prevent XSS
  },
});
```

Devolver `data.text` interpolado directamente en un template literal es un sink de XSS. Los reviewers deberían rechazar cualquier patch que lo haga.
