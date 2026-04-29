# django-yp-admin

**Um tema com tecnologia htmx + helpers para `django.contrib.admin`. Duas dependências. Zero jQuery.**

`django-yp-admin` é um **tema de admin com tecnologia htmx mais um pequeno conjunto de helpers** para `django.contrib.admin`. Inclui sobrescritas de templates (Picnic CSS, widgets HTML5 nativos, htmx) e modelos abstratos e mixins de admin reutilizáveis (OrderedModel, SingletonModel, histórico leve, widgets htmx). É montado sobre o `AdminSite` padrão; **não** é um substituto completo.

!!! note "v0.1"
    105 testes em Python 3.11–3.14 × Django 4.2 / 5.2 / 6.0. Subclasses personalizadas de `AdminSite` e pacotes de admin de terceiros (**django-cms**, **wagtail**, **allauth**, **django-guardian**, **django-polymorphic**, **django-reversion**, **django-import-export** ponta a ponta) **ainda não estão validados**. Veja [Compatibilidade](compatibility.md).

## Visão geral

![Dashboard](../screenshots/dashboard.png)

Changelist com barra lateral de filtros, filtros de intervalo, multi-select:

![Changelist](../screenshots/changelist-blog.png)

## O que você ganha

- **Tema com tecnologia htmx.** Sobrescritas de templates para changelist, formulário de mudança e login. Base com Picnic CSS, tematizável via propriedades CSS personalizadas. Modo escuro via `prefers-color-scheme`.
- **Sem jQuery.** ~62KB gzip de JS total em vez de ~250KB.
- **Duas dependências obrigatórias.** Django + `django-htmx`. Extras opcionais quando quiser.
- **HTML5 nativo.** `<input type="date">`, `<dialog>`, `<details>` em vez de widgets jQuery.
- **Helpers (opt-in).** `OrderedModel`, `SingletonModel`, histórico leve, filtros com htmx, autocomplete com htmx + Tom Select, inlines aninhados/ordenáveis nativos com htmx.

## Instalação

```bash
pip install django-yp-admin
```

## Início rápido

```python
INSTALLED_APPS = [
    "django_yp_admin",   # before django.contrib.admin
    "django.contrib.admin",
    "django_htmx",
    # ...
]
```

Abra `/admin/`. Os admins padrão continuam funcionando com o novo tema. Para ativar filtros e widgets nativos de htmx por modelo, troque a classe base do seu `ModelAdmin` para `django_yp_admin.options.ModelAdmin`.

## Próximos passos

- [Instalação](installation.md)
- [Início rápido](quickstart.md)
- [Referência de ModelAdmin](modeladmin.md)
- [Filtros](filters.md)
- [Singletons](singleton.md)
- [Modelos ordenados](ordered.md)
- [Versionamento](versioning.md)
- [Extras opcionais](optional-extras.md)
- [Suporte de navegadores](browser-support.md)
- [Compatibilidade](compatibility.md)
