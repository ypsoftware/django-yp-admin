"""django-simple-history integration. Active only if simple_history is installed."""

import importlib.util

if importlib.util.find_spec("simple_history") is not None:
    from simple_history.admin import SimpleHistoryAdmin

    class HistoryAdmin(SimpleHistoryAdmin):
        """Re-exported SimpleHistoryAdmin. Inherits our base templates via app loader.

        Currently a thin alias provided as an integration hook. No yp-specific
        overrides yet; add htmx flags / Picnic templates in a future release.
        """
else:
    HistoryAdmin = None  # type: ignore

__all__ = ["HistoryAdmin"]
