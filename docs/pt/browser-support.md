# Suporte de navegadores

`django-yp-admin` mira **apenas navegadores modernos** — os últimos 3 anos de releases. É uma escolha deliberada: usamos `<dialog>` nativo, `:has()`, aninhamento CSS, container queries, inputs de data confiáveis e ES2022. É por isso que o bundle de JS é de 8KB em vez de 250KB.

| Navegador | Versão mínima | Lançado |
|---|---|---|
| Firefox | 115 (ESR) | Julho 2023 |
| Chrome | 115 | Julho 2023 |
| Safari | 16.4 | Março 2023 |
| Edge | 115 (Chromium) | Julho 2023 |

Se você precisa suportar navegadores mais antigos, fique com `django.contrib.admin`. Não vamos adicionar polyfills.

## Tamanho do stack

| Camada | Ferramenta | Tamanho (gzip) |
|---|---|---:|
| AJAX | htmx | ~14KB |
| Estado de UI local (opcional) | Alpine.js | ~15KB |
| Autocomplete | Tom Select | ~25KB |
| Base CSS | Picnic CSS | ~10KB |
| Nosso código | TypeScript bundleado com Bun | ~8KB |
| **Total** | | **~62KB** |

Compare com os ~250KB de jQuery + Select2 + xregexp + JS personalizado do admin padrão.
