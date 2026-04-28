# Quickstart

A minimal `ModelAdmin` with the new htmx flags:

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

Because `django_yp_admin.options.ModelAdmin` subclasses `django.contrib.admin.ModelAdmin`, every option you already know (`fieldsets`, `inlines`, `readonly_fields`, `prepopulated_fields`, …) keeps working unchanged.

## Existing admins keep working

You don't need to migrate. Existing classes that subclass `django.contrib.admin.ModelAdmin` directly will render with our templates as soon as `django_yp_admin` is in `INSTALLED_APPS` — only the look and the htmx swaps come along.

To opt into new features per model, switch the import to `from django_yp_admin.options import ModelAdmin`.
