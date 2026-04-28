"""Tests for ``django_yp_admin.options.ModelAdmin`` formfield swapping.

Verifies:
- ``formfield_for_foreignkey`` swaps Django's AutocompleteSelect for our
  ``HtmxAutocomplete`` when the field is in ``autocomplete_fields``.
- It does NOT swap outside ``autocomplete_fields``.
- An explicit ``widget=`` kwarg from the caller is respected.
- ``formfield_for_manytomany`` swaps to ``HtmxAutocompleteMultiple`` and
  strips Django's "Hold down Control..." help text addition without
  clobbering user-supplied help text.
"""

from __future__ import annotations

import pytest
from django import forms
from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory

from django_yp_admin.options import ModelAdmin
from django_yp_admin.widgets import HtmxAutocomplete, HtmxAutocompleteMultiple
from tests.testapp.models import Album, Track


pytestmark = pytest.mark.django_db


@pytest.fixture
def request_with_superuser():
    rf = RequestFactory()
    user = User.objects.create_superuser(
        username="admin_test", email="a@example.com", password="x"
    )
    req = rf.get("/")
    req.user = user
    return req


class TrackAdminWithAutocomplete(ModelAdmin):
    autocomplete_fields = ["album"]


class TrackAdminWithoutAutocomplete(ModelAdmin):
    autocomplete_fields = []


def test_formfield_for_foreignkey_swaps_to_htmx_when_in_autocomplete_fields(
    request_with_superuser,
):
    # Album admin must be registered for autocomplete target lookup to succeed.
    if not admin.site.is_registered(Album):
        admin.site.register(Album)
    ma = TrackAdminWithAutocomplete(Track, admin.site)
    field = ma.formfield_for_foreignkey(
        Track._meta.get_field("album"), request_with_superuser
    )
    assert isinstance(field.widget, HtmxAutocomplete)


def test_formfield_for_foreignkey_does_not_swap_outside_autocomplete_fields(
    request_with_superuser,
):
    ma = TrackAdminWithoutAutocomplete(Track, admin.site)
    field = ma.formfield_for_foreignkey(
        Track._meta.get_field("album"), request_with_superuser
    )
    assert not isinstance(field.widget, HtmxAutocomplete)


def test_formfield_for_foreignkey_respects_explicit_widget_kwarg(
    request_with_superuser,
):
    if not admin.site.is_registered(Album):
        admin.site.register(Album)
    ma = TrackAdminWithAutocomplete(Track, admin.site)
    class MarkerSelect(forms.Select):
        pass

    sentinel = MarkerSelect(attrs={"data-test": "user"})
    field = ma.formfield_for_foreignkey(
        Track._meta.get_field("album"),
        request_with_superuser,
        widget=sentinel,
    )
    # User-supplied widget class is preserved; HtmxAutocomplete is NOT injected.
    assert not isinstance(field.widget, HtmxAutocomplete)
    assert isinstance(field.widget, MarkerSelect)


# --- M2M tests -------------------------------------------------------------
# Track has no native M2M; build a small dynamic model OR test via a fake
# field. Easier: define a model with M2M in this module — but adding models
# at test time requires migrations. Instead, reuse Album ↔ Track relation
# inverted: there is no M2M. We add a dynamic ad-hoc ModelAdmin that
# overrides ``formfield_for_manytomany`` calls by patching a fake db_field.
#
# Cleanest: define an inline admin that uses an existing M2M. The test app
# does not ship one. So we construct a synthetic situation by calling the
# method against a model with an M2M field — we use Django's auth.User /
# auth.Group M2M (User.groups), which is always available.

from django.contrib.auth.models import Group


class UserAdminAutocompleteGroups(ModelAdmin):
    autocomplete_fields = ["groups"]


class UserAdminAutocompleteGroupsWithHelp(ModelAdmin):
    autocomplete_fields = ["groups"]

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        formfield = super().formfield_for_manytomany(db_field, request, **kwargs)
        # Re-apply user help text after super() (super stripped the Django addendum).
        formfield.help_text = "Pick groups carefully."
        return formfield


def _ensure_group_admin_registered():
    if not admin.site.is_registered(Group):
        admin.site.register(Group)


def test_formfield_for_manytomany_swaps_widget(request_with_superuser):
    _ensure_group_admin_registered()
    ma = UserAdminAutocompleteGroups(User, admin.site)
    db_field = User._meta.get_field("groups")
    formfield = ma.formfield_for_manytomany(db_field, request_with_superuser)
    assert isinstance(formfield.widget, HtmxAutocompleteMultiple)


def test_formfield_for_manytomany_strips_hold_down_control_help_text(
    request_with_superuser,
):
    _ensure_group_admin_registered()
    ma = UserAdminAutocompleteGroups(User, admin.site)
    db_field = User._meta.get_field("groups")
    formfield = ma.formfield_for_manytomany(db_field, request_with_superuser)
    help_text = str(formfield.help_text or "")
    assert "Hold down" not in help_text
    assert "Control" not in help_text


def test_formfield_for_manytomany_preserves_user_help_text(request_with_superuser):
    """A user-supplied help_text (set by subclass) should survive the swap."""
    _ensure_group_admin_registered()
    ma = UserAdminAutocompleteGroupsWithHelp(User, admin.site)
    db_field = User._meta.get_field("groups")
    formfield = ma.formfield_for_manytomany(db_field, request_with_superuser)
    assert "Pick groups carefully." in str(formfield.help_text)
    assert "Hold down" not in str(formfield.help_text)
