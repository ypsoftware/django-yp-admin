# Filtros

`django_yp_admin.filters` traz substitutos drop-in para os padrões populares de `django-filter` e `django-admin-rangefilter`. Todos os filtros são simples subclasses de `SimpleListFilter` / `FieldListFilter` do Django — funcionam em qualquer `ModelAdmin.list_filter`.

![Barra lateral de filtros](../screenshots/changelist-blog.png)

## DropdownFilter

Um `<select>` em vez de uma lista vertical de links:

```python
from django_yp_admin.filters import DropdownFilter, ChoicesDropdownFilter


class StatusFilter(DropdownFilter):
    title = "status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return Article.STATUS_CHOICES


class ArticleAdmin(ModelAdmin):
    list_filter = (StatusFilter, ("category", ChoicesDropdownFilter))
```

Variantes: `RelatedDropdownFilter` (FK/M2M), `FieldDropdownFilter` (`AllValues`), `ChoicesDropdownFilter` (`choices=`).

## MultiSelectFilter

Seleção de múltiplos valores via `__in`. URL: `?tags=a&tags=b`.

```python
from django_yp_admin.filters import MultiSelectFilter


class TagFilter(MultiSelectFilter):
    title = "tags"
    parameter_name = "tags"

    def lookups(self, request, model_admin):
        return [(t.slug, t.name) for t in Tag.objects.all()]
```

## DateRangeFilter / DateTimeRangeFilter / NumericRangeFilter

Limites pareados `__gte` / `__lte`, com `<input type="date">`, `<input type="datetime-local">`, `<input type="number">` nativos. Entrada inválida é silenciosamente ignorada (queryset retornado sem filtro para aquele limite).

```python
from django_yp_admin.filters import DateRangeFilter, NumericRangeFilter


class ArticleAdmin(ModelAdmin):
    list_filter = (
        ("created_at", DateRangeFilter),
        ("price", NumericRangeFilter),
    )
```

URL: `?created_at__gte=2024-01-01&created_at__lte=2024-12-31`.
