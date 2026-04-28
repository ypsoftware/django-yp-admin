/**
 * HTML5 Drag&Drop reorder for inlines. Replaces django-admin-sortable2 + jQuery UI.
 * On drop, sends new order via fetch POST.
 */

import { getCsrfToken } from "./csrf";

const INIT_FLAG = "__ypSortableInit";

interface SortableContainer extends HTMLElement {
  [INIT_FLAG]?: boolean;
}

interface SortableRow extends HTMLElement {
  draggable: boolean;
}

function rowSelector(container: HTMLElement): string {
  return container.querySelector("[data-yp-sortable-row]")
    ? "[data-yp-sortable-row]"
    : "tr";
}

function getRows(container: HTMLElement): SortableRow[] {
  return Array.from(
    container.querySelectorAll<SortableRow>(rowSelector(container)),
  ).filter((row) => row.parentElement === container || container.contains(row));
}

function computeReorderUrl(container: HTMLElement): string {
  const explicit = container.dataset.ypSortableUrl;
  if (explicit) return explicit;
  const host = container.closest<HTMLElement>("[data-yp-reorder-url]");
  return host?.dataset.ypReorderUrl ?? "";
}

function clearDropMarkers(container: HTMLElement): void {
  container.querySelectorAll(".yp-drop-before, .yp-drop-after").forEach((el) => {
    el.classList.remove("yp-drop-before", "yp-drop-after");
  });
}

function showError(message: string): void {
  document.dispatchEvent(
    new CustomEvent("yp:error", { detail: { message } }),
  );
}

async function postReorder(
  url: string,
  pk: string,
  newOrder: number,
): Promise<boolean> {
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCsrfToken(),
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ pk, new_order: newOrder }),
      credentials: "same-origin",
    });
    if (!response.ok) {
      showError(`Reorder failed: ${response.status}`);
      return false;
    }
    return true;
  } catch (err) {
    showError(`Reorder failed: ${(err as Error).message}`);
    return false;
  }
}

function attachContainer(container: SortableContainer): void {
  if (container[INIT_FLAG]) return;
  container[INIT_FLAG] = true;

  let dragging: SortableRow | null = null;
  let originalNext: Element | null = null;

  const onDragStart = (event: DragEvent) => {
    const row = (event.target as Element)?.closest<SortableRow>(
      rowSelector(container),
    );
    if (!row || !container.contains(row)) return;
    dragging = row;
    originalNext = row.nextElementSibling;
    row.classList.add("yp-dragging");
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", row.dataset.pk ?? "");
    }
  };

  const onDragOver = (event: DragEvent) => {
    if (!dragging) return;
    const row = (event.target as Element)?.closest<SortableRow>(
      rowSelector(container),
    );
    if (!row || row === dragging || !container.contains(row)) return;
    event.preventDefault();
    if (event.dataTransfer) event.dataTransfer.dropEffect = "move";
    const rect = row.getBoundingClientRect();
    const before = event.clientY < rect.top + rect.height / 2;
    clearDropMarkers(container);
    row.classList.add(before ? "yp-drop-before" : "yp-drop-after");
  };

  const onDrop = async (event: DragEvent) => {
    if (!dragging) return;
    const row = (event.target as Element)?.closest<SortableRow>(
      rowSelector(container),
    );
    if (!row || row === dragging) {
      clearDropMarkers(container);
      return;
    }
    event.preventDefault();
    const rect = row.getBoundingClientRect();
    const before = event.clientY < rect.top + rect.height / 2;
    const parent = row.parentElement;
    if (!parent) return;
    if (before) {
      parent.insertBefore(dragging, row);
    } else {
      parent.insertBefore(dragging, row.nextElementSibling);
    }
    clearDropMarkers(container);

    const moved = dragging;
    const pk = moved.dataset.pk ?? "";
    const rows = getRows(container);
    const newOrder = rows.indexOf(moved);
    const url = computeReorderUrl(container);
    const ok = pk ? await postReorder(url, pk, newOrder) : false;
    if (!ok && parent) {
      // Revert: re-insert at original position.
      if (originalNext && originalNext.parentElement === parent) {
        parent.insertBefore(moved, originalNext);
      } else {
        parent.appendChild(moved);
      }
    }
  };

  const onDragEnd = () => {
    if (dragging) dragging.classList.remove("yp-dragging");
    clearDropMarkers(container);
    dragging = null;
    originalNext = null;
  };

  for (const row of getRows(container)) {
    row.draggable = true;
  }

  container.addEventListener("dragstart", onDragStart);
  container.addEventListener("dragover", onDragOver);
  container.addEventListener("drop", onDrop);
  container.addEventListener("dragend", onDragEnd);
}

export function initSortable(root: ParentNode = document): void {
  const containers = root.querySelectorAll<SortableContainer>("[data-yp-sortable]");
  containers.forEach(attachContainer);
}

function findHandleRow(handle: HTMLElement): HTMLElement | null {
  // Prefer an explicit sortable row marker, fall back to the closest <tr>.
  return (
    handle.closest<HTMLElement>("[data-yp-sortable-row]") ??
    handle.closest<HTMLElement>("tr")
  );
}

function findHandleContainer(handle: HTMLElement, row: HTMLElement | null): HTMLElement {
  const explicit = handle.closest<HTMLElement>("[data-yp-sortable]");
  if (explicit) return explicit;
  // Fallback: the row's parent (e.g. <tbody>) acts as the container.
  return (row?.parentElement as HTMLElement | null) ?? document.body;
}

async function keyboardReorder(handle: HTMLElement, delta: number): Promise<void> {
  const row = findHandleRow(handle);
  if (!row) return;
  const container = findHandleContainer(handle, row);
  const siblings = Array.from(
    (row.parentElement?.children ?? []) as HTMLCollectionOf<HTMLElement>,
  ).filter((el) => el.tagName === row.tagName);
  const currentIndex = siblings.indexOf(row);
  if (currentIndex < 0) return;
  const newIndex = currentIndex + delta;
  if (newIndex < 0 || newIndex >= siblings.length) return;

  const parent = row.parentElement;
  if (!parent) return;
  const target = siblings[newIndex];
  if (delta < 0) {
    parent.insertBefore(row, target);
  } else {
    parent.insertBefore(row, target.nextElementSibling);
  }

  const pk = handle.dataset.pk ?? row.dataset.pk ?? "";
  const url = computeReorderUrl(container);
  if (pk && url) {
    await postReorder(url, pk, newIndex);
  }
  // Re-focus the handle (DOM move keeps the element, but ensure focus).
  handle.focus();
}

function onHandleKeydown(event: KeyboardEvent): void {
  const handle = (event.target as Element | null)?.closest<HTMLElement>(
    "[data-yp-drag-handle]",
  );
  if (!handle) return;
  if (event.key === "ArrowUp") {
    event.preventDefault();
    void keyboardReorder(handle, -1);
  } else if (event.key === "ArrowDown") {
    event.preventDefault();
    void keyboardReorder(handle, 1);
  }
}

function register(): void {
  initSortable();
  document.addEventListener("keydown", onHandleKeydown);
  document.addEventListener("htmx:afterSettle", (e) => {
    const target = (e as CustomEvent).detail?.elt as ParentNode | undefined;
    initSortable(target ?? document);
    // Also ensure newly added rows inside an already-initialised container get draggable=true.
    document
      .querySelectorAll<HTMLElement>("[data-yp-sortable]")
      .forEach((c) => {
        getRows(c).forEach((row) => {
          row.draggable = true;
        });
      });
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", register);
} else {
  register();
}
