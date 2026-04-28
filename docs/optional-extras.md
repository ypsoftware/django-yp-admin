# Optional extras

Heavy app-wide packages stay opt-in. Admin integration auto-activates when the dep is installed.

## Available extras

```bash
pip install django-yp-admin[history]        # django-simple-history (>=3.5)
pip install django-yp-admin[import-export]  # django-import-export (>=4.0)
pip install django-yp-admin[full]           # both
```

## Activation semantics

Each integration module probes for the optional dep with `importlib.util.find_spec`:

```python
# django_yp_admin/contrib/history_admin.py
import importlib.util

if importlib.util.find_spec("simple_history") is not None:
    from simple_history.admin import SimpleHistoryAdmin

    class HistoryAdmin(SimpleHistoryAdmin):
        ...
else:
    HistoryAdmin = None
```

If the dep is missing, the wrapper class is `None`. You can either:

1. Guard before subclassing:
   ```python
   from django_yp_admin.contrib.history_admin import HistoryAdmin
   if HistoryAdmin is not None:
       class MyAdmin(HistoryAdmin, ModelAdmin):
           ...
   ```
2. Import unconditionally and let `pip install django-yp-admin[history]` be the obvious fix when the import fails or the class is `None`.

## Available wrappers

| Module | Class | Activated by |
|---|---|---|
| `django_yp_admin.contrib.history_admin` | `HistoryAdmin` | `pip install django-yp-admin[history]` |
| `django_yp_admin.contrib.import_export_admin` | `ImportExportAdmin` | `pip install django-yp-admin[import-export]` |

Both wrappers preserve the upstream API and add our htmx-aware templates.

## Alpine.js: optional bundle

Alpine is **opt-in**. The frontend build emits two artifacts under
`django_yp_admin/static/yp_admin/js/`:

| File | Contents | Approx. minified size |
|---|---|---|
| `yp-admin.js` | htmx + Tom Select + our TS. Alpine resolved to a no-op stub. | ~124 KB (~40 KB gzip) |
| `yp-admin-alpine.js` | Same as above **plus** Alpine.js. | ~171 KB (~55 KB gzip) |

Default `ModelAdmin.media` references `yp-admin.js`. To enable Alpine-driven
local UI state in your project, swap the file in your overriding `Media` class:

```python
class MyAdmin(admin.ModelAdmin):
    class Media:
        js = ("yp_admin/js/yp-admin-alpine.js",)
```

A `Meta.use_alpine = True` flag on `ModelAdmin` is planned to automate the
swap in a future release.

### How the split works

`frontend/build.ts` runs `Bun.build` twice. The slim variant uses a Bun
`onResolve` plugin that redirects `import Alpine from "alpinejs"` to a tiny
no-op proxy stub, so Alpine's ~50 KB source never reaches the slim bundle.
The full variant resolves `alpinejs` normally. The build define
`__WITH_ALPINE__` is also exposed for any future `if (__WITH_ALPINE__)` gates
in user code.

## Autocomplete XSS policy

Autocomplete options render as **text** by default. Tom Select's built-in
`option`/`item` renderers escape the `text` field automatically, and the
related-object popup payload (`event.detail.newRepr`) is additionally
sanitized in `autocomplete.ts` before reaching `addOption`.

If you customize Tom Select via a `render` config that returns an HTML
string, you **must** escape every user-provided field with the `escape()`
helper exported from `frontend/src/autocomplete.ts`:

```ts
import { escape } from "./autocomplete";

new TomSelect(el, {
  render: {
    option: (data) => `<div class="opt">${escape(data.text)}</div>`,
    //                                    ^^^^^^^ required to prevent XSS
  },
});
```

Returning `data.text` interpolated directly into a template literal is an
XSS sink. Reviewers should reject any patch that does so.
