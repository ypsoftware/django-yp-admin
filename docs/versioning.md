# Versioning

Lightweight in-house snapshot/revert, ~700 LOC, no extra dep.

## Models

`django_yp_admin.history` ships two models:

- `Revision` — one row per `save()` (timestamp + user + comment).
- `Version` — one snapshot of one model instance, attached to a `Revision` via FK and to the original via GenericForeignKey. Stores `serialized_data` as JSON.

## Admin

Add the `VersionAdmin` mixin, or just set `versioning = True`:

```python
from django_yp_admin.options import ModelAdmin
from django_yp_admin.history import VersionAdmin


@admin.register(Article)
class ArticleAdmin(VersionAdmin, ModelAdmin):
    pass  # versioning = True by default on VersionAdmin
```

Each save snapshots the instance. A history view is exposed at `<object_id>/yp-history/`. Click a `Version` and call `version.revert()` to restore.

## Revert

```python
from django_yp_admin.history.models import Version

v = Version.objects.filter(object_id="42").latest("revision__created_at")
v.revert()  # writes the snapshot back to the original row
```

## When to use this vs django-simple-history

| Use case | Pick |
|---|---|
| Snapshot + revert, single-table audit, no extra app config | `django_yp_admin.history` |
| Full per-model history table, M2M tracking, follow-FK on revert, integrations with DRF/admin filters | `django-simple-history` (install `django-yp-admin[history]`) |

The two coexist — you can use `simple_history` for some models and `VersionAdmin` for others.
