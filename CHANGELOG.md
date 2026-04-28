# Changelog

## 0.1.0 — pre-alpha (unreleased)

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
