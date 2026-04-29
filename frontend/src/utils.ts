/**
 * Shared frontend utilities for django-yp-admin.
 */

/**
 * Run a function when the DOM is ready. Handles both initial load
 * (DOMContentLoaded) and cases where the script runs after the
 * document has already parsed.
 */
export function onReady(fn: () => void): void {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", fn, { once: true });
  } else {
    fn();
  }
}
