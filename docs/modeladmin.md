# ModelAdmin reference

`django_yp_admin.options.ModelAdmin` extends `django.contrib.admin.ModelAdmin`. All upstream options remain available. The fields below are added by us.

## ModelAdmin flags

| Field | Type | Default | Description |
|---|---|---|---|
| `htmx_changelist` | `bool` | `False` | Enable htmx swaps for list filters, search, and pagination. The changelist re-renders in place. |
| `htmx_inline_save` | `bool` | `False` | Save inline forms via htmx PATCH-style swap; no full page reload. |
| `versioning` | `bool` | `False` | When True, the admin's `save_model` snapshots the instance into the `Version` table. See [Versioning](versioning.md). |

## Inline options

`StackedInline` and `TabularInline` from `django_yp_admin.options` add:

| Field | Type | Default | Description |
|---|---|---|---|
| `htmx_lazy` | `bool` | `False` | Inline rows are fetched on demand via htmx the first time the section is expanded. |
| `sortable_field` | `str \| None` | `None` | Name of an integer field that controls row order. When set, rows render with HTML5 Drag & Drop and call the reorder endpoint via htmx. |

## Example

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

`ModelAdmin.media` automatically appends `yp_admin/js/yp-admin.js` and `yp_admin/css/yp-admin.css`. You don't need to declare them yourself.
