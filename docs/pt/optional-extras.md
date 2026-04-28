# Extras opcionais

Pacotes pesados que afetam a app inteira ficam como opt-in. A integração do admin é ativada automaticamente quando a dependência está instalada.

## Extras disponíveis

```bash
pip install django-yp-admin[history]        # django-simple-history (>=3.5)
pip install django-yp-admin[import-export]  # django-import-export (>=4.0)
pip install django-yp-admin[full]           # both
```

## Semântica de ativação

Cada módulo de integração consulta a dependência opcional com `importlib.util.find_spec`:

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

Se a dependência estiver faltando, a classe wrapper é `None`. Você pode:

1. Proteger antes de herdar:
   ```python
   from django_yp_admin.contrib.history_admin import HistoryAdmin
   if HistoryAdmin is not None:
       class MyAdmin(HistoryAdmin, ModelAdmin):
           ...
   ```
2. Importar incondicionalmente e deixar que `pip install django-yp-admin[history]` seja a solução óbvia quando o import falhar ou a classe for `None`.

## Wrappers disponíveis

| Módulo | Classe | Ativado por |
|---|---|---|
| `django_yp_admin.contrib.history_admin` | `HistoryAdmin` | `pip install django-yp-admin[history]` |
| `django_yp_admin.contrib.import_export_admin` | `ImportExportAdmin` | `pip install django-yp-admin[import-export]` |

Ambos os wrappers preservam a API upstream e adicionam nossos templates cientes de htmx.

## Alpine.js: bundle opcional

Alpine é **opt-in**. O build do frontend emite dois artefatos sob
`django_yp_admin/static/yp_admin/js/`:

| Arquivo | Conteúdo | Tamanho minificado aprox. |
|---|---|---|
| `yp-admin.js` | htmx + Tom Select + nosso TS. Alpine resolvido a um stub no-op. | ~124 KB (~40 KB gzip) |
| `yp-admin-alpine.js` | O mesmo do anterior **mais** Alpine.js. | ~171 KB (~55 KB gzip) |

`ModelAdmin.media` por padrão referencia `yp-admin.js`. Para ativar o estado de UI local com Alpine no seu projeto, troque o arquivo na sua classe `Media`:

```python
class MyAdmin(admin.ModelAdmin):
    class Media:
        js = ("yp_admin/js/yp-admin-alpine.js",)
```

Está planejada uma flag `Meta.use_alpine = True` em `ModelAdmin` para automatizar a troca em uma versão futura.

### Como a divisão funciona

`frontend/build.ts` roda `Bun.build` duas vezes. A variante slim usa um plugin `onResolve` do Bun que redireciona `import Alpine from "alpinejs"` para um pequeno stub proxy no-op, então os ~50 KB do fonte do Alpine nunca chegam ao bundle slim. A variante full resolve `alpinejs` normalmente. O define de build `__WITH_ALPINE__` também é exposto para futuros gates `if (__WITH_ALPINE__)` no código de usuário.

## Política de XSS no autocomplete

As opções de autocomplete são renderizadas como **texto** por padrão. Os renderers `option`/`item` embutidos do Tom Select escapam o campo `text` automaticamente, e o payload do popup de objeto relacionado (`event.detail.newRepr`) é adicionalmente sanitizado em `autocomplete.ts` antes de chegar ao `addOption`.

Se você customizar o Tom Select via uma config `render` que retorna uma string HTML, você **deve** escapar cada campo fornecido pelo usuário com o helper `escape()` exportado de `frontend/src/autocomplete.ts`:

```ts
import { escape } from "./autocomplete";

new TomSelect(el, {
  render: {
    option: (data) => `<div class="opt">${escape(data.text)}</div>`,
    //                                    ^^^^^^^ required to prevent XSS
  },
});
```

Retornar `data.text` interpolado diretamente em um template literal é um sink de XSS. Os reviewers devem rejeitar qualquer patch que faça isso.
