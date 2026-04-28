# Referência de ModelAdmin

`django_yp_admin.options.ModelAdmin` estende `django.contrib.admin.ModelAdmin`. Todas as opções upstream continuam disponíveis. Os campos abaixo foram adicionados por nós.

## Flags de ModelAdmin

| Campo | Tipo | Padrão | Descrição |
|---|---|---|---|
| `htmx_changelist` | `bool` | `False` | Ativa swaps de htmx para filtros de lista, busca e paginação. A changelist é re-renderizada no lugar. |
| `htmx_inline_save` | `bool` | `False` | Salva formulários inline via swap estilo PATCH do htmx; sem recarregamento completo da página. |
| `versioning` | `bool` | `False` | Quando True, o `save_model` do admin tira um snapshot da instância para a tabela `Version`. Veja [Versionamento](versioning.md). |

## Opções de inline

`StackedInline` e `TabularInline` de `django_yp_admin.options` adicionam:

| Campo | Tipo | Padrão | Descrição |
|---|---|---|---|
| `htmx_lazy` | `bool` | `False` | As linhas inline são buscadas sob demanda via htmx na primeira vez que a seção é expandida. |
| `sortable_field` | `str \| None` | `None` | Nome de um campo inteiro que controla a ordem das linhas. Quando definido, as linhas são renderizadas com HTML5 Drag & Drop e chamam o endpoint de reordenação via htmx. |

## Exemplo

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

`ModelAdmin.media` adiciona automaticamente `yp_admin/js/yp-admin.js` e `yp_admin/css/yp-admin.css`. Você não precisa declará-los manualmente.
