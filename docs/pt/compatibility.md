# Compatibilidade

!!! warning "v0.1, pré-alfa — leia isto primeiro"
    `django-yp-admin` é um **tema com tecnologia htmx + helpers** para `django.contrib.admin`, **não** um substituto completo. A suíte de testes atual (104 testes) exercita o tema, os helpers e uma fatia fina das integrações opcionais. As alegações de compatibilidade abaixo descrevem **intenção de design**, não garantias validadas por testes de regressão.

Esta página documenta o que é preservado por design, o que se sabe que quebra e o que ainda não está suportado.

## O que é preservado (por design)

Estas são escolhas de design intencionais. **Ainda não são cobertas por testes de regressão com terceiros** — por favor abra issues se você encontrar um quebra.

- **API de `ModelAdmin`.** `django_yp_admin.options.ModelAdmin` herda de `django.contrib.admin.ModelAdmin`. A intenção é que toda opção padrão (`fieldsets`, `inlines`, `readonly_fields`, `prepopulated_fields`, `formfield_overrides`, `get_queryset`, …) continue funcionando.
- **`AdminSite` padrão.** Usamos `django.contrib.admin.site` diretamente. **Não** entregamos nossa própria subclasse de `AdminSite`.
- **Classes CSS legadas.** `.module`, `.results`, `.changelist`, `.submit-row`, `.inline-group`, `.empty-form`, `.row1`, `.row2`, etc. continuam como hooks do DOM. Os estilos do Picnic são aplicados em paralelo.
- **Nomes de `{% block %}` em templates.** `content`, `extrahead`, `extrastyle`, `branding`, `nav-global`, `breadcrumbs`, `object-tools`, `pagination` — preservados.
- **Contrato de URL de `AutocompleteJsonView`.** Mesmo path, mesmo formato JSON (`{"results": [...], "pagination": {"more": ...}}`).

## O que se sabe que quebra

- **`django.jQuery`.** O global se foi. JS que chamava `django.jQuery(...)` vai falhar. Migre para APIs vanilla do DOM ou atributos de htmx.
- **Widgets de jQuery UI.** SortableJS / jQuery UI Sortable, widgets de calendário/relógio em popup foram substituídos por HTML5 Drag & Drop, `<input type="date">`, `<input type="time">`. Drop-in para o usuário final; quebra para extensões JS.
- **Select2.** Substituído pelo Tom Select. Código de inicialização customizado do Select2 não vai rodar.

## Roadmap / Ainda não suportado

O seguinte está **no roadmap mas ainda não testado ou validado**. Se seu projeto depende disso, fique no `django.contrib.admin` por enquanto.

### Subclasses personalizadas de AdminSite

Atualmente miramos no `admin.site` padrão. Projetos que herdam de `AdminSite` (login customizado, index customizado, configurações multi-site) estão **não testados**.

### Pacotes de admin de terceiros

Estes antes apareciam como "compatibilidade testada". Era aspiracional. **Ainda não estão validados**:

- **django-reversion** — `VersionAdmin` ponta a ponta.
- **django-import-export** — `ImportExportModelAdmin` ponta a ponta (existe integração básica via o extra `[import-export]`, mas o uso no mundo real não está verificado).
- **django-guardian** — `GuardedModelAdmin`.
- **django-polymorphic** — `PolymorphicChildModelAdmin`.
- **django-modeltranslation** — abas do admin.
- **django-nested-admin**, **django-admin-sortable2**, **django-admin-rangefilter**, **django-autocomplete-light**, **django-filter** — a coexistência com nossas reimplementações não está verificada.

### Frameworks que trazem seu próprio admin

- **django-cms** — páginas do admin e toolbar.
- **wagtail** — o admin do Wagtail vive em uma URL separada mas compartilha alguns templates/static; não testado.
- **allauth** — páginas do admin e UI de gestão de contas.

### Temas de terceiros

Temas que miram nas classes CSS legadas do admin devem continuar renderizando já que preservamos esses hooks — mas não fizemos testes de regressão com nenhum tema específico. Espere arestas onde o Picnic e o CSS do tema interagem.

## Guia de migração (para o caminho suportado)

Melhor encaixe hoje: um projeto que usa **`django.contrib.admin` padrão** com subclasses **padrão de `ModelAdmin`**, sem subclasse de `AdminSite`, e sem pacotes de admin de terceiros das listas acima.

1. Adicione `django_yp_admin` antes de `django.contrib.admin` em `INSTALLED_APPS`.
2. Adicione `django_htmx` e `django_htmx.middleware.HtmxMiddleware`.
3. Visite `/admin/`. Os admins padrão devem renderizar com o novo tema.
4. Procure `django.jQuery` no projeto — substitua qualquer ocorrência por JS vanilla.
5. Opcional: troque `from django.contrib.admin import ModelAdmin` por `from django_yp_admin.options import ModelAdmin` para ativar filtros e widgets nativos de htmx por modelo.

Relatórios de compatibilidade do mundo real contra `AdminSite` customizados e pacotes de terceiros são especialmente bem-vindos — por favor abra issues.
