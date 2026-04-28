"""Custom admin list filters for django-yp-admin (dropdown, multiselect, range)."""

from django.contrib import admin
from django.contrib.admin import FieldListFilter
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _


class DropdownFilter(admin.SimpleListFilter):
    """SimpleListFilter rendered as a <select> dropdown instead of a list."""

    template = "admin/yp_admin/filter_dropdown.html"
    title = ""
    parameter_name = ""

    def __init__(self, request, params, model, model_admin):
        # parent SimpleListFilter only enforces parameter_name is not None;
        # our class default of "" would slip through. Validate explicitly.
        if not self.parameter_name:
            raise ImproperlyConfigured(
                "The list filter '%s' does not specify a 'parameter_name'." % self.__class__.__name__
            )
        super().__init__(request, params, model, model_admin)
        if not self.title:
            raise ImproperlyConfigured("The list filter '%s' does not specify a 'title'." % self.__class__.__name__)

    def lookups(self, request, model_admin):
        return ()

    def has_output(self):
        # Parent uses self.lookup_choices populated in __init__. When lookups()
        # returns empty/None, lookup_choices is [] and has_output() is False.
        return bool(self.lookup_choices)

    def queryset(self, request, queryset):
        value = self.value()
        if value in (None, ""):
            return queryset
        return queryset.filter(**{self.parameter_name: value})


class RelatedDropdownFilter(admin.RelatedFieldListFilter):
    """RelatedFieldListFilter (FK/M2M) rendered as a <select> dropdown."""

    template = "admin/yp_admin/filter_dropdown.html"


class FieldDropdownFilter(admin.AllValuesFieldListFilter):
    """AllValuesFieldListFilter (non-FK fields) rendered as a <select> dropdown."""

    template = "admin/yp_admin/filter_dropdown.html"

    def __init__(self, field, request, params, model, model_admin, field_path):
        super().__init__(field, request, params, model, model_admin, field_path)
        if not getattr(self, "parameter_name", None) and not getattr(self, "lookup_kwarg", None):
            raise ImproperlyConfigured(
                "The list filter '%s' does not specify a 'parameter_name'." % self.__class__.__name__
            )
        if not self.title:
            raise ImproperlyConfigured("The list filter '%s' does not specify a 'title'." % self.__class__.__name__)


class ChoicesDropdownFilter(admin.ChoicesFieldListFilter):
    """ChoicesFieldListFilter rendered as a <select> dropdown."""

    template = "admin/yp_admin/filter_dropdown.html"


class MultiSelectFilter(admin.SimpleListFilter):
    """SimpleListFilter that allows selecting multiple values via __in lookup."""

    template = "admin/yp_admin/filter_multiselect.html"
    title = ""
    parameter_name = ""

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)
        # value() reads self._values, set inside queryset(). Initialize here
        # so callers that hit value() before queryset() get an empty list
        # instead of AttributeError.
        self._values = []

    def lookups(self, request, model_admin):
        return ()

    def values(self, request):
        return [v for v in request.GET.getlist(self.parameter_name) if v]

    def value(self):
        # Override single-value semantics to a list for template rendering.
        return self._values

    def has_output(self):
        return True

    def queryset(self, request, queryset):
        self._values = self.values(request)
        if not self._values:
            return queryset
        return queryset.filter(**{f"{self.parameter_name}__in": self._values})

    def choices(self, changelist):
        selected = set(self.value() or [])
        yield {
            "selected": not selected,
            "value": "",
            "display": _("All"),
        }
        for lookup, title in self.lookups(None, None) or ():
            yield {
                "selected": str(lookup) in selected,
                "value": lookup,
                "display": title,
            }


class _RangeFilterBase(FieldListFilter):
    """Shared base for paired __gte/__lte range filters with input validation."""

    template = ""
    input_type = "text"
    parser = staticmethod(lambda v: v)

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.field_path = field_path
        self.lookup_kwarg_gte = f"{field_path}__gte"
        self.lookup_kwarg_lte = f"{field_path}__lte"
        super().__init__(field, request, params, model, model_admin, field_path)
        self.request_get = request.GET

    def expected_parameters(self):
        return [self.lookup_kwarg_gte, self.lookup_kwarg_lte]

    def _clean(self, raw):
        if raw in (None, ""):
            return None
        try:
            return self.parser(raw)
        except (ValueError, TypeError):
            return None

    def _coerce_for_field(self, value):
        """Coerce a parsed value so it matches the underlying field type.

        For DateTimeFields under ``USE_TZ=True``, naive datetime / date inputs
        get promoted to timezone-aware datetimes in the active timezone so the
        ORM does not emit ``RuntimeWarning: ... naive datetime ... while time
        zone support is active``.
        """
        from datetime import date, datetime

        from django.conf import settings
        from django.db import models as dj_models
        from django.utils import timezone

        if not isinstance(self.field, dj_models.DateTimeField):
            return value
        if not getattr(settings, "USE_TZ", False):
            return value
        if isinstance(value, datetime):
            if timezone.is_naive(value):
                return timezone.make_aware(value, timezone.get_current_timezone())
            return value
        if isinstance(value, date):
            dt = datetime.combine(value, datetime.min.time())
            return timezone.make_aware(dt, timezone.get_current_timezone())
        return value

    def queryset(self, request, queryset):
        filters = {}
        gte = self._clean(request.GET.get(self.lookup_kwarg_gte))
        lte = self._clean(request.GET.get(self.lookup_kwarg_lte))
        if gte is not None:
            filters[self.lookup_kwarg_gte] = self._coerce_for_field(gte)
        if lte is not None:
            filters[self.lookup_kwarg_lte] = self._coerce_for_field(lte)
        if not filters:
            return queryset
        return queryset.filter(**filters)

    def choices(self, changelist):
        preserved = changelist.get_filters_params()
        preserved.pop(self.lookup_kwarg_gte, None)
        preserved.pop(self.lookup_kwarg_lte, None)
        return [
            {
                "input_type": self.input_type,
                "field_path": self.field_path,
                "param_gte": self.lookup_kwarg_gte,
                "param_lte": self.lookup_kwarg_lte,
                "value_gte": self.request_get.get(self.lookup_kwarg_gte, ""),
                "value_lte": self.request_get.get(self.lookup_kwarg_lte, ""),
                "preserved": preserved,
            }
        ]


def _parse_date(value):
    from datetime import date

    return date.fromisoformat(value)


def _parse_datetime(value):
    from datetime import datetime

    # HTML datetime-local: "YYYY-MM-DDTHH:MM" (optionally with seconds).
    return datetime.fromisoformat(value)


def _parse_number(value):
    from decimal import Decimal, InvalidOperation

    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(str(exc))


class DateRangeFilter(_RangeFilterBase):
    """FieldListFilter for DateField with two <input type='date'> bounds."""

    template = "admin/yp_admin/filter_date_range.html"
    input_type = "date"
    parser = staticmethod(_parse_date)


class DateTimeRangeFilter(_RangeFilterBase):
    """FieldListFilter for DateTimeField with two <input type='datetime-local'> bounds."""

    template = "admin/yp_admin/filter_datetime_range.html"
    input_type = "datetime-local"
    parser = staticmethod(_parse_datetime)


class NumericRangeFilter(_RangeFilterBase):
    """FieldListFilter for numeric fields with two <input type='number'> bounds."""

    template = "admin/yp_admin/filter_numeric_range.html"
    input_type = "number"
    parser = staticmethod(_parse_number)
