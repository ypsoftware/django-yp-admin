# Soporte de navegadores

`django-yp-admin` apunta a **navegadores modernos solamente** — los últimos 3 años de versiones. Es una elección deliberada: usamos `<dialog>` nativo, `:has()`, anidamiento CSS, container queries, inputs de fecha confiables y ES2022. Por eso el bundle de JS es de 8KB en lugar de 250KB.

| Navegador | Versión mínima | Lanzado |
|---|---|---|
| Firefox | 115 (ESR) | Julio 2023 |
| Chrome | 115 | Julio 2023 |
| Safari | 16.4 | Marzo 2023 |
| Edge | 115 (Chromium) | Julio 2023 |

Si necesitas soportar navegadores más antiguos, quédate con `django.contrib.admin`. No agregaremos polyfills.

## Tamaño del stack

| Capa | Herramienta | Tamaño (gzip) |
|---|---|---:|
| AJAX | htmx | ~14KB |
| Estado de UI local (opcional) | Alpine.js | ~15KB |
| Autocompletado | Tom Select | ~25KB |
| Base CSS | Picnic CSS | ~10KB |
| Nuestro código | TypeScript bundleado con Bun | ~8KB |
| **Total** | | **~62KB** |

Compara con los ~250KB de jQuery + Select2 + xregexp + JS personalizado del admin por defecto.
