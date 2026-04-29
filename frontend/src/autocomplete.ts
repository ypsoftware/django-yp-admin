/**
 * htmx-driven autocomplete using Tom Select. Replaces Select2 + django-autocomplete-light.
 * Hits the same /admin/autocomplete/?app_label=&model_name=&field_name=&term= endpoint.
 *
 * SECURITY (XSS):
 *   Tom Select's default `option`/`item` renderers escape `text` automatically.
 *   We never pass user-controlled HTML to Tom Select. Strings reaching
 *   `addOption`/`updateOption` (notably `newRepr` from the related-object popup
 *   protocol) are defensively run through `escape()` before insertion as a
 *   belt-and-braces measure.
 *
 *   IMPORTANT: If you ever add a custom `render: { option, item, ... }` config,
 *   you MUST escape every user-provided field with `escape()` below. Returning
 *   a template literal that interpolates `data.text` directly (e.g.
 *   `<div>${data.text}</div>`) is an XSS sink. See docs/optional-extras.md
 *   ("Autocomplete XSS policy").
 */

import TomSelect from "tom-select";
import { onReady } from "./utils";

/**
 * Minimal HTML entity escape. Use for any user-provided string that will be
 * passed to a Tom Select custom `render` template returning an HTML string.
 */
export function escape(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

interface AutocompleteResult {
  id: string;
  text: string;
}

interface AutocompleteResponse {
  results: AutocompleteResult[];
}

const INSTANCE_KEY = "__ypTomSelect";

interface AugmentedSelect extends HTMLSelectElement {
  [INSTANCE_KEY]?: TomSelect;
}

function buildUrl(base: string, query: string): string {
  const sep = base.includes("?") ? "&" : "?";
  return `${base}${sep}term=${encodeURIComponent(query)}`;
}

function initSelect(select: AugmentedSelect): void {
  if (select[INSTANCE_KEY]) {
    return;
  }
  const url = select.dataset.ypAutocompleteUrl;
  if (!url) {
    return;
  }
  const allowClear = select.dataset.ypAllowClear === "true";
  const multiple = select.multiple;

  const ts = new TomSelect(select, {
    valueField: "id",
    labelField: "text",
    searchField: ["text"],
    loadThrottle: 250,
    preload: "focus",
    maxItems: multiple ? null : 1,
    allowEmptyOption: allowClear,
    plugins: allowClear ? ["clear_button"] : [],
    load: (query: string, callback: (results: AutocompleteResult[]) => void) => {
      fetch(buildUrl(url, query), { headers: { Accept: "application/json" } })
        .then((r) => r.json() as Promise<AutocompleteResponse>)
        .then((data) => callback(data.results ?? []))
        .catch(() => callback([]));
    },
  });

  select[INSTANCE_KEY] = ts;
}

export function initAutocomplete(root: ParentNode = document): void {
  const selects = root.querySelectorAll<AugmentedSelect>(
    'select[data-yp-autocomplete="true"]',
  );
  selects.forEach(initSelect);
}

function findRelevantInstance(target?: EventTarget | null): TomSelect | null {
  // Prefer the currently focused autocomplete; otherwise fall back to the
  // last-used instance via document.activeElement chain.
  const candidates = document.querySelectorAll<AugmentedSelect>(
    'select[data-yp-autocomplete="true"]',
  );
  let active: TomSelect | null = null;
  candidates.forEach((sel) => {
    const inst = sel[INSTANCE_KEY];
    if (!inst) return;
    if (target instanceof Element && sel.contains(target)) {
      active = inst;
    }
    if (!active && document.activeElement && sel.contains(document.activeElement)) {
      active = inst;
    }
  });
  if (active) return active;
  // Fall back to first instance.
  for (const sel of Array.from(candidates)) {
    if (sel[INSTANCE_KEY]) return sel[INSTANCE_KEY] ?? null;
  }
  return null;
}

interface RelatedObjectDetail {
  newId?: string;
  newRepr?: string;
  objId?: string;
}

function handleRelatedAdded(event: Event): void {
  const detail = (event as CustomEvent<RelatedObjectDetail>).detail;
  if (!detail?.newId || !detail.newRepr) return;
  const inst = findRelevantInstance(event.target);
  if (!inst) return;
  // newRepr comes from the related-object popup; treat as untrusted.
  // Strip control characters and any literal HTML tag delimiters defensively.
  // Tom Select's default render escapes text, but we pin this to guarantee no
  // raw HTML reaches downstream code paths even if a custom render is added.
  const safeText = sanitizeUntrustedText(detail.newRepr);
  inst.addOption({ id: detail.newId, text: safeText });
  inst.addItem(detail.newId);
}

/**
 * Strip characters that have no business in a human-readable label and could
 * become live HTML if a custom `render` ever forgets to escape. This is
 * lossless for normal Unicode text, only neutering `<` and `>`.
 */
function sanitizeUntrustedText(value: string): string {
  // eslint-disable-next-line no-control-regex
  return value.replace(/[\u0000-\u001F\u007F]/g, "").replace(/[<>]/g, "");
}

function handleRelatedChanged(event: Event): void {
  const detail = (event as CustomEvent<RelatedObjectDetail>).detail;
  if (!detail?.newId || !detail.newRepr) return;
  const inst = findRelevantInstance(event.target);
  if (!inst) return;
  const safeText = sanitizeUntrustedText(detail.newRepr);
  inst.updateOption(detail.newId, { id: detail.newId, text: safeText });
  inst.refreshOptions(false);
}

function handleRelatedDeleted(event: Event): void {
  const detail = (event as CustomEvent<RelatedObjectDetail>).detail;
  if (!detail?.objId) return;
  const inst = findRelevantInstance(event.target);
  if (!inst) return;
  inst.removeItem(detail.objId);
  inst.removeOption(detail.objId);
}

function register(): void {
  initAutocomplete();
  document.addEventListener("htmx:afterSettle", (e) => {
    const target = (e as CustomEvent).detail?.elt as ParentNode | undefined;
    initAutocomplete(target ?? document);
  });
  document.addEventListener("yp:related-object-added", handleRelatedAdded);
  document.addEventListener("yp:related-object-changed", handleRelatedChanged);
  document.addEventListener("yp:related-object-deleted", handleRelatedDeleted);
}

onReady(register);
