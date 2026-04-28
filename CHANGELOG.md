# Changelog

## 0.1.0a3 — 2026-04-28

Support matrix refresh + four edge-case bug fixes.

### Bug fixes

- **`DateRangeFilter` / `DateTimeRangeFilter` emitted naive-datetime warnings under `USE_TZ=True`.** Range bounds parsed as `date` / naive `datetime` were passed straight to a queryset on a `DateTimeField`, triggering `RuntimeWarning: ... naive datetime ... while time zone support is active` (and silently wrong-tz comparisons in some setups). Fix: `_RangeFilterBase` now coerces `date` / naive `datetime` values to aware datetimes in the active timezone before filtering.
- **`HtmxAutocomplete.get_url()` dropped `to_field` for FKs declaring a non-pk target.** With `ForeignKey(..., to_field='slug')`, the autocomplete URL omitted `to_field`, so `AutocompleteJsonView` searched the wrong column. Fix: pass `to_field` when the FK target differs from the related model's pk.
- **`OrderedModel.move_to(N)` did not clamp out-of-range positions.** Passing `N > max_order` wrote `order=N` and left a gap; passing `N < 0` raised `IntegrityError` from the `PositiveIntegerField` CHECK constraint mid-transaction. Fix: clamp `new_order` to `[0, max_existing_order]` before the sibling shift.

### Packaging / CI

- **Drop Django 5.0 and 5.1** from the test matrix and trove classifiers. Both are EOL (5.0 EOL 2025-04, 5.1 EOL 2025-12) and only inflate CI without adding coverage.
- **Add Django 5.2 LTS** (supported until 2028-04-30) and **Django 6.0** (supported until 2027-04-30) to the matrix and classifiers.
- **Drop Python 3.10** (EOL 2025-10). Bumping `requires-python` was unnecessary (already `>=3.11`).
- **Add Python 3.14** to the matrix.
- CI matrix exclusions follow Django's published Python compat: 4.2 keeps 3.11/3.12; 5.2 covers 3.11/3.12/3.13; 6.0 covers 3.12/3.13/3.14.

### Tests

- New `tests/test_edge_cases.py` (12 tests): tz-aware DateRangeFilter, NumericRangeFilter with negatives/zero, OrderedModel re-parenting, revert content_type mismatch, HTML escape in DropdownFilter, HtmxAutocomplete with custom `to_field`, sortable inline with empty queryset, change_form with all readonly fields, MultiSelectFilter with 100 options, `move_to()` clamping (>max and negative), threadsafe `SingletonModel.get_solo()`.
- Suite: 92 → **104 tests**.

## 0.1.0a2 — 2026-04-28

Bug fixes from real-world demo project run on Django 4.2 / 5.0 / 5.1.

### Critical fixes

- **Django 5.1 compat**: `admin/includes/fieldset.html` used the `length_is` filter which was removed in Django 5.1. Add/change forms raised `TemplateSyntaxError: Invalid filter: 'length_is'` on every render. Replaced with `|length == N`.
- **Sortable inline never rendered**: the template `admin/yp_admin/edit_inline/tabular_sortable.html` (a) accessed `inline_admin_formset.opts.model._meta.app_label` (Django forbids leading-underscore attribute lookups in templates → hard error on every change_form with a sortable inline), and (b) overrode `{% block inline %}` which does not exist in `admin/edit_inline/tabular.html`, so even when the underscore bug was bypassed the wrapper div with `data-yp-sortable="true"` was never emitted and drag-and-drop reorder silently did not work.
  - Replaced with a flat template that wraps `{% include "admin/edit_inline/tabular.html" %}` in a `yp-sortable-group` div carrying the data hooks.
  - Underscore-attr lookup moved to a `yp_inline_reorder_url` template tag.

### Tests

- Added `tests/test_template_render.py` (3 tests): renders the actual change_form via `Client.get()` for both a plain ModelAdmin and one with a sortable inline. These fail loudly on the bugs above. Suite: 89 → 92.

## 0.1.0a1 — pre-alpha (initial release)

First public iteration. Repositioned from "drop-in replacement" to **htmx-powered theme + helpers** for `django.contrib.admin`.

### Security

- `Version.revert()` now requires an `allowed_fields` allowlist; merges per-field instead of full deserialize+save. Closes mass-assignment vector where a user with `change_*` perm could overwrite FKs (`owner_id`, `created_by`, ...) by reverting old snapshots. Non-superusers without a registered `ModelAdmin` are refused.
- Removed duplicate `revert` URL that was mounted with only `@login_required`. Single canonical route is mounted via `YpAdminSite.admin_view` (staff-only).
- `revert_view` looks up `ModelAdmin` in both `django.contrib.admin.site` and `YpAdminSite` registries before falling back to superuser-only.
- `VersionAdmin.save_model` now wraps super-call + snapshot creation in `transaction.atomic()`. Snapshot failure rolls back the model save.
- `history_view` enforces `has_view_permission` per object.
- `revert_view` URL pattern hardened: `<str:object_id>` (not `<path:>`), with explicit 255-char cap returning 404.
- `reorder_view` returns 404 (not 400) for unknown app/model/pk to avoid info disclosure.

### Correctness

- `OrderedModel`: documented requirement for `UniqueConstraint(*order_with_respect_to, "order")` per subclass; `move_to()` rewritten as row-by-row updates inside a `transaction.atomic()` + `select_for_update()` block to avoid mid-statement constraint violations.
- `SingletonModel.delete()` now raises `ProtectedError`. Queryset-level `.delete()` also raises (custom `SingletonQuerySet`).
- `_HtmxAutocompleteMixin.optgroups` bug fix: pass per-option `selected` bool to `create_option`, not the whole `selected_choices` set.
- `OrderedAdmin.get_ordering` honors subclass `ordering` instead of overriding it.
- `MultiSelectFilter` initializes `_values` in `__init__`. `DropdownFilter` and `FieldDropdownFilter` raise `ImproperlyConfigured` on missing `parameter_name` / `title`.
- Renamed `__drag__` (dunder, risky with introspection) to `_yp_drag_handle`.

### Templates

- Per-`ModelAdmin` overrides moved from `admin/change_list.html` and `admin/change_form.html` to `admin/yp_admin/change_list.html` and `admin/yp_admin/change_form.html`. Eliminates infinite-recursion risk under either `INSTALLED_APPS` order. Defaults set on `ModelAdmin.change_list_template` / `change_form_template`.
- Global theme overrides (`base`, `base_site`, `login`, `pagination`) remain at root and rely on `INSTALLED_APPS` ordering documented in CLAUDE.md.

### Frontend

- All inline `onchange=` / `onclick=` handlers replaced with declarative `data-yp-*` attributes plus a delegated listener in `main.ts`. CSP-clean (`script-src 'self'`).
- `getCsrfToken()` throws on missing cookie instead of silently returning `""`.
- Drag handles get `role="button"`, `aria-label`, `tabindex="0"`. Keyboard reorder via Arrow keys (POST + re-focus).
- Reorder URL read from server-rendered `data-yp-reorder-url` attribute. No more regex over `window.location.pathname`.
- Tom Select XSS hardening: `escape()` helper exported, defensive sanitize on `newRepr` from related-object popups, JSDoc warning for custom `render`.
- Alpine.js split out of the default bundle. Two artifacts:
  - `yp-admin.js` — 124 KB raw / **39 KB gzip**
  - `yp-admin-alpine.js` — 171 KB raw / **55 KB gzip**

### Tests

- 19 → **89 tests** (4.7×). Added auth/perm matrix for `reorder_view`, `revert_view`, `history_view` (anon / non-staff / staff w/o perm / staff w/ perm / superuser × CSRF). Widget rendering, `formfield_for_foreignkey` and `formfield_for_manytomany` swap behavior, `INSTALLED_APPS` ordering smoke tests, popup-shim presence in compiled bundle, concurrent `move_to` race regression test.

### Packaging

- Removed deprecated `default_app_config`. Django 3.2+ auto-discovers via `apps.py`.
- GitHub Actions CI: matrix on Python 3.11/3.12/3.13 × Django 4.2/5.0/5.1 + frontend bundle drift check.
- `CONTRIBUTING.md` documents the `cd frontend && bun run build` step and the requirement to commit the bundle.

### Known limitations

- Custom `AdminSite` subclasses, django-cms, wagtail, allauth admin, debug-toolbar, jazzmin, grappelli, polymorphic, guardian, modeltranslation, nested-admin: **not yet tested**. Listed under "Roadmap / Not yet supported" in [docs/compatibility.md](docs/compatibility.md).
- Bundle size budget (CLAUDE.md previously claimed ~62 KB gzip total; reality is 39 KB slim / 55 KB with Alpine, dominated by Tom Select).
