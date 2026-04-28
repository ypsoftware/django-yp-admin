# Inicio rápido

Un `ModelAdmin` mínimo con los nuevos flags de htmx:

```python
# myapp/admin.py
from django.contrib import admin
from django_yp_admin.options import ModelAdmin

from .models import Article


@admin.register(Article)
class ArticleAdmin(ModelAdmin):
    list_display = ("title", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("title",)

    # New htmx-aware flags (all default False, opt-in):
    htmx_changelist = True   # filter / search / pagination via htmx swaps
    htmx_inline_save = True  # save inline rows without full reload
    versioning = True        # auto-snapshot saves into Version table
```

Como `django_yp_admin.options.ModelAdmin` hereda de `django.contrib.admin.ModelAdmin`, todas las opciones que ya conoces (`fieldsets`, `inlines`, `readonly_fields`, `prepopulated_fields`, …) siguen funcionando sin cambios.

## Los admins existentes siguen funcionando

No necesitas migrar. Las clases existentes que heredan directamente de `django.contrib.admin.ModelAdmin` se renderizarán con nuestros templates apenas `django_yp_admin` esté en `INSTALLED_APPS` — solo el aspecto visual y los swaps de htmx vienen incluidos.

Para activar las nuevas funciones por modelo, cambia el import a `from django_yp_admin.options import ModelAdmin`.
