/**
 * Compat shim for related-object popup protocol.
 *
 * Legacy admin addons call window.opener.dismissAddRelatedObjectPopup(...).
 * We expose the global function but route the event into htmx instead of opening
 * a real new window — the popup runs inside <dialog> in the same document.
 */

declare global {
  interface Window {
    dismissAddRelatedObjectPopup?: (win: Window, newId: string, newRepr: string) => void;
    dismissChangeRelatedObjectPopup?: (win: Window, newId: string, newRepr: string) => void;
    dismissDeleteRelatedObjectPopup?: (win: Window, objId: string) => void;
  }
}

window.dismissAddRelatedObjectPopup = (_win, newId, newRepr) => {
  document.dispatchEvent(
    new CustomEvent("yp:related-object-added", { detail: { newId, newRepr } }),
  );
};

window.dismissChangeRelatedObjectPopup = (_win, newId, newRepr) => {
  document.dispatchEvent(
    new CustomEvent("yp:related-object-changed", { detail: { newId, newRepr } }),
  );
};

window.dismissDeleteRelatedObjectPopup = (_win, objId) => {
  document.dispatchEvent(
    new CustomEvent("yp:related-object-deleted", { detail: { objId } }),
  );
};

export {};
