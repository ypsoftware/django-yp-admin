# Frontend (django-yp-admin)

TypeScript source bundled with [Bun](https://bun.sh/). Output goes to `../django_yp_admin/static/yp_admin/js/yp-admin.js` and is committed to the repo. End users install via `pip` and never see this directory.

## Setup

```bash
curl -fsSL https://bun.sh/install | bash   # if you don't have Bun
cd frontend
bun install
```

## Build

```bash
bun run build      # one-shot, minified
bun run watch      # rebuild on change, with sourcemaps
bun run typecheck  # tsc --noEmit
```

## Layout

```
src/
  main.ts            entry point
  autocomplete.ts    htmx + Tom Select
  sortable.ts        HTML5 drag&drop reorder
  nested-inline.ts   htmx-native nested inlines
  popup-shim.ts      compat for legacy related-object popup protocol
build.ts             Bun build script
package.json
tsconfig.json
bunfig.toml
```

## Browser baseline

ES2022. Last 3 years of Firefox / Chrome / Safari / Edge. No transpilation.
