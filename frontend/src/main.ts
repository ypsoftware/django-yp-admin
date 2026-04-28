/**
 * django-yp-admin frontend entry.
 *
 * Imports htmx, Alpine, Tom Select, and our own modules. Bun bundles everything
 * into a single yp-admin.js shipped under django_yp_admin/static/yp_admin/js/.
 */

import htmx from "htmx.org";
import Alpine from "alpinejs";
import "tom-select";

import "./autocomplete";
import "./sortable";
import "./nested-inline";
import "./popup-shim";

declare global {
  interface Window {
    Alpine: typeof Alpine;
    htmx: typeof htmx;
  }
}

window.htmx = htmx;
window.Alpine = Alpine;

htmx.config.includeIndicatorStyles = false;
htmx.config.scrollIntoViewOnBoost = false;

Alpine.start();

/**
 * CSP-clean replacements for inline event handlers.
 *
 * Templates declare intent via data attributes; the listeners below are bound
 * once at the document level and survive htmx swaps. Idempotency is enforced
 * with a Symbol flag on `document` so repeated initialization is a no-op.
 */
const YP_BOUND = Symbol.for("yp-admin.delegated-handlers");
type Bound = { [k: symbol]: boolean } & Document;

function bindDelegatedHandlers(): void {
  const doc = document as Bound;
  if (doc[YP_BOUND]) return;
  doc[YP_BOUND] = true;

  // [data-yp-auto-submit] selects/inputs: fall back to native form submit when
  // htmx is unavailable. With htmx present the hx-* attributes already drive
  // the change, so this is a progressive-enhancement no-op.
  document.addEventListener("change", (event) => {
    const target = event.target as HTMLElement | null;
    if (!target) return;
    if (!(target instanceof HTMLSelectElement || target instanceof HTMLInputElement)) return;
    if (!target.hasAttribute("data-yp-auto-submit")) return;
    if (window.htmx) return;
    target.form?.submit();
  });

  // [data-yp-confirm] buttons/links: window.confirm() before activating.
  document.addEventListener(
    "click",
    (event) => {
      const target = event.target as HTMLElement | null;
      const trigger = target?.closest<HTMLElement>("[data-yp-confirm]");
      if (!trigger) return;
      const message = trigger.getAttribute("data-yp-confirm") ?? "";
      if (!window.confirm(message)) {
        event.preventDefault();
        event.stopPropagation();
      }
    },
    true,
  );
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bindDelegatedHandlers, { once: true });
} else {
  bindDelegatedHandlers();
}

// htmx swaps replace fragments but the document-level listeners persist; we
// still call this defensively so a future refactor that moves bindings into
// the swapped subtree keeps working.
document.body.addEventListener("htmx:afterSwap", bindDelegatedHandlers);
