/**
 * Knowledge Zakat — Axios HTTP client.
 *
 * Centralises three concerns that used to live ad-hoc in each page:
 *
 *  1. Base URL for the FastAPI backend.
 *  2. Attach the JWT bearer token to every outgoing request, pulling
 *     it from the auth store (which is itself hydrated from
 *     localStorage on app boot — see lib/stores.ts).
 *  3. React to 401 responses globally: log the user out, push a
 *     friendly notification, and redirect to /login. Pages no longer
 *     need to know about expired tokens.
 *
 * The previous code re-created an axios config in each page and
 * sometimes forgot the Authorization header on retry, which led to
 * mysterious "logged-in but stuck on login screen" bugs.
 */

import axios, {
  AxiosError,
  type AxiosInstance,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from 'axios';
import { get } from 'svelte/store';

import { token, logout } from './stores';
import { notify } from './notifications';
import { navigate } from './router';

// ---------------------------------------------------------------------------
// Base URL
// ---------------------------------------------------------------------------
// Vite exposes env vars prefixed with VITE_*. Falling back to
// localhost:8000 keeps a fresh `git clone` working with zero setup.
const BASE_URL: string =
  (import.meta as ImportMeta & { env?: Record<string, string> }).env?.VITE_API_URL
  ?? 'http://127.0.0.1:8000';

// ---------------------------------------------------------------------------
// The shared client.
// ---------------------------------------------------------------------------
const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  // 15s is generous enough for slow connections but short enough that
  // a hung backend doesn't leave the user staring at a spinner forever.
  timeout: 15_000,
  headers: { 'Content-Type': 'application/json' },
});

// ---------------------------------------------------------------------------
// Request interceptor — attach the bearer token if we have one.
// ---------------------------------------------------------------------------
// We read the token from the Svelte store rather than from
// localStorage directly. That way `logout()` (which clears the store)
// instantly stops all subsequent requests from sending stale credentials,
// even if localStorage is somehow out of sync.
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const t = get(token);
  if (t) {
    config.headers.set('Authorization', `Bearer ${t}`);
  }
  return config;
});

// ---------------------------------------------------------------------------
// Response interceptor — global error reaction.
// ---------------------------------------------------------------------------
// We do TWO things here:
//   (a) Swallow nothing — the error still propagates so the calling
//       page can show context-aware messages ("Invalid email" on the
//       login form, etc.). We just react to *transport-level* problems
//       that every page handles identically.
//   (b) On 401 from a NON-login endpoint, force a logout. A 401 from
//       /login is an "invalid credentials" message, not a session
//       expiry, so we let it through unchanged.
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const status = error.response?.status;
    const requestUrl = error.config?.url ?? '';

    if (status === 401 && !requestUrl.includes('/login') && !requestUrl.includes('/token')) {
      // Session expired or token revoked. Reset everything and bounce
      // back to the login screen.
      logout();
      navigate('login', null, /* replace */ true);
      notify.warning('انتهت صلاحية الجلسة، يرجى تسجيل الدخول مرة أخرى');
    } else if (error.code === 'ECONNABORTED' || error.message === 'Network Error') {
      // The backend is unreachable. Useful while the FastAPI server
      // is restarting in dev — this prevents a flood of red toasts
      // by deferring to the per-page error UI for *content* errors,
      // while still informing the user that the network is the issue.
      notify.error('تعذّر الاتصال بالخادم، يرجى التحقق من الاتصال');
    }

    return Promise.reject(error);
  },
);

export default api;

/**
 * Re-export AxiosRequestConfig so callers don't have to import axios
 * directly just to type a config arg. Small ergonomic win.
 */
export type { AxiosRequestConfig };
