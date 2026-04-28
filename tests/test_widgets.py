"""Tests for HtmxAutocomplete widgets.

Regression tests for FIX-8: ``_HtmxAutocompleteMixin.optgroups`` was passing
the ``selected_choices`` set (instead of the per-option ``selected`` bool) into
``create_option``, which marked options as selected even when they shouldn't
be (and broke ``selected="selected"`` rendering since the value was a set).
"""

import pytest
from django.contrib import admin

from django_yp_admin.widgets import HtmxAutocomplete, HtmxAutocompleteMultiple
from tests.testapp.models import Album, Track


pytestmark = pytest.mark.django_db


def _track_album_field():
    return Track._meta.get_field("album")


def test_htmx_autocomplete_render_no_value():
    """Widget renders with no selected value: only the empty option, no <option> for any Album."""
    Album.objects.create(name="A")
    Album.objects.create(name="B")

    widget = HtmxAutocomplete(
        field=_track_album_field(),
        admin_site=admin.site,
    )
    # Mimic ModelChoiceField bound to this widget.
    from django import forms

    widget.choices = forms.ModelChoiceField(queryset=Album.objects.all()).choices
    widget.is_required = False
    widget.allow_multiple_selected = False

    html = widget.render("album", None)

    assert 'data-yp-autocomplete="true"' in html
    # No album options rendered (Tom Select fetches them via htmx).
    assert ">A</option>" not in html
    assert ">B</option>" not in html


def test_htmx_autocomplete_render_with_selected_fk():
    """Single FK with an initial value renders exactly one <option selected>."""
    a = Album.objects.create(name="Alpha")
    Album.objects.create(name="Beta")

    widget = HtmxAutocomplete(
        field=_track_album_field(),
        admin_site=admin.site,
    )
    from django import forms

    widget.choices = forms.ModelChoiceField(queryset=Album.objects.all()).choices
    widget.is_required = True
    widget.allow_multiple_selected = False

    html = widget.render("album", a.pk)

    assert f'value="{a.pk}" selected' in html or f'value="{a.pk}"  selected' in html
    assert ">Alpha</option>" in html
    # The non-selected album is not in the markup (filtered by selected_choices).
    assert ">Beta</option>" not in html


def test_htmx_autocomplete_multiple_with_two_selected():
    """M2M-style widget with two initial values renders both as selected."""
    a = Album.objects.create(name="One")
    b = Album.objects.create(name="Two")
    Album.objects.create(name="Three")

    widget = HtmxAutocompleteMultiple(
        field=_track_album_field(),
        admin_site=admin.site,
    )
    from django import forms

    widget.choices = forms.ModelChoiceField(queryset=Album.objects.all()).choices
    widget.is_required = True
    widget.allow_multiple_selected = True

    html = widget.render("albums", [a.pk, b.pk])

    # Both selected options present and marked selected.
    assert f'value="{a.pk}"' in html
    assert f'value="{b.pk}"' in html
    assert html.count("selected") >= 2
    assert ">One</option>" in html
    assert ">Two</option>" in html
    assert ">Three</option>" not in html


def test_htmx_autocomplete_url_uses_default_admin_site():
    """FIX-14: When bound to ``django.contrib.admin.site`` (template-only
    mode), the ``data-yp-autocomplete-url`` attribute must point at the stock
    ``admin:autocomplete`` URL, not a hardcoded ``yp_admin:`` namespace."""
    from django.urls import reverse

    widget = HtmxAutocomplete(
        field=_track_album_field(),
        admin_site=admin.site,
    )
    from django import forms

    widget.choices = forms.ModelChoiceField(queryset=Album.objects.all()).choices
    widget.is_required = False
    widget.allow_multiple_selected = False

    # The site name on django.contrib.admin.site is "admin".
    assert admin.site.name == "admin"

    expected_base = reverse("admin:autocomplete")
    url = widget.get_url()
    assert url.startswith(expected_base + "?"), url

    html = widget.render("album", None)
    assert f'data-yp-autocomplete-url="{expected_base}?' in html


def _bound_widget(widget_cls, *, is_required, multiple):
    widget = widget_cls(field=_track_album_field(), admin_site=admin.site)
    from django import forms

    widget.choices = forms.ModelChoiceField(queryset=Album.objects.all()).choices
    widget.is_required = is_required
    widget.allow_multiple_selected = multiple
    return widget


def test_htmx_autocomplete_renders_data_attrs():
    """Required single FK: data-yp-autocomplete, url, no allow-clear (since required)."""
    widget = _bound_widget(HtmxAutocomplete, is_required=True, multiple=False)
    html = widget.render("album", None)

    assert 'data-yp-autocomplete="true"' in html
    assert 'data-yp-autocomplete-url="' in html
    # required => no allow-clear emitted
    assert "data-yp-allow-clear" not in html
    # single => no `multiple` attribute
    assert " multiple" not in html

    # Optional variant emits allow-clear.
    widget2 = _bound_widget(HtmxAutocomplete, is_required=False, multiple=False)
    html2 = widget2.render("album", None)
    assert 'data-yp-allow-clear="true"' in html2


def test_htmx_autocomplete_url_resolves_for_named_admin_site(settings):
    """Custom YpAdminSite(name="custom") must resolve to custom:autocomplete."""
    from django.urls import reverse

    settings.ROOT_URLCONF = "tests.urls_custom_site"

    from tests.urls_custom_site import custom_site

    widget = HtmxAutocomplete(field=_track_album_field(), admin_site=custom_site)
    expected_base = reverse("custom:autocomplete")
    url = widget.get_url()
    assert url.startswith(expected_base + "?"), url
    assert "/custom-admin/" in url


def test_htmx_autocomplete_optgroups_returns_only_selected():
    """``optgroups`` should yield options only for IDs present in `value`."""
    a = Album.objects.create(name="Sel")
    Album.objects.create(name="NotSel")

    widget = _bound_widget(HtmxAutocomplete, is_required=True, multiple=False)
    groups = widget.optgroups("album", [str(a.pk)])

    # One group (default), with exactly one rendered option for the selected pk.
    assert len(groups) == 1
    _name, options, _idx = groups[0]
    values = [opt["value"] for opt in options]
    labels = [opt["label"] for opt in options]
    assert a.pk in values or str(a.pk) in [str(v) for v in values]
    assert "Sel" in labels
    assert "NotSel" not in labels


def test_htmx_autocomplete_multiple_data_attrs():
    """Multiple variant renders ``multiple`` attribute and yp-* data attrs."""
    a = Album.objects.create(name="One")
    b = Album.objects.create(name="Two")

    widget = _bound_widget(HtmxAutocompleteMultiple, is_required=True, multiple=True)
    html = widget.render("albums", [a.pk, b.pk])

    assert 'data-yp-autocomplete="true"' in html
    assert 'data-yp-autocomplete-url="' in html
    assert "multiple" in html  # SelectMultiple emits multiple attr


def test_htmx_autocomplete_handles_no_to_field_name():
    """FK without explicit ``to_field`` should still resolve to_field via PK attname."""
    a = Album.objects.create(name="Solo")

    field = _track_album_field()
    # Sanity: Track.album declares no explicit to_field, so remote_field.field_name is None.
    assert getattr(field.remote_field, "field_name", None) in (None, "id")

    widget = _bound_widget(HtmxAutocomplete, is_required=True, multiple=False)
    # Must not raise when computing optgroups.
    groups = widget.optgroups("album", [str(a.pk)])
    labels = [opt["label"] for grp in groups for opt in grp[1]]
    assert "Solo" in labels
