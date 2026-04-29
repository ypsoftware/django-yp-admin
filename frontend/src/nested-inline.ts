/**
 * htmx-native nested inlines. Replaces django-nested-admin.
 * Add/remove rows via hx-get / hx-delete returning fragments.
 */

import htmx from "htmx.org";
import { onReady } from "./utils";

const LAZY_FLAG = "__ypNestedLazyBound";

interface LazyDetails extends HTMLDetailsElement {
  [LAZY_FLAG]?: boolean;
}

export function updateTotalForms(formsetPrefix: string, delta: number): number {
  const input = document.querySelector<HTMLInputElement>(
    `input[name="${formsetPrefix}-TOTAL_FORMS"]`,
  );
  if (!input) return 0;
  const current = parseInt(input.value, 10) || 0;
  const next = Math.max(0, current + delta);
  input.value = String(next);
  return next;
}

function bindLazy(root: ParentNode = document): void {
  root
    .querySelectorAll<LazyDetails>("details[data-yp-nested-lazy]")
    .forEach((details) => {
      if (details[LAZY_FLAG]) return;
      details[LAZY_FLAG] = true;
      details.addEventListener("toggle", () => {
        if (!details.open) return;
        if (details.dataset.ypNestedLoaded === "true") return;
        details.dataset.ypNestedLoaded = "true";
        htmx.trigger(details, "load", {});
      });
    });
}

function onRemoveClick(event: Event): void {
  const button = (event.target as Element)?.closest<HTMLElement>(
    "[data-yp-remove-row]",
  );
  if (!button) return;
  const row = button.closest<HTMLElement>("[data-yp-row]") ?? button.closest("tr");
  if (!row) return;

  // If the row has a saved pk, let htmx handle hx-delete (declarative).
  if (button.hasAttribute("hx-delete") || button.hasAttribute("data-hx-delete")) {
    return;
  }
  const pk = (row as HTMLElement).dataset?.pk;
  if (pk) {
    // hx-delete declarative path expected; if not present, do nothing here.
    return;
  }

  event.preventDefault();
  const prefix = button.dataset.ypFormsetPrefix ?? button.dataset.ypPrefix;
  row.remove();
  if (prefix) {
    updateTotalForms(prefix, -1);
  }
}

function onAddedToDom(event: Event): void {
  // After htmx swaps in a new row from [data-yp-add-row], bump TOTAL_FORMS.
  const detail = (event as CustomEvent).detail as
    | { elt?: HTMLElement; requestConfig?: { elt?: HTMLElement } }
    | undefined;
  const trigger = detail?.requestConfig?.elt ?? detail?.elt;
  if (!(trigger instanceof HTMLElement)) return;
  if (!trigger.matches("[data-yp-add-row]")) return;
  const prefix =
    trigger.dataset.ypFormsetPrefix ?? trigger.dataset.ypPrefix;
  if (prefix) {
    updateTotalForms(prefix, 1);
  }
}

function register(): void {
  bindLazy();
  document.addEventListener("click", onRemoveClick);
  document.addEventListener("htmx:afterSettle", (e) => {
    const target = (e as CustomEvent).detail?.elt as ParentNode | undefined;
    bindLazy(target ?? document);
  });
  document.addEventListener("htmx:afterOnLoad", onAddedToDom);
}

onReady(register);
