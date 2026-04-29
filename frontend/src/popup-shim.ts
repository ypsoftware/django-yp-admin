/**
 * Compat shim for related-object popup protocol.
 *
 * Legacy admin addons call window.opener.dismissAddRelatedObjectPopup(...).
 * We expose the global function but route the event into htmx instead of opening
 * a real new window — the popup runs inside <dialog> in the same document.
 *
 * If another library already defined these globals, we chain the original.
 */

declare global {
  interface Window {
    dismissAddRelatedObjectPopup?: (win: Window, newId: string, newRepr: string) => void;
    dismissChangeRelatedObjectPopup?: (win: Window, newId: string, newRepr: string) => void;
    dismissDeleteRelatedObjectPopup?: (win: Window, objId: string) => void;
  }
}

const origAdd = window.dismissAddRelatedObjectPopup;
const origChange = window.dismissChangeRelatedObjectPopup;
const origDelete = window.dismissDeleteRelatedObjectPopup;

window.dismissAddRelatedObjectPopup = (win, newId, newRepr) => {
  document.dispatchEvent(
    new CustomEvent("yp:related-object-added", { detail: { newId, newRepr } }),
  );
  origAdd?.(win, newId, newRepr);
};

window.dismissChangeRelatedObjectPopup = (win, newId, newRepr) => {
  document.dispatchEvent(
    new CustomEvent("yp:related-object-changed", { detail: { newId, newRepr } }),
  );
  origChange?.(win, newId, newRepr);
};

window.dismissDeleteRelatedObjectPopup = (win, objId) => {
  document.dispatchEvent(
    new CustomEvent("yp:related-object-deleted", { detail: { objId } }),
  );
  origDelete?.(win, objId);
};

export {};
