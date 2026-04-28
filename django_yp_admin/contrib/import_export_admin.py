"""django-import-export integration. Active only if import_export is installed."""

import importlib.util

if importlib.util.find_spec("import_export") is not None:
    from import_export.admin import ImportExportModelAdmin

    class ImportExportAdmin(ImportExportModelAdmin):
        """Re-exported ImportExportModelAdmin. Integration hook only.

        Currently a thin alias. No yp-specific template overrides yet; add
        Picnic-aware import/export templates in a future release.
        """
else:
    ImportExportAdmin = None  # type: ignore

__all__ = ["ImportExportAdmin"]
