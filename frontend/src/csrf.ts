/**
 * CSRF cookie reader. Django stores the token in a `csrftoken` cookie by default.
 *
 * Throws when the cookie is absent so silent 403s don't masquerade as success.
 * Only call from state-changing requests (POST/PUT/PATCH/DELETE).
 */

export function getCsrfToken(name = "csrftoken"): string {
  const prefix = `${name}=`;
  const parts = document.cookie ? document.cookie.split("; ") : [];
  for (const part of parts) {
    if (part.startsWith(prefix)) {
      return decodeURIComponent(part.slice(prefix.length));
    }
  }
  throw new Error(
    "Missing CSRF cookie. Ensure CsrfViewMiddleware is enabled and the page was loaded from Django.",
  );
}
