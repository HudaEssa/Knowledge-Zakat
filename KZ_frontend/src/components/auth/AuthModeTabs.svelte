<!--
  Knowledge Zakat — Auth Mode Tabs.

  Two-tab pill toggle that drives the flip card. The animated
  background "pill" slides between the two options. RTL-aware:
  uses `right` to position the pill so it lands under the correct
  tab in Arabic layout.

  Controlled component:
   - `mode`: which face is currently showing ('login' | 'register').
   - `onChange`: parent handler. Parent navigates the URL so refresh
     keeps the right face up.
-->

<script lang="ts">
  type AuthMode = 'login' | 'register';

  interface Props {
    mode: AuthMode;
    onChange: (mode: AuthMode) => void;
  }

  let { mode, onChange }: Props = $props();

  // The sliding "pill" is positioned with `right` (because dir="rtl").
  // - Login on the right side (default): right = 0.375rem
  // - Register on the left side:         right = calc(50% + 0.375rem)
  let pillRight = $derived(
    mode === 'register' ? 'calc(50% + 0.375rem)' : '0.375rem',
  );
</script>

<div
  class="bg-white/70 backdrop-blur rounded-full p-1.5 mb-5 border-kz border-brand-200 grid grid-cols-2 gap-1 relative"
  role="tablist"
  aria-label="نوع البطاقة"
>
  <!-- Animated background pill -->
  <div
    class="absolute top-1.5 bottom-1.5 w-[calc(50%-0.375rem)] rounded-full bg-brand shadow-kz-brand transition-all duration-500 ease-out"
    style="right: {pillRight};"
    aria-hidden="true"
  ></div>

  <button
    type="button"
    role="tab"
    aria-selected={mode === 'login'}
    onclick={() => onChange('login')}
    class="relative z-10 py-2.5 text-sm font-bold rounded-full transition-colors duration-300 {mode ===
    'login'
      ? 'text-white'
      : 'text-ink-secondary hover:text-brand'}"
  >
    تسجيل الدخول
  </button>

  <button
    type="button"
    role="tab"
    aria-selected={mode === 'register'}
    onclick={() => onChange('register')}
    class="relative z-10 py-2.5 text-sm font-bold rounded-full transition-colors duration-300 {mode ===
    'register'
      ? 'text-white'
      : 'text-ink-secondary hover:text-brand'}"
  >
    إنشاء حساب
  </button>
</div>
