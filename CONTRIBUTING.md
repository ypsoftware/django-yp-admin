# Contributing to django-yp-admin

Thanks for your interest. This package aims to be a **drop-in, jQuery-free, htmx-powered** replacement for the Django admin with a tiny dependency tree. Contributions that move us closer to that goal are welcome.

## Ground rules

1. **No jQuery.** Ever. If a feature seems to need it, it does not.
2. **Two mandatory deps only**: Django + django-htmx. Anything else goes to optional extras.
3. **Build step is allowed for JS/CSS sources** but bundled output must be committed under `django_yp_admin/static/yp_admin/`. End users install via `pip` and never see Bun. Contributors touching `frontend/src/` need Bun: `curl -fsSL https://bun.sh/install | bash`.
4. **Modern browsers only**: last 3 years of Firefox, Chrome, Safari, Edge. Use native `<dialog>`, `:has()`, CSS nesting, `<input type="date">` freely.
5. **Keep `ModelAdmin` API identical.** Drop-in is the headline feature. Breaking it kills the project.
6. **Preserve legacy CSS class hooks**: `.module`, `.results`, `.changelist`, `.submit-row`, `.inline-group`, `.empty-form`, `.action-checkbox-column`. Third-party addons rely on them.
7. **Preserve template block names**: `object-tools-items`, `submit_buttons_top/bottom`, `extrahead`, `extrastyle`, `content`, `nav-global`, `breadcrumbs`.

## Dev setup

Python side:

```bash
git clone https://github.com/ypsoftware/django-yp-admin
cd django-yp-admin
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Frontend side (only if you touch `frontend/src/`):

```bash
cd frontend
bun install
bun run build       # outputs to django_yp_admin/static/yp_admin/
bun run watch       # rebuild on change
```

## Project layout

```
django_yp_admin/      # package source (Python)
  templates/admin/    # template overrides
  static/yp_admin/    # bundled JS + CSS (committed, output of Bun)
  templatetags/
  views/
frontend/             # JS/TS source (committed, NOT shipped in wheel)
  src/                # TypeScript modules
  package.json
  build.ts
docs/                 # public ReadTheDocs site (MkDocs Material)
internal-docs/        # research, design notes (gitignored)
tests/                # pytest suite
```

## Workflow

1. Open an issue first for non-trivial changes.
2. Branch from `main`. Branch name: `feat/...`, `fix/...`, `docs/...`.
3. Run tests and linters before pushing: `pytest`, `ruff check`, `ruff format`.
4. If you touched JS, rebuild and commit the output: `cd frontend && bun run build`.
5. PR description must explain **what breaks** and **what addon compat is preserved**.
6. Add or update tests. We do not merge untested behavior changes.
7. Update `docs/` when changing user-facing behavior.

## Commit messages

Conventional Commits. Subject ≤50 chars.

```
feat(autocomplete): replace Select2 with Tom Select
fix(inlines): preserve __prefix__ for legacy addons
docs(readme): refresh dep tree numbers
```

## Compatibility tests

Every PR touching templates, static, or `ModelAdmin` integration must include a matrix run against the optional extras:

- django-import-export
- django-simple-history
- django-guardian
- django-polymorphic
- django-ordered-model
- django-filter

If you break one, propose a shim or revert.

## Code style

- **Python**: ruff defaults, type hints on public API.
- **HTML**: 2-space indent, semantic tags, ARIA attributes on interactive widgets.
- **CSS**: custom properties for tokens, no `!important` unless overriding Django admin. Use native CSS nesting.
- **TypeScript**: vanilla ES2022. No jQuery. No frameworks beyond htmx + optional Alpine + Tom Select.

## License

By contributing you agree your work is licensed under MIT.

## Contact

Yp Software <info@ypsoftware.com.py>
