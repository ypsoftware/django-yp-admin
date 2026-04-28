# Instalação

!!! warning "v0.1, pré-alfa"
    `django-yp-admin` é um **tema + helpers** montado sobre `django.contrib.admin`, não um substituto completo. Subclasses personalizadas de `AdminSite` e pacotes de admin de terceiros (django-cms, wagtail, allauth, etc.) **ainda não** foram testados. Veja [Compatibilidade](compatibility.md).

## Requisitos

- Python 3.10+
- Django 4.2+
- `django-htmx` 1.17+

## Instalação

```bash
pip install django-yp-admin
```

## Configurações

Adicione `django_yp_admin` em `INSTALLED_APPS` **antes** de `django.contrib.admin`. A resolução de templates depende da ordem — nosso pacote precisa vir primeiro para que `admin/base_site.html`, `admin/change_list.html`, etc. tenham precedência.

```python
INSTALLED_APPS = [
    # ...
    "django_htmx",
    "django_yp_admin",        # before django.contrib.admin
    "django.contrib.admin",
    # ...
]

MIDDLEWARE = [
    # ...
    "django_htmx.middleware.HtmxMiddleware",
]
```

Não são necessárias mudanças de URL — mantenha `path("admin/", admin.site.urls)`. Usamos o `admin.site` padrão; **não** entregamos nosso próprio `AdminSite`.

## Extras opcionais

```bash
pip install django-yp-admin[history]        # adds django-simple-history
pip install django-yp-admin[import-export]  # adds django-import-export
pip install django-yp-admin[full]           # both
```

Quando o pacote opcional está instalado, a integração de admin correspondente em `django_yp_admin.contrib` é ativada automaticamente via `importlib.util.find_spec`. Existe cobertura básica de testes; a validação para produção está pendente. Veja [Extras opcionais](optional-extras.md).

## Verificação

Rode o servidor de desenvolvimento, visite `/admin/`. Você deve ver o estilo do Picnic CSS e (em changelists registradas com `django_yp_admin.options.ModelAdmin`) filtros com tecnologia htmx.

## O que NÃO está suportado ainda

Se seu projeto usa algum dos seguintes, **fique no `django.contrib.admin` por enquanto** — ainda não validamos isso:

- Uma subclasse personalizada de `AdminSite` (seu próprio `admin.AdminSite(...)`).
- Páginas de admin do **django-cms**, **wagtail**, **allauth**.
- **django-guardian** (`GuardedModelAdmin`), **django-polymorphic** (`PolymorphicChildModelAdmin`).
- Uso ponta a ponta de **django-reversion** `VersionAdmin` ou **django-import-export** `ImportExportModelAdmin`.
- Extensões JS legadas que chamam `django.jQuery` — vão quebrar.
