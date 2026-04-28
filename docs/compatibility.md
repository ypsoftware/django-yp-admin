# Compatibility

!!! warning "v0.1, pre-alpha — read this first"
    `django-yp-admin` is an **htmx-powered theme + helpers** for `django.contrib.admin`, **not** a full drop-in replacement. The current test suite (104 tests) exercises the theme, helpers, and a thin slice of the optional integrations. The compatibility claims below describe **design intent**, not regression-tested guarantees.

This page documents what is preserved by design, what is known to break, and what is not yet supported.

## What is preserved (by design)

These are intentional design choices. They are **not yet covered by third-party regression tests** — please file issues if you hit a break.

- **`ModelAdmin` API.** `django_yp_admin.options.ModelAdmin` subclasses `django.contrib.admin.ModelAdmin`. Every standard option (`fieldsets`, `inlines`, `readonly_fields`, `prepopulated_fields`, `formfield_overrides`, `get_queryset`, …) is meant to keep working.
- **Stock `AdminSite`.** We use `django.contrib.admin.site` directly. We do **not** ship our own `AdminSite` subclass.
- **Legacy CSS classes.** `.module`, `.results`, `.changelist`, `.submit-row`, `.inline-group`, `.empty-form`, `.row1`, `.row2`, etc. remain as DOM hooks. Picnic styles are layered alongside.
- **Template `{% block %}` names.** `content`, `extrahead`, `extrastyle`, `branding`, `nav-global`, `breadcrumbs`, `object-tools`, `pagination` — preserved.
- **`AutocompleteJsonView` URL contract.** Same path, same JSON shape (`{"results": [...], "pagination": {"more": ...}}`).

## What is known to break

- **`django.jQuery`.** The global is gone. JS that called `django.jQuery(...)` will fail. Migrate to vanilla DOM APIs or htmx attributes.
- **jQuery UI widgets.** SortableJS / jQuery UI Sortable, calendar/clock popup widgets are replaced by HTML5 Drag & Drop, `<input type="date">`, `<input type="time">`. Drop-in for end users; breaking for JS extensions.
- **Select2.** Replaced by Tom Select. Custom Select2 init code will not run.

## Roadmap / Not yet supported

The following are **on the roadmap but not yet tested or validated**. If your project depends on them, stay on `django.contrib.admin` for now.

### Custom AdminSite subclasses

We currently target the stock `admin.site`. Projects that subclass `AdminSite` (custom login, custom index, multi-site setups) are **untested**.

### Third-party admin packages

These were previously listed as "tested compatible". That was aspirational. They are **not yet validated**:

- **django-reversion** — `VersionAdmin` end-to-end.
- **django-import-export** — `ImportExportModelAdmin` end-to-end (basic integration via the `[import-export]` extra exists, but real-world usage is unverified).
- **django-guardian** — `GuardedModelAdmin`.
- **django-polymorphic** — `PolymorphicChildModelAdmin`.
- **django-modeltranslation** — admin tabs.
- **django-nested-admin**, **django-admin-sortable2**, **django-admin-rangefilter**, **django-autocomplete-light**, **django-filter** — coexistence with our reimplementations is unverified.

### Frameworks that ship their own admin

- **django-cms** — admin pages and toolbar.
- **wagtail** — Wagtail's admin lives at a separate URL but shares some templates/static; untested.
- **allauth** — admin pages and account management UI.

### Third-party themes

Themes that target legacy admin CSS classes should keep rendering since we preserve those hooks — but we have not regression-tested any specific theme. Expect rough edges where Picnic and the theme's CSS interact.

## Migration guide (for the supported path)

Best fit today: a project using **stock `django.contrib.admin`** with **stock `ModelAdmin`** subclasses, no `AdminSite` subclass, and no third-party admin packages from the lists above.

1. Add `django_yp_admin` before `django.contrib.admin` in `INSTALLED_APPS`.
2. Add `django_htmx` and `django_htmx.middleware.HtmxMiddleware`.
3. Visit `/admin/`. Stock admins should render with the new theme.
4. Search the project for `django.jQuery` — replace any hits with vanilla JS.
5. Optional: switch `from django.contrib.admin import ModelAdmin` to `from django_yp_admin.options import ModelAdmin` to opt into htmx-native filters/widgets per model.

Real-world compat reports against custom `AdminSite` and third-party packages are especially welcome — please file issues.
