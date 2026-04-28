# Início rápido

Um `ModelAdmin` mínimo com as novas flags de htmx:

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

Como `django_yp_admin.options.ModelAdmin` herda de `django.contrib.admin.ModelAdmin`, todas as opções que você já conhece (`fieldsets`, `inlines`, `readonly_fields`, `prepopulated_fields`, …) continuam funcionando sem mudanças.

## Os admins existentes continuam funcionando

Você não precisa migrar. Classes existentes que herdam diretamente de `django.contrib.admin.ModelAdmin` vão renderizar com nossos templates assim que `django_yp_admin` estiver em `INSTALLED_APPS` — só a aparência e os swaps de htmx vêm junto.

Para ativar as novas funcionalidades por modelo, troque o import para `from django_yp_admin.options import ModelAdmin`.
