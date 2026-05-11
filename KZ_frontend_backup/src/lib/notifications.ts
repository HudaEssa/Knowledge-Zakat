/**
 * Knowledge Zakat — Notification system (data layer).
 *
 * Replaces the scattered mix of `alert(...)`, `console.error(...)`,
 * inline `errorMessage` strings and per-component modals. Pages call:
 *
 *     notify.success('تم حفظ التعديلات');
 *     notify.error('تعذّر الاتصال بالخادم');
 *
 * The actual rendering happens in `components/Notification.svelte`,
 * which subscribes to this store. Splitting data and view this way
 * means tests can assert on calls to `notify.*` without mounting any
 * DOM, and the visual style can be redesigned without touching pages.
 */

import { writable, type Writable } from 'svelte/store';
import type { AppNotification, NotificationKind } from './types';

// ---------------------------------------------------------------------------
// Internal store — list of currently visible notifications.
// ---------------------------------------------------------------------------
// We store a list (not a single value) so multiple notifications can
// stack (e.g. a 401 error from a background poll while the user is
// still reading a previous success message).
export const notifications: Writable<AppNotification[]> = writable<AppNotification[]>([]);

// Monotonic id counter so each toast gets a unique key for Svelte's
// {#each} block. Date.now() collides on fast successive calls.
let _idCounter = 0;
function nextId(): number {
  _idCounter += 1;
  return _idCounter;
}

// Default auto-dismiss timing. Errors stay longer so users have time
// to read them; successes get out of the way quickly.
const DEFAULT_DURATION: Record<NotificationKind, number> = {
  success: 3500,
  info: 4000,
  warning: 5000,
  error: 6000,
};

/**
 * Push a notification onto the queue. Schedules its own dismissal
 * via setTimeout if `duration > 0`.
 */
function push(kind: NotificationKind, message: string, duration?: number): number {
  const id = nextId();
  const dur = duration ?? DEFAULT_DURATION[kind];
  const item: AppNotification = { id, kind, message, duration: dur };

  notifications.update((list) => [...list, item]);

  if (dur > 0) {
    // setTimeout, not setInterval: we want exactly one dismissal.
    // The id check inside dismiss() makes it a no-op if the user
    // already closed it manually.
    setTimeout(() => dismiss(id), dur);
  }
  return id;
}

/** Remove a notification by id. Safe to call on already-dismissed ids. */
export function dismiss(id: number): void {
  notifications.update((list) => list.filter((n) => n.id !== id));
}

/** Drop every active notification. Useful on route changes. */
export function clearAll(): void {
  notifications.set([]);
}

/**
 * Public ergonomic API. Pages should call `notify.success(...)` etc.
 * rather than reaching into the internal `push` function — keeps the
 * call sites short and the kinds enumerable.
 */
export const notify = {
  success: (message: string, duration?: number): number => push('success', message, duration),
  error: (message: string, duration?: number): number => push('error', message, duration),
  info: (message: string, duration?: number): number => push('info', message, duration),
  warning: (message: string, duration?: number): number => push('warning', message, duration),
};
