/**
 * Knowledge Zakat — Application stores.
 *
 * Refactor from the previous JS version:
 *  - Strict TypeScript types from lib/types.ts everywhere.
 *  - `token` and `user` are now hydrated from localStorage at module
 *    load and *automatically* persisted on every change. Pages no
 *    longer have to remember to call `localStorage.setItem(...)` after
 *    setting the store. The previous code had this duplicated in
 *    Login.svelte, Register.svelte and Profile.svelte, which is how
 *    bugs like "logout doesn't actually clear the user" got in.
 *  - Removed `currentPage`, `selectedSessionId`, `selectedTeacherId`.
 *    Routing state now lives in lib/router.ts (the URL itself is the
 *    source of truth). Page payloads are passed via the URL param.
 *  - Added `logout()` helper so every entry point clears the same set
 *    of keys instead of each component having to remember the list.
 */

import { writable, type Writable } from 'svelte/store';
import type { User } from './types';

// ---------------------------------------------------------------------------
// localStorage key names — kept in one place to avoid typo-bugs.
// ---------------------------------------------------------------------------
const LS = {
  TOKEN: 'kz.token',
  USER: 'kz.user',
  THEME: 'kz.theme',
} as const;

// ---------------------------------------------------------------------------
// Safe JSON read for hydration.
// ---------------------------------------------------------------------------
// localStorage can hold corrupt JSON (manual edit, half-written value
// from an interrupted previous session, etc.). A single broken value
// must NOT crash the entire app on boot — we'd never see the login
// screen to recover. So we wrap reads in a try/catch and fall back to
// null.
function readJSON<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(key);
    if (raw == null) return null;
    return JSON.parse(raw) as T;
  } catch {
    // Corrupt entry — purge it so we don't repeat the failure on
    // every reload.
    localStorage.removeItem(key);
    return null;
  }
}

// ---------------------------------------------------------------------------
// Auth stores
// ---------------------------------------------------------------------------

/** JWT bearer token. `null` means logged out. */
export const token: Writable<string | null> = writable<string | null>(
  localStorage.getItem(LS.TOKEN)
);

/** Currently authenticated user, or `null` if logged out. */
export const user: Writable<User | null> = writable<User | null>(
  readJSON<User>(LS.USER)
);

// Auto-persist: every time someone calls `token.set(...)` or
// `user.set(...)`, mirror the change to localStorage. Subscribers
// returned by `.subscribe(...)` here intentionally never unsubscribe —
// the stores live as long as the app does.
token.subscribe((v) => {
  if (v == null) {
    localStorage.removeItem(LS.TOKEN);
  } else {
    localStorage.setItem(LS.TOKEN, v);
  }
});

user.subscribe((v) => {
  if (v == null) {
    localStorage.removeItem(LS.USER);
  } else {
    localStorage.setItem(LS.USER, JSON.stringify(v));
  }
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Centralised logout. Use this from EVERY logout entry point
 * (sidebar button, 401 interceptor, "delete account" flow). Keeps
 * the cleanup list in one place.
 *
 * NOTE: navigation away from the page is the caller's responsibility —
 * we don't import `navigate` here to avoid a circular dependency
 * between stores.ts and router.ts.
 */
export function logout(): void {
  token.set(null);
  user.set(null);
  // Defensive sweep in case some legacy code wrote under the old key
  // names. Cheap, and makes hot-reload during development reliable.
  localStorage.removeItem('token');
  localStorage.removeItem('user');
}

/**
 * Role helpers. Used by App.svelte to pick a layout, and by sidebars
 * to show/hide menu items. Returning `false` for a null user lets the
 * caller short-circuit safely without nullable checks at every site.
 */
export function hasRole(u: User | null, name: 'admin' | 'teacher' | 'student'): boolean {
  if (!u || !Array.isArray(u.roles)) return false;
  return u.roles.some((r) => r.role_name === name);
}
