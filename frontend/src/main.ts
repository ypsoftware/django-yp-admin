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

/**
 * Sync <body class> + <title> when an htmx swap replaces #content.
 *
 * Forms POST with hx-target="#content" hx-select="#content". Django returns
 * either the same form (errors) or a redirected page (success). The chrome
 * (header, breadcrumbs, body class, title) lives outside #content, so we
 * mirror body class + title from the response so view-scoped CSS selectors
 * keep working and the tab title reflects the current page.
 */
document.body.addEventListener("htmx:beforeSwap", (evt: Event) => {
  const e = evt as CustomEvent<{ xhr: XMLHttpRequest; serverResponse: string; target: HTMLElement }>;
  const target = e.detail?.target;
  if (!target || target.id !== "content") return;
  const xhr = e.detail.xhr;
  const ct = xhr.getResponseHeader("Content-Type") || "";
  if (!ct.includes("text/html")) return;
  const html = e.detail.serverResponse;
  if (!html || html.indexOf("<body") === -1) return;
  try {
    const doc = new DOMParser().parseFromString(html, "text/html");
    if (doc.body && doc.body.className !== undefined) {
      document.body.className = doc.body.className;
    }
    if (doc.title) document.title = doc.title;
  } catch { /* noop */ }
});

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

/**
 * [data-yp-inline-save] — converts the enclosing <form> into an htmx-driven
 * inline-save form. Replaces the old inline <script> approach so we stay
 * CSP-clean (no inline script execution).
 */
function bindInlineSave(root: ParentNode = document): void {
  root.querySelectorAll<HTMLElement>("[data-yp-inline-save]").forEach((el) => {
    const form = el.closest("form");
    if (!form || form.hasAttribute("hx-post")) return;
    const url = el.dataset.ypInlineSaveUrl || window.location.pathname;
    form.setAttribute("hx-post", url);
    form.setAttribute("hx-target", "this");
    form.setAttribute("hx-swap", "outerHTML");
    window.htmx.process(form);
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    bindInlineSave();
  }, { once: true });
} else {
  bindInlineSave();
}

document.body.addEventListener("htmx:afterSwap", () => {
  bindInlineSave();
});

/**
 * Wire Django admin change/add forms with htmx so save round-trips swap only
 * #content instead of full page reloads. Errors render inline; valid saves
 * follow Django's redirect (htmx fetches the redirect target and selects
 * #content from it). Chrome stays put.
 *
 * We target `form[id$="_form"]` inside #content-main — Django's convention
 * for the model form (e.g. `user_form`). Skipped when the form already has
 * hx-post (inline-save shim or popup forms).
 */
function bindModelFormHtmx(root: ParentNode = document): void {
  const main = root.querySelector("#content-main");
  if (!main) return;
  const form = main.querySelector<HTMLFormElement>('form[id$="_form"]');
  if (!form || form.hasAttribute("hx-post")) return;
  if (form.closest("[data-yp-inline-save]")) return;
  form.setAttribute("hx-post", form.getAttribute("action") || window.location.pathname);
  form.setAttribute("hx-target", "#content");
  form.setAttribute("hx-select", "#content");
  form.setAttribute("hx-swap", "outerHTML show:window:top");
  form.setAttribute("hx-push-url", "true");
  window.htmx.process(form);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => bindModelFormHtmx(), { once: true });
} else {
  bindModelFormHtmx();
}
document.body.addEventListener("htmx:afterSwap", () => bindModelFormHtmx());

/**
 * Enhance the changelist search form with htmx attributes so search
 * submissions swap only #changelist-form instead of full page reloads.
 *
 * Django's stock {% search_form cl %} renders a plain <form id="changelist-search">
 * with method="get". We add hx-get/hx-target/hx-select/hx-swap/hx-push-url
 * so it behaves like the rest of the changelist.
 */
function bindSearchFormHtmx(root: ParentNode = document): void {
  const form = root.querySelector<HTMLFormElement>("form#changelist-search");
  if (!form || form.hasAttribute("hx-get")) return;
  form.setAttribute("hx-get", form.getAttribute("action") || window.location.href);
  form.setAttribute("hx-target", "#changelist-form");
  form.setAttribute("hx-select", "#changelist-form");
  form.setAttribute("hx-swap", "outerHTML show:window:top");
  form.setAttribute("hx-push-url", "true");
  // Debounce search to avoid excessive requests while typing
  form.setAttribute("hx-trigger", "submit changed delay:300ms, search");
  window.htmx.process(form);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => bindSearchFormHtmx(), { once: true });
} else {
  bindSearchFormHtmx();
}
document.body.addEventListener("htmx:afterSwap", () => bindSearchFormHtmx());

/**
 * Enhance changelist column header sort links with htmx so sorting
 * swaps only #changelist-form instead of full page reloads.
 *
 * Django renders sort links as plain <a> tags inside <th class="sorted">
 * headers. We add hx-get/hx-target/hx-select/hx-swap/hx-push-url to each.
 */
function bindColumnSortHtmx(root: ParentNode = document): void {
  const container = root.querySelector("#changelist-form");
  if (!container) return;
  const links = container.querySelectorAll<HTMLAnchorElement>("th a[href*='o=']");
  links.forEach((link) => {
    if (link.hasAttribute("hx-get")) return;
    link.setAttribute("hx-get", link.getAttribute("href") || "");
    link.setAttribute("hx-target", "#changelist-form");
    link.setAttribute("hx-select", "#changelist-form");
    link.setAttribute("hx-swap", "outerHTML show:window:top");
    link.setAttribute("hx-push-url", "true");
    window.htmx.process(link);
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => bindColumnSortHtmx(), { once: true });
} else {
  bindColumnSortHtmx();
}
document.body.addEventListener("htmx:afterSwap", () => bindColumnSortHtmx());

/**
 * After an htmx swap on the change form, scroll to the first validation
 * error and focus the first invalid field. This mirrors Django admin's
 * stock behavior where the page scrolls to the errornote on validation
 * failure.
 */
function scrollToFirstError(root: ParentNode = document): void {
  const errornote = root.querySelector(".errornote");
  if (errornote) {
    errornote.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  const firstError = root.querySelector<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>(
    ".errors input:not([type=hidden]), .errors textarea, .errors select, input:invalid, textarea:invalid, select:invalid",
  );
  if (firstError) {
    firstError.focus();
  }
}

document.body.addEventListener("htmx:afterSwap", (evt: Event) => {
  const target = (evt as CustomEvent).detail?.target;
  if (target && target.id === "content") {
    scrollToFirstError(target);
  }
});

/**
 * Inject `data-label` attributes on changelist <td> cells so CSS can
 * display floating labels in card view on small screens.
 *
 * Reads header text from each <th> in the <thead> and copies it as
 * `data-label` on the corresponding <td> in every <tbody> row.
 * Idempotent — skips cells that already have the attribute.
 */
function bindCardLabels(root: ParentNode = document): void {
  const table = root.querySelector<HTMLTableElement>("#result_list");
  if (!table) return;
  const headers = table.querySelectorAll<HTMLTableCellElement>("thead th");
  if (!headers.length) return;
  const rows = table.querySelectorAll<HTMLTableRowElement>("tbody tr");
  rows.forEach((row) => {
    const cells = row.querySelectorAll<HTMLTableCellElement>("td, th");
    let headerIndex = 0;
    cells.forEach((cell) => {
      if (cell.hasAttribute("data-label")) return;
      // Skip cells whose column index is out of range (e.g. extra action cols)
      if (headerIndex >= headers.length) return;
      // Extract clean header text (ignores sort arrows, links, etc.)
      const headerText = headers[headerIndex].textContent?.trim() || "";
      if (headerText) {
        cell.setAttribute("data-label", headerText);
      }
      headerIndex++;
    });
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => bindCardLabels(), { once: true });
} else {
  bindCardLabels();
}
document.body.addEventListener("htmx:afterSwap", () => bindCardLabels());
