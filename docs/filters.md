# Filters

`django_yp_admin.filters` ships drop-in replacements for the popular `django-filter` and `django-admin-rangefilter` patterns. All filters are plain Django `SimpleListFilter` / `FieldListFilter` subclasses — they work in any `ModelAdmin.list_filter`.

## DropdownFilter

A `<select>` instead of a vertical list of links:

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

Variants: `RelatedDropdownFilter` (FK/M2M), `FieldDropdownFilter` (`AllValues`), `ChoicesDropdownFilter` (`choices=`).

## MultiSelectFilter

Multi-value selection via `__in`. URL: `?tags=a&tags=b`.

```python
from django_yp_admin.filters import MultiSelectFilter


class TagFilter(MultiSelectFilter):
    title = "tags"
    parameter_name = "tags"

    def lookups(self, request, model_admin):
        return [(t.slug, t.name) for t in Tag.objects.all()]
```

## DateRangeFilter / DateTimeRangeFilter / NumericRangeFilter

Paired `__gte` / `__lte` bounds, native `<input type="date">`, `<input type="datetime-local">`, `<input type="number">`. Invalid input is silently ignored (queryset returned unfiltered for that bound).

```python
from django_yp_admin.filters import DateRangeFilter, NumericRangeFilter


class ArticleAdmin(ModelAdmin):
    list_filter = (
        ("created_at", DateRangeFilter),
        ("price", NumericRangeFilter),
    )
```

URL: `?created_at__gte=2024-01-01&created_at__lte=2024-12-31`.
