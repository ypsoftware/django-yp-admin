# Changelog

## 0.1.1 — 2026-04-29

Frontend correctness pass + custom-`AdminSite` support. No API changes.

### Bug fixes

- **htmx swap leaked full `<html>` into `#changelist-form`.** Filter widgets, pagination links, and the facet/clear-filter anchors all set `hx-target="#changelist-form"` but no `hx-select`. With the `hx-boost` body-level inheritance, htmx swapped the entire response (including `<html>`/`<head>`/sidebar chrome) into the changelist container, nesting a fresh page on every interaction. Fix: every htmx-driven changelist control now declares `hx-select="#changelist-form" hx-swap="outerHTML"` explicitly. Removed `hx-boost="true"` from `<body>` — full page reloads between sections (home → list) are fine; htmx is reserved for changelist filter/pagination/save-form swaps.
- **Body class + `<title>` went stale after htmx swaps.** The chrome (header, breadcrumbs, view-scoped CSS hooks like `body.dashboard`, `body.app-blog`) lives outside `#content`; swapping `#content` left the previous page's body class in place, so view-scoped selectors leaked across pages. Fix: `htmx:beforeSwap` listener mirrors `<body class>` and `<title>` from the response when the swap target is `#content`.
- **Inline `<script>` in `change_form.html` violated CSP.** `htmx_inline_save` rendered an inline script that wired `hx-post`/`hx-target`/`hx-swap` from `window.location.pathname`. Replaced with a `data-yp-inline-save` marker attribute; `bindInlineSave()` in `main.ts` reads `data-yp-inline-save-url` and calls `htmx.process()` on the enclosing form. CSP `script-src 'self'` now passes without `'unsafe-inline'`.
- **Form save reloaded the full page.** Add/change forms had no htmx wiring; saving round-tripped the chrome unnecessarily. `bindModelFormHtmx()` now wires `form[id$="_form"]` inside `#content-main` to POST via htmx with `hx-target="#content"`, `hx-select="#content"`, `hx-swap="outerHTML show:window:top"`, `hx-push-url="true"`. Errors render inline; valid saves follow Django's redirect (htmx fetches it and selects `#content`). Skipped when the form already has `hx-post` (inline-save shim, popup forms).
- **Custom `AdminSite` subclasses broke `yp_reorder` / `yp_revert` URL reverses.** `templatetags/yp_admin.py` and `history/admin.py` hardcoded `admin:` and `yp_admin:` namespaces. Fix: read `admin_site.name` from the bound site and build `{site_name}:yp_reorder` / `{site_name}:yp_revert`. `history.html` reads `revert_url_name` from context.
- **`OrderedModel.move_to()` sentinel could collide on high-pk rows.** The two-phase update used `max_order + self.pk + 1` as a temporary slot, which on tables with very large pks pushes the value far outside the unique-constraint range and stresses `PositiveIntegerField` bounds. Replaced with `max_order + len(locked) + 1` — small, deterministic, still outside any sibling shift's range.
- **Picnic CSS was loaded from `unpkg.com`.** Self-hosted as `static/yp_admin/css/picnic.min.css` and imported with a relative URL. Works offline, no third-party CSP allowance, no CDN drift.

### Internals

- `base.html` restored to Django stock structure (`{% block nav-breadcrumbs %}` wrapping `{% block breadcrumbs %}`); third-party templates that override only `breadcrumbs` keep working. Footer moved outside `<main>`.
- Removed three `xfail` markers in `tests/test_edge_cases.py` — the underlying bugs (DateRangeFilter naive datetime warnings, `move_to()` clamp >max, negative position) were already fixed in `0.1.0a3`/`0.1.0`; the markers are now plain assertions.
- New test: htmx_changelist + admin actions still POST normally (regression guard for the changelist form wrapper).

## 0.1.0 — 2026-04-28

First stable release. Same surface as `0.1.0a3` plus visual-polish CSS fixes, an `OrderedModel` correctness fix for non-FK grouping fields, multi-language documentation, and screenshots embedded in docs.

### Bug fixes

- **Dashboard app-list link contrast.** Picnic CSS sets `tbody th[scope="row"]` to a solid accent background; the inner `<a>` inherited the accent color too, so model labels (Authors, Blog posts, …) rendered ~invisible blue-on-blue. Fix: explicit white link color on those cells, and reset the accent background on changelist `<th class="field-…">` cells which lack `scope="row"`.
- **Changelist filter sidebar layout.** Picnic styles `<nav>` as a fixed top navbar (`position: fixed; top: 0; z-index: 10000`). `#changelist-filter` is a `<nav>` for semantics, but rendered as a full-width banner overlapping the page content. Fix: reset position/z-index/width on `#changelist-filter`.
- **Changelist 3-children grid flow.** `#changelist` has 3 grid items (`#toolbar`, `#changelist-form`, `#changelist-filter`), so `grid-template-columns: 1fr 14rem` placed the form into the narrow filter column. Fix: `#toolbar` and date hierarchy now `grid-column: 1 / -1`, leaving form/filter on the next row.
- **Related-popup `<dialog>` always visible.** `dialog.yp-related-popup` had unconditional `display: grid`, overriding the UA default `display: none` for closed `<dialog>`s. Result: an empty modal sat on top of every change-form page. Fix: scope `display: grid` to `[open]`.
- **`OrderedModel._wrt_filter_kwargs` assumed every wrt field was a FK.** A wrt tuple mixing FK + CharField (e.g. `order_with_respect_to = ("board", "status")`) raised `FieldError: Cannot resolve keyword 'status_id'` on save. Fix: introspect each field via `_meta.get_field()` and only append `_id` for `many_to_one` relations; bare field name otherwise.

### Documentation

- **i18n.** Full Spanish (`docs/es/`) and Portuguese-Brazilian (`docs/pt/`) translations of all reference pages. `mkdocs.yml` wires `mkdocs-static-i18n` (`en` default, `es`, `pt`).
- **Screenshots.** `docs/screenshots/` holds 13 PNGs captured from the demo project (Playwright, 1440×900). Embedded in `index`, `filters`, `singleton`, `ordered` (en/es/pt).
- Removed stale "~19 tests" reference; updated to 104.
- Replaced "Drop-in replacement for django.contrib.admin" wording in `mkdocs.yml` with the accurate "htmx-powered theme + helpers for django.contrib.admin".

### Demo

- Added four new demo apps to [django-yp-admin-demo](https://github.com/ypsoftware/django-yp-admin-demo): `cookbook` (Recipe + ordered Ingredients/Steps + difficulty Dropdown + cook-time NumericRange), `music` (Album + sortable Track + DateRange on release_date), `survey` (3-level NestedInline Survey → Question → Choice with versioning), `kanban` (Task ordered within `(board, status)` groups with the full filter family).

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
