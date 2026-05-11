/**
 * Knowledge Zakat — Hash-based client-side router.
 *
 * Why a custom router?
 *  - The previous implementation kept the "current page" only in a
 *    Svelte store, with no link to the browser URL. A page reload
 *    therefore reset the user back to Home, regardless of where they
 *    were. That was the refresh bug we set out to fix.
 *  - Hash routing (URLs like `#/my_learning`) keeps the active page in
 *    the URL itself. The browser persists it across reloads, lets the
 *    user open multiple tabs at different pages, and re-enables the
 *    Back/Forward buttons — all for free.
 *  - Hash (rather than History API) was deliberate: it requires no
 *    server-side rewrite rules and works the same on `localhost` and
 *    on a static host. Important for a graduation project that may
 *    not control its hosting layer.
 *
 * Public surface:
 *   route       — Svelte store, current Route object.
 *   navigate()  — change route programmatically.
 *   initRouter()— wire the window event listeners. Call once at startup.
 *
 * URL grammar:
 *     #/<name>            -> { name, param: null }
 *     #/<name>/<param>    -> { name, param: '<param>' }
 *   Anything else falls back to the home/login default depending on
 *   auth state (handled by App.svelte, not here).
 */

import { writable, type Writable } from 'svelte/store';
import type { Route, RouteName } from './types';

// ---------------------------------------------------------------------------
// Whitelist of valid route names
// ---------------------------------------------------------------------------
// We *intentionally* keep this in sync with the RouteName union in
// types.ts. If you add a name there, add it here too — TypeScript will
// otherwise downcast unknown strings to RouteName silently.
const KNOWN_ROUTES: ReadonlySet<RouteName> = new Set<RouteName>([
  'login',
  'register',
  'home',
  'my_learning',
  'student_profile',
  'session_view',
  'session_details',
  'teacher_view',
  'teacher_home',
  'create_session',
  'my_lectures',
  'teacher_requests',
  'profile',
  'update_session',
  'admin_logs',
  'admin_dashboard',
  'admin_panel',
]);

const DEFAULT_ROUTE: Route = { name: 'home', param: null };

// ---------------------------------------------------------------------------
// Hash <-> Route conversion
// ---------------------------------------------------------------------------

/**
 * Read `window.location.hash` and translate it into a Route.
 * Tolerant: any malformed or unknown hash falls back to DEFAULT_ROUTE.
 */
function parseHash(hash: string): Route {
  // Strip a leading "#/" or "#"; we don't want to leak the punctuation
  // into route names.
  const cleaned = hash.replace(/^#\/?/, '').trim();
  if (!cleaned) return { ...DEFAULT_ROUTE };

  const [rawName, ...rest] = cleaned.split('/');
  const name = rawName as RouteName;

  if (!KNOWN_ROUTES.has(name)) {
    return { ...DEFAULT_ROUTE };
  }

  // We only support a single positional param for now. If a future
  // page needs more, switch to query-string parsing here.
  const param = rest.length > 0 ? decodeURIComponent(rest.join('/')) : null;
  return { name, param };
}

/** Inverse of parseHash. */
function routeToHash(route: Route): string {
  if (route.param != null && route.param !== '') {
    return `#/${route.name}/${encodeURIComponent(route.param)}`;
  }
  return `#/${route.name}`;
}

// ---------------------------------------------------------------------------
// The store
// ---------------------------------------------------------------------------

/**
 * The single source of truth for "where am I?". Every page reads from
 * this store; nobody writes to it directly — use `navigate()`.
 */
export const route: Writable<Route> = writable<Route>(parseHash(window.location.hash));

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Change the active route. Updates the URL (which fires `hashchange`,
 * which updates the store), so calling this is enough — no manual
 * `route.set(...)` needed.
 *
 * `replace` chooses between `pushState` and `replaceState` semantics.
 * Use `replace: true` for redirects (e.g. after login) so the user
 * doesn't end up back on the login screen when they hit Back.
 */
export function navigate(name: RouteName, param: string | number | null = null, replace = false): void {
  const next: Route = { name, param: param == null ? null : String(param) };
  const newHash = routeToHash(next);

  if (window.location.hash === newHash) {
    // No-op navigation. The hashchange event won't fire, so push the
    // value into the store explicitly to keep callers honest.
    route.set(next);
    return;
  }

  if (replace) {
    // Rewrite the current history entry rather than appending one.
    const url = `${window.location.pathname}${window.location.search}${newHash}`;
    window.history.replaceState(null, '', url);
    // replaceState doesn't fire hashchange, so update the store ourselves.
    route.set(next);
  } else {
    window.location.hash = newHash;
    // hashchange will fire and the listener below will sync the store.
  }
}

/**
 * Wire window listeners. Idempotent: calling twice is safe (we de-dupe
 * via a module-level flag) but really should only be called from the
 * top-level App.svelte's onMount.
 */
let _listenersAttached = false;

export function initRouter(): void {
  if (_listenersAttached) return;
  _listenersAttached = true;

  // Sync the store every time the user uses Back/Forward, edits the
  // hash manually, or clicks an anchor that mutates location.hash.
  window.addEventListener('hashchange', () => {
    route.set(parseHash(window.location.hash));
  });

  // If the page was opened with a bare URL (no hash), normalise it to
  // `#/home` so the next reload preserves position correctly.
  if (!window.location.hash) {
    const initial = routeToHash(DEFAULT_ROUTE);
    window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}${initial}`);
  }
}
