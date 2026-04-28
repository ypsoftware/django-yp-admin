"""Tests for SingletonModel: pk pinned to 1, get_solo, delete refused loudly."""
import pytest

from django.db.models import ProtectedError

from tests.testapp.models import SiteConfig


pytestmark = pytest.mark.django_db


def test_pk_always_one():
    cfg = SiteConfig(site_name="X")
    cfg.save()
    assert cfg.pk == 1
    cfg2 = SiteConfig(site_name="Y")
    cfg2.save()
    assert cfg2.pk == 1
    assert SiteConfig.objects.count() == 1
    assert SiteConfig.objects.get().site_name == "Y"


def test_get_solo_creates():
    assert SiteConfig.objects.count() == 0
    obj = SiteConfig.get_solo()
    assert obj.pk == 1
    assert SiteConfig.objects.count() == 1
    # Idempotent
    again = SiteConfig.get_solo()
    assert again.pk == 1
    assert SiteConfig.objects.count() == 1


def test_singleton_instance_delete_raises():
    cfg = SiteConfig.get_solo()
    with pytest.raises(ProtectedError):
        cfg.delete()
    assert SiteConfig.objects.count() == 1


def test_singleton_queryset_delete_raises():
    SiteConfig.get_solo()
    with pytest.raises(ProtectedError):
        SiteConfig.objects.all().delete()
    assert SiteConfig.objects.count() == 1
