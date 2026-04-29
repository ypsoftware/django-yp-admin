# Compatibilidad

!!! warning "v0.1 — lee esto primero"
    `django-yp-admin` es un **tema impulsado por htmx + helpers** para `django.contrib.admin`, **no** un reemplazo completo. La suite de tests actual (105 tests) ejercita el tema, los helpers y una porción mínima de las integraciones opcionales. Las afirmaciones de compatibilidad de abajo describen **intención de diseño**, no garantías validadas por tests de regresión.

Esta página documenta lo que se preserva por diseño, lo que se sabe que se rompe y lo que todavía no está soportado.

## Lo que se preserva (por diseño)

Estas son decisiones de diseño intencionales. **Todavía no están cubiertas por tests de regresión con terceros** — por favor abre un issue si te encuentras con un quiebre.

- **API de `ModelAdmin`.** `django_yp_admin.options.ModelAdmin` hereda de `django.contrib.admin.ModelAdmin`. La intención es que cada opción estándar (`fieldsets`, `inlines`, `readonly_fields`, `prepopulated_fields`, `formfield_overrides`, `get_queryset`, …) siga funcionando.
- **`AdminSite` estándar.** Usamos `django.contrib.admin.site` directamente. **No** incluimos nuestra propia subclase de `AdminSite`.
- **Clases CSS legacy.** `.module`, `.results`, `.changelist`, `.submit-row`, `.inline-group`, `.empty-form`, `.row1`, `.row2`, etc. permanecen como hooks del DOM. Los estilos de Picnic se aplican en paralelo.
- **Nombres de `{% block %}` en templates.** `content`, `extrahead`, `extrastyle`, `branding`, `nav-global`, `breadcrumbs`, `object-tools`, `pagination` — preservados.
- **Contrato de URL de `AutocompleteJsonView`.** Mismo path, misma forma JSON (`{"results": [...], "pagination": {"more": ...}}`).

## Lo que se sabe que se rompe

- **`django.jQuery`.** El global ya no está. JS que llamaba a `django.jQuery(...)` va a fallar. Migra a APIs vanilla del DOM o atributos de htmx.
- **Widgets de jQuery UI.** SortableJS / jQuery UI Sortable, widgets de calendario/reloj popup están reemplazados por HTML5 Drag & Drop, `<input type="date">`, `<input type="time">`. Drop-in para el usuario final; ruptura para extensiones JS.
- **Select2.** Reemplazado por Tom Select. El código de inicialización personalizado de Select2 no se va a ejecutar.

## Roadmap / Aún no soportado

Lo siguiente está **en el roadmap pero todavía no probado o validado**. Si tu proyecto depende de algo de esto, mantente en `django.contrib.admin` por ahora.

### Subclases personalizadas de AdminSite

Actualmente apuntamos al `admin.site` estándar. Los proyectos que heredan de `AdminSite` (login personalizado, index personalizado, configuraciones multi-site) están **sin probar**.

### Paquetes de admin de terceros

Estos antes figuraban como "compatibilidad probada". Era aspiracional. **Aún no están validados**:

- **django-reversion** — `VersionAdmin` de extremo a extremo.
- **django-import-export** — `ImportExportModelAdmin` de extremo a extremo (existe integración básica vía el extra `[import-export]`, pero el uso en el mundo real no está verificado).
- **django-guardian** — `GuardedModelAdmin`.
- **django-polymorphic** — `PolymorphicChildModelAdmin`.
- **django-modeltranslation** — pestañas del admin.
- **django-nested-admin**, **django-admin-sortable2**, **django-admin-rangefilter**, **django-autocomplete-light**, **django-filter** — la coexistencia con nuestras reimplementaciones no está verificada.

### Frameworks que traen su propio admin

- **django-cms** — páginas del admin y toolbar.
- **wagtail** — el admin de Wagtail vive en una URL separada pero comparte algunos templates/static; no probado.
- **allauth** — páginas del admin y UI de gestión de cuentas.

### Temas de terceros

Los temas que apuntan a las clases CSS legacy del admin deberían seguir renderizando ya que preservamos esos hooks — pero no hemos hecho tests de regresión con ningún tema específico. Espera asperezas donde Picnic y el CSS del tema interactúan.

## Guía de migración (para el camino soportado)

Mejor encaje hoy: un proyecto que usa **`django.contrib.admin` estándar** con subclases **estándar de `ModelAdmin`**, sin subclase de `AdminSite`, y sin paquetes de admin de terceros de las listas de arriba.

1. Agrega `django_yp_admin` antes de `django.contrib.admin` en `INSTALLED_APPS`.
2. Agrega `django_htmx` y `django_htmx.middleware.HtmxMiddleware`.
3. Visita `/admin/`. Los admins estándar deberían renderizar con el nuevo tema.
4. Busca `django.jQuery` en el proyecto — reemplaza cualquier coincidencia con JS vanilla.
5. Opcional: cambia `from django.contrib.admin import ModelAdmin` a `from django_yp_admin.options import ModelAdmin` para activar filtros y widgets nativos de htmx por modelo.

Reportes de compatibilidad del mundo real contra `AdminSite` personalizados y paquetes de terceros son especialmente bienvenidos — por favor abre issues.
