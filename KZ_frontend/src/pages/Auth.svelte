<!--
  Knowledge Zakat — Auth page (orchestrator).

  This page is now a thin shell: it picks the mode from the URL,
  passes navigation handlers down, and lays out the marketing aside
  + the flip card. Every piece of UI lives in /components/auth/* so
  no Auth concern leaks into other parts of the codebase.

  Composition:
    Auth.svelte
    ├── <AuthBackground />          decorative blobs
    ├── <AuthMarketingAside />      desktop-only left column
    └── flip card stage
        ├── <AuthModeTabs />        Login | Register pill toggle
        └── <AuthFlipCard>
            ├── {#snippet front()} <LoginForm /> {/snippet}
            └── {#snippet back()}  <RegisterForm /> {/snippet}

  Routing contract is unchanged:
    - '/login'    → flip card shows the front (login)
    - '/register' → flip card shows the back (register)
-->

<script lang="ts">
  import { GraduationCap } from 'lucide-svelte';
  import { route, navigate } from '../lib/router';
  import type { User } from '../lib/types';

  // Auth-specific components — all isolated under /components/auth/
  import AuthBackground from '../components/auth/AuthBackground.svelte';
  import AuthMarketingAside from '../components/auth/AuthMarketingAside.svelte';
  import AuthModeTabs from '../components/auth/AuthModeTabs.svelte';
  import AuthFlipCard from '../components/auth/AuthFlipCard.svelte';
  import LoginForm from '../components/auth/LoginForm.svelte';
  import RegisterForm from '../components/auth/RegisterForm.svelte';

  type AuthMode = 'login' | 'register';

  // Mode comes from the URL, so refresh keeps the right face up.
  let mode = $derived<AuthMode>(
    $route.name === 'register' ? 'register' : 'login',
  );
  let isRegisterMode = $derived(mode === 'register');

  // ── Handlers passed down to child components ──────────────────
  function handleModeChange(target: AuthMode): void {
    if (target !== mode) navigate(target, null, true);
  }

  function handleSuccess(_user: User): void {
    // Tiny delay so the success toast has time to render before
    // the page transitions away.
    setTimeout(() => navigate('home', null, true), 400);
  }

  function handleGuest(): void {
    navigate('home', null, true);
  }
</script>

<div
  class="min-h-screen w-full flex items-stretch bg-brand-100 relative"
  dir="rtl"
>
  <AuthBackground />

  <AuthMarketingAside onGuest={handleGuest} />

  <main
    class="flex-1 flex items-start lg:items-center justify-center p-6 md:p-12 relative z-10 overflow-y-auto"
  >
    <div class="w-full max-w-md">
      <!-- Mobile-only brand strip -->
      <div class="lg:hidden flex items-center justify-center gap-3 mb-6">
        <div
          class="w-12 h-12 rounded-2xl bg-brand flex items-center justify-center text-white shadow-kz-brand"
        >
          <GraduationCap size={24} />
        </div>
        <h1 class="text-xl font-bold text-brand">زكاة العلم</h1>
      </div>

      <AuthModeTabs {mode} onChange={handleModeChange} />

      <AuthFlipCard isFlipped={isRegisterMode}>
        {#snippet front()}
          <LoginForm onSuccess={handleSuccess} onGuest={handleGuest} />
        {/snippet}
        {#snippet back()}
          <RegisterForm onSuccess={handleSuccess} onGuest={handleGuest} />
        {/snippet}
      </AuthFlipCard>

    
    </div>
  </main>
</div>