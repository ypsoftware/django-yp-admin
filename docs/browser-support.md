# Browser support

`django-yp-admin` targets **modern browsers only** — last 3 years of releases. This is a deliberate choice: we use native `<dialog>`, `:has()`, CSS nesting, container queries, reliable date inputs, and ES2022. That is why the JS bundle is 8KB instead of 250KB.

| Browser | Minimum version | Released |
|---|---|---|
| Firefox | 115 (ESR) | July 2023 |
| Chrome | 115 | July 2023 |
| Safari | 16.4 | March 2023 |
| Edge | 115 (Chromium) | July 2023 |

If you need to support older browsers, stick with `django.contrib.admin`. We will not add polyfills.

## Stack size

| Layer | Tool | Size (gzip) |
|---|---|---:|
| AJAX | htmx | ~14KB |
| Local UI state (optional) | Alpine.js | ~15KB |
| Autocomplete | Tom Select | ~25KB |
| CSS base | Picnic CSS | ~10KB |
| Our code | TypeScript bundled with Bun | ~8KB |
| **Total** | | **~62KB** |

Compare with the default admin's ~250KB of jQuery + Select2 + xregexp + custom JS.
