"""Popup-shim smoke tests.

The popup shim is pure TS frontend (frontend/src/popup-shim.ts) with no
server-side counterpart. It rewrites the legacy admin related-object popup
protocol (window.opener.dismissAddRelatedObjectPopup et al.) into custom
DOM events so htmx-driven inline popups can hook them.

We can't run JSDOM here; instead we verify:
- the TS source ships in the repo
- the source declares the three legacy globals
- the bundled JS contains the marker symbols (so the shim is actually
  included in the published yp-admin.js bundle).
"""
from __future__ import annotations

from pathlib import Path

import django_yp_admin

REPO_ROOT = Path(django_yp_admin.__file__).resolve().parent.parent
SHIM = REPO_ROOT / "frontend" / "src" / "popup-shim.ts"
BUNDLE = (
    Path(django_yp_admin.__file__).resolve().parent
    / "static" / "yp_admin" / "js" / "yp-admin.js"
)

LEGACY_GLOBALS = (
    "dismissAddRelatedObjectPopup",
    "dismissChangeRelatedObjectPopup",
    "dismissDeleteRelatedObjectPopup",
)

EVENT_NAMES = (
    "yp:related-object-added",
    "yp:related-object-changed",
    "yp:related-object-deleted",
)


def test_popup_shim_source_present():
    assert SHIM.is_file(), f"missing TS source: {SHIM}"
    assert SHIM.stat().st_size > 0


def test_popup_shim_declares_legacy_globals():
    src = SHIM.read_text(encoding="utf-8")
    for name in LEGACY_GLOBALS:
        assert name in src, f"{name} missing from popup-shim.ts"


def test_popup_shim_emits_yp_events():
    src = SHIM.read_text(encoding="utf-8")
    for evt in EVENT_NAMES:
        assert evt in src, f"{evt} not dispatched by popup-shim.ts"


def test_popup_shim_no_obvious_unsafe_patterns():
    src = SHIM.read_text(encoding="utf-8")
    # No eval / innerHTML smuggling in a security-sensitive shim.
    assert "eval(" not in src
    assert "innerHTML" not in src
    assert "document.write" not in src


def test_popup_shim_bundled_into_yp_admin_js():
    """The compiled bundle must actually include the shim. Otherwise legacy
    related-object popups will silently break."""
    assert BUNDLE.is_file(), f"missing bundle: {BUNDLE}"
    blob = BUNDLE.read_text(encoding="utf-8", errors="replace")
    for name in LEGACY_GLOBALS:
        assert name in blob, f"bundle missing legacy global: {name}"
    # At least one of the custom-event names should survive minification
    # (string literals are preserved).
    assert any(evt in blob for evt in EVENT_NAMES), \
        "bundle does not appear to dispatch yp:related-object-* events"
