/**
 * Global TypeScript ambient declarations for Knowledge Zakat.
 *
 * Place this file at `src/app.d.ts` (next to App.svelte). Vite +
 * svelte-check pick it up automatically and apply its types
 * project-wide. No imports needed.
 *
 * What this file does:
 *  - Tells TypeScript about Vite's `import.meta.env.VITE_*` variables
 *    so calls like `import.meta.env.VITE_API_URL` are typed.
 *  - Allows importing `.svelte` files from `.ts` modules without
 *    "Cannot find module" errors. (svelte-check usually injects a
 *    similar shim, but being explicit is robust against tooling drift.)
 */

/// <reference types="svelte" />
/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the FastAPI backend, e.g. http://127.0.0.1:8000.
   *  Defined in .env (or .env.local) and injected by Vite at build time. */
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare module '*.svelte' {
  import type { ComponentType, SvelteComponent } from 'svelte';
  const component: ComponentType<SvelteComponent>;
  export default component;
}
