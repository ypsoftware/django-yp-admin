# Versionamento

Snapshot/revert leve feito em casa, ~700 LOC, sem dependência adicional.

## Modelos

`django_yp_admin.history` traz dois modelos:

- `Revision` — uma linha por `save()` (timestamp + usuário + comentário).
- `Version` — um snapshot de uma instância de modelo, ligada a uma `Revision` via FK e ao original via GenericForeignKey. Armazena `serialized_data` como JSON.

## Admin

Adicione o mixin `VersionAdmin`, ou simplesmente defina `versioning = True`:

```python
from django_yp_admin.options import ModelAdmin
from django_yp_admin.history import VersionAdmin


@admin.register(Article)
class ArticleAdmin(VersionAdmin, ModelAdmin):
    pass  # versioning = True by default on VersionAdmin
```

Cada save tira um snapshot da instância. Uma view de histórico fica exposta em `<object_id>/yp-history/`. Clique em uma `Version` e chame `version.revert()` para restaurar.

## Revert

```python
from django_yp_admin.history.models import Version

v = Version.objects.filter(object_id="42").latest("revision__created_at")
v.revert()  # writes the snapshot back to the original row
```

## Quando usar isto vs django-simple-history

| Caso de uso | Escolha |
|---|---|
| Snapshot + revert, auditoria de tabela única, sem configuração extra de app | `django_yp_admin.history` |
| Tabela de histórico completa por modelo, tracking de M2M, follow-FK no revert, integrações com DRF/filtros do admin | `django-simple-history` (instale `django-yp-admin[history]`) |

Os dois coexistem — você pode usar `simple_history` para alguns modelos e `VersionAdmin` para outros.
