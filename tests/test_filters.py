"""Tests for custom filters: range filters with valid/invalid bounds."""
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory

from django_yp_admin.filters import (
    DateRangeFilter,
    DateTimeRangeFilter,
    DropdownFilter,
    MultiSelectFilter,
    NumericRangeFilter,
)
from tests.testapp.models import Article


pytestmark = pytest.mark.django_db


def _make_filter(filter_cls, field_name, params):
    rf = RequestFactory()
    request = rf.get("/", params)
    field = Article._meta.get_field(field_name)
    return filter_cls(field, request, dict(params), Article, None, field_name)


def test_numeric_range_both_bounds():
    Article.objects.create(title="a", price=Decimal("10"))
    Article.objects.create(title="b", price=Decimal("50"))
    Article.objects.create(title="c", price=Decimal("100"))
    f = _make_filter(NumericRangeFilter, "price",
                     {"price__gte": "20", "price__lte": "80"})
    rf = RequestFactory()
    req = rf.get("/", {"price__gte": "20", "price__lte": "80"})
    qs = f.queryset(req, Article.objects.all())
    titles = sorted(qs.values_list("title", flat=True))
    assert titles == ["b"]


def test_numeric_range_missing_lower_bound():
    Article.objects.create(title="a", price=Decimal("10"))
    Article.objects.create(title="b", price=Decimal("100"))
    f = _make_filter(NumericRangeFilter, "price", {"price__lte": "50"})
    rf = RequestFactory()
    req = rf.get("/", {"price__lte": "50"})
    qs = f.queryset(req, Article.objects.all())
    assert sorted(qs.values_list("title", flat=True)) == ["a"]


def test_numeric_range_invalid_value_ignored():
    Article.objects.create(title="a", price=Decimal("10"))
    Article.objects.create(title="b", price=Decimal("100"))
    f = _make_filter(NumericRangeFilter, "price",
                     {"price__gte": "notanumber"})
    rf = RequestFactory()
    req = rf.get("/", {"price__gte": "notanumber"})
    qs = f.queryset(req, Article.objects.all())
    assert qs.count() == 2  # invalid -> no filter applied


def test_date_range_filter_clean():
    f = _make_filter(DateRangeFilter, "created_at",
                     {"created_at__gte": "2024-01-01"})
    assert f._clean("2024-01-01") == date(2024, 1, 1)
    assert f._clean("garbage") is None
    assert f._clean("") is None


def test_datetime_range_filter_clean():
    f = _make_filter(DateTimeRangeFilter, "created_at",
                     {"created_at__gte": "2024-01-01T10:00"})
    assert f._clean("2024-01-01T10:00") == datetime(2024, 1, 1, 10, 0)
    assert f._clean("nope") is None


def test_numeric_range_no_params_returns_all():
    Article.objects.create(title="a", price=Decimal("10"))
    f = _make_filter(NumericRangeFilter, "price", {})
    rf = RequestFactory()
    req = rf.get("/")
    qs = f.queryset(req, Article.objects.all())
    assert qs.count() == 1


class _StatusMultiSelect(MultiSelectFilter):
    title = "Status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return (("draft", "Draft"), ("published", "Published"))


def test_multiselect_value_before_queryset_returns_empty():
    rf = RequestFactory()
    req = rf.get("/")
    f = _StatusMultiSelect(req, {}, Article, None)
    # value() must not raise AttributeError when called before queryset().
    assert f.value() == []


class _NoParamDropdown(DropdownFilter):
    title = "Status"
    # parameter_name intentionally left as default ("")

    def lookups(self, request, model_admin):
        return (("a", "A"),)


def test_dropdown_filter_missing_parameter_name_raises():
    rf = RequestFactory()
    req = rf.get("/")
    with pytest.raises(ImproperlyConfigured):
        _NoParamDropdown(req, {}, Article, None)


class _EmptyDropdown(DropdownFilter):
    title = "Status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return ()


def test_dropdown_filter_no_lookups_no_output():
    rf = RequestFactory()
    req = rf.get("/")
    f = _EmptyDropdown(req, {}, Article, None)
    assert f.has_output() is False
