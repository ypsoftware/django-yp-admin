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
import { onReady } from "./utils";

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

onReady(bindDelegatedHandlers);

/**
 * Generic enhancer: adds htmx attributes to matching elements and calls
 * htmx.process(). Idempotent — skips elements that already have the first
 * attribute.
 */
function enhance(
  selector: string,
  attrs: Record<string, string>,
  processTarget = true,
): (root?: ParentNode) => void {
  const firstAttr = Object.keys(attrs)[0];
  return (root: ParentNode = document) => {
    root.querySelectorAll<HTMLElement>(selector).forEach((el) => {
      if (el.hasAttribute(firstAttr)) return;
      Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
      if (processTarget) window.htmx.process(el);
    });
  };
}

/**
 * Register an enhancer to run on DOM ready and after every htmx swap.
 */
function registerEnhancer(fn: (root?: ParentNode) => void): void {
  onReady(() => fn());
  document.body.addEventListener("htmx:afterSwap", () => fn());
}

// ============================================================
// Enhancers
// ============================================================

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
registerEnhancer(bindInlineSave);

/**
 * Wire Django admin change/add forms with htmx so save round-trips swap only
 * #content instead of full page reloads.
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
registerEnhancer(bindModelFormHtmx);

/**
 * Enhance the changelist search form with htmx attributes.
 */
const bindSearchFormHtmx = enhance("form#changelist-search", {
  "hx-target": "#changelist-form",
  "hx-select": "#changelist-form",
  "hx-swap": "outerHTML show:window:top",
  "hx-push-url": "true",
  "hx-trigger": "submit changed delay:300ms, search",
});
registerEnhancer((root = document) => {
  const form = root.querySelector<HTMLFormElement>("form#changelist-search");
  if (!form || form.hasAttribute("hx-get")) return;
  form.setAttribute("hx-get", form.getAttribute("action") || window.location.href);
  bindSearchFormHtmx(root);
});

/**
 * Enhance changelist column header sort links with htmx.
 */
const bindColumnSortHtmx = enhance("th a[href*='o=']", {
  "hx-target": "#changelist-form",
  "hx-select": "#changelist-form",
  "hx-swap": "outerHTML show:window:top",
  "hx-push-url": "true",
});
registerEnhancer((root = document) => {
  const container = root.querySelector("#changelist-form");
  if (!container) return;
  const links = container.querySelectorAll<HTMLAnchorElement>("th a[href*='o=']");
  links.forEach((link) => {
    if (link.hasAttribute("hx-get")) return;
    link.setAttribute("hx-get", link.getAttribute("href") || "");
  });
  bindColumnSortHtmx(container);
});

/**
 * After an htmx swap on the change form, scroll to the first validation
 * error and focus the first invalid field.
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
      if (headerIndex >= headers.length) return;
      const headerText = headers[headerIndex].textContent?.trim() || "";
      if (headerText) {
        cell.setAttribute("data-label", headerText);
      }
      headerIndex++;
    });
  });
}
registerEnhancer(bindCardLabels);
