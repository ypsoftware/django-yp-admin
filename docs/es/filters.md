# Filtros

`django_yp_admin.filters` ofrece reemplazos drop-in para los patrones populares de `django-filter` y `django-admin-rangefilter`. Todos los filtros son simples subclases de `SimpleListFilter` / `FieldListFilter` de Django — funcionan en cualquier `ModelAdmin.list_filter`.

![Barra lateral de filtros](../screenshots/changelist-blog.png)

## DropdownFilter

Un `<select>` en lugar de una lista vertical de enlaces:

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

Selección de múltiples valores vía `__in`. URL: `?tags=a&tags=b`.

```python
from django_yp_admin.filters import MultiSelectFilter


class TagFilter(MultiSelectFilter):
    title = "tags"
    parameter_name = "tags"

    def lookups(self, request, model_admin):
        return [(t.slug, t.name) for t in Tag.objects.all()]
```

## DateRangeFilter / DateTimeRangeFilter / NumericRangeFilter

Límites pareados `__gte` / `__lte`, con `<input type="date">`, `<input type="datetime-local">`, `<input type="number">` nativos. La entrada inválida se ignora silenciosamente (el queryset se devuelve sin filtrar para ese límite).

```python
from django_yp_admin.filters import DateRangeFilter, NumericRangeFilter


class ArticleAdmin(ModelAdmin):
    list_filter = (
        ("created_at", DateRangeFilter),
        ("price", NumericRangeFilter),
    )
```

URL: `?created_at__gte=2024-01-01&created_at__lte=2024-12-31`.
