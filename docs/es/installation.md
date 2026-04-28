# Instalación

!!! warning "v0.1, pre-alfa"
    `django-yp-admin` es un **tema + helpers** montado sobre `django.contrib.admin`, no un reemplazo completo. Las subclases personalizadas de `AdminSite` y los paquetes de admin de terceros (django-cms, wagtail, allauth, etc.) **todavía no** han sido probados. Consulta [Compatibilidad](compatibility.md).

## Requisitos

- Python 3.10+
- Django 4.2+
- `django-htmx` 1.17+

## Instalación

```bash
pip install django-yp-admin
```

## Configuración

Agrega `django_yp_admin` a `INSTALLED_APPS` **antes** de `django.contrib.admin`. La resolución de templates depende del orden — nuestro paquete debe ir primero para que `admin/base_site.html`, `admin/change_list.html`, etc. tengan precedencia.

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

No se requieren cambios de URL — mantén `path("admin/", admin.site.urls)`. Usamos el `admin.site` estándar; **no** incluimos nuestro propio `AdminSite`.

## Extras opcionales

```bash
pip install django-yp-admin[history]        # adds django-simple-history
pip install django-yp-admin[import-export]  # adds django-import-export
pip install django-yp-admin[full]           # both
```

Cuando el paquete opcional está instalado, la integración de admin correspondiente en `django_yp_admin.contrib` se activa automáticamente vía `importlib.util.find_spec`. Existe cobertura básica de tests; la validación a nivel de producción está pendiente. Consulta [Extras opcionales](optional-extras.md).

## Verificación

Ejecuta el servidor de desarrollo y visita `/admin/`. Deberías ver el estilo de Picnic CSS y (en changelists registradas con `django_yp_admin.options.ModelAdmin`) filtros impulsados por htmx.

## Lo que NO está soportado todavía

Si tu proyecto usa alguno de los siguientes, **mantente en `django.contrib.admin` por ahora** — todavía no los hemos validado:

- Una subclase personalizada de `AdminSite` (tu propio `admin.AdminSite(...)`).
- Páginas de admin de **django-cms**, **wagtail**, **allauth**.
- **django-guardian** (`GuardedModelAdmin`), **django-polymorphic** (`PolymorphicChildModelAdmin`).
- Uso de extremo a extremo de **django-reversion** `VersionAdmin` o **django-import-export** `ImportExportModelAdmin`.
- Extensiones JS legacy que llaman a `django.jQuery` — se romperán.
