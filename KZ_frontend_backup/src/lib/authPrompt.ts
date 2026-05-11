/**
 * Knowledge Zakat — Auth Prompt store.
 *
 * Lightweight global signal used by the <AuthPromptToast /> component.
 * Any page can call `authPrompt.show(message)` to nudge a guest user
 * toward signing in / registering, and `authPrompt.hide()` to dismiss.
 *
 * Why a store and not a prop drill: the toast lives at the App root
 * (so it overlays any page) but the trigger is deep inside Home /
 * SessionDetails / TeacherView. A store keeps the wiring trivial.
 */

import { writable } from 'svelte/store';

interface AuthPromptState {
  visible: boolean;
  message: string;
}

function createAuthPrompt() {
  const { subscribe, set } = writable<AuthPromptState>({
    visible: false,
    message: '',
  });

  // Auto-hide timer handle; reset on every `show()` so back-to-back
  // calls don't stack timers.
  let timer: ReturnType<typeof setTimeout> | null = null;

  function show(message: string, autoHideMs = 8000): void {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
    set({ visible: true, message });
    if (autoHideMs > 0) {
      timer = setTimeout(() => {
        set({ visible: false, message: '' });
        timer = null;
      }, autoHideMs);
    }
  }

  function hide(): void {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
    set({ visible: false, message: '' });
  }

  return { subscribe, show, hide };
}

export const authPrompt = createAuthPrompt();