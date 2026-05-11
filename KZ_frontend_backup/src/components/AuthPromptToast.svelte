<!--
  Knowledge Zakat — Auth Prompt Toast.

  Shown to guest users when they try to perform an action that
  requires authentication (enroll, rate, comment, etc).

  Lives at the top-right of the viewport, dismissible, with a
  primary "Login" button that navigates to the auth page in the
  desired mode (login or register).

  Usage:
    import { authPrompt } from '../lib/authPrompt';
    authPrompt.show('يجب تسجيل الدخول لتتمكن من التقييم');
-->

<script lang="ts">
  import { fly, fade } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import { LogIn, UserPlus, X, AlertCircle } from 'lucide-svelte';
  import { navigate } from '../lib/router';
  import { authPrompt } from '../lib/authPrompt';

  function goLogin(): void {
    authPrompt.hide();
    navigate('login', null, true);
  }

  function goRegister(): void {
    authPrompt.hide();
    navigate('register', null, true);
  }

  function dismiss(): void {
    authPrompt.hide();
  }
</script>

{#if $authPrompt.visible}
  <div
    dir="rtl"
    class="fixed top-24 right-4 md:right-8 z-[100] max-w-sm w-[calc(100vw-2rem)] md:w-96"
    in:fly={{ y: -30, duration: 350, easing: quintOut }}
    out:fade={{ duration: 200 }}
  >
    <div
      class="bg-white border-kz border-brand-200 rounded-3xl shadow-kz-xl overflow-hidden"
    >
      <!-- Top stripe -->
      <div class="h-1.5 bg-gradient-to-l from-brand to-brand-400"></div>

      <!-- Body -->
      <div class="p-5 md:p-6">
        <div class="flex items-start gap-3 mb-4">
          <div
            class="w-11 h-11 rounded-2xl bg-brand-soft flex items-center justify-center text-brand shrink-0"
          >
            <AlertCircle size={22} />
          </div>
          <div class="flex-1 min-w-0 pt-1">
            <h3 class="text-base font-bold text-brand leading-tight">
              يلزم تسجيل الدخول
            </h3>
            <p class="text-sm text-ink-secondary mt-1.5 leading-relaxed">
              {$authPrompt.message || 'يجب تسجيل الدخول لإكمال هذه العملية'}
            </p>
          </div>
          <button
            type="button"
            onclick={dismiss}
            aria-label="إغلاق"
            class="text-ink-muted hover:text-brand transition-colors p-1 -m-1 shrink-0"
          >
            <X size={18} />
          </button>
        </div>

        <!-- Action buttons -->
        <div class="grid grid-cols-2 gap-2.5">
          <button
            type="button"
            onclick={goLogin}
            class="flex items-center justify-center gap-2 px-4 py-2.5 bg-brand text-white rounded-xl font-bold text-sm shadow-kz-brand hover:bg-brand-dark transition-all active:scale-[0.98]"
          >
            <LogIn size={16} />
            <span>تسجيل الدخول</span>
          </button>
          <button
            type="button"
            onclick={goRegister}
            class="flex items-center justify-center gap-2 px-4 py-2.5 bg-brand-soft text-brand rounded-xl font-bold text-sm border-kz border-brand-200 hover:bg-brand-100 transition-all active:scale-[0.98]"
          >
            <UserPlus size={16} />
            <span>إنشاء حساب</span>
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}