<!--
  Knowledge Zakat — Student layout (with guest mode).

  When the visitor is a guest (`$token` is empty):
    • The sidebar shows only "استكشاف المحاضرات" — the other links
      would be useless without an account.
    • The header swaps the avatar/profile/logout cluster for two
      prominent CTAs: "تسجيل الدخول" and "إنشاء حساب".
    • A subtle "guest" pill appears next to the brand to remind the
      visitor they're browsing without an account.

  When authenticated, the layout behaves exactly as before.
-->

<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import { user, logout, token } from '../lib/stores';
  import { route, navigate } from '../lib/router';
  import { notify } from '../lib/notifications';
  import type { RouteName } from '../lib/types';
  import NotificationBell from './NotificationBell.svelte';

  import logoImg from '../assets/logo.jpg';
  import {
    LogOut,
    Globe,
    BookOpen,
    User as UserIcon,
    Menu,
    ChevronLeft,
    LogIn,
    UserPlus,
    Eye,
  } from 'lucide-svelte';

  let { children } = $props();
  let isSidebarOpen = $state(true);

  // Guest = no auth token. We expose this as a $derived signal so the
  // template can branch declaratively without manually re-evaluating.
  let isGuest = $derived(!$token);

  // Nav links shown to authenticated students.
  const authedNavLinks = [
    { id: 'home', label: 'استكشاف المحاضرات', icon: Globe },
    { id: 'my_learning', label: 'محاضراتي', icon: BookOpen },
    { id: 'student_profile', label: 'ملفي الشخصي', icon: UserIcon },
  ];

  // Guests only see "استكشاف" — every other link would route to a
  // page they can't access, which the router would just redirect
  // them back to /login from.
  const guestNavLinks = [
    { id: 'home', label: 'استكشاف المحاضرات', icon: Globe },
  ];

  let navLinks = $derived(isGuest ? guestNavLinks : authedNavLinks);

  function go(id: RouteName): void {
    navigate(id);
    if (window.innerWidth < 1024) isSidebarOpen = false;
  }

  function handleLogout(): void {
    logout();
    navigate('login', null, true);
    notify.info('تم تسجيل الخروج بنجاح');
  }

  function goLogin(): void {
    navigate('login', null, true);
  }

  function goRegister(): void {
    navigate('register', null, true);
  }
</script>

<div
  dir="rtl"
  class="min-h-screen bg-brand-100 font-sans text-[#2a3c54] relative overflow-hidden flex flex-col"
>
  <div class="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-brand-200/40 blur-3xl kz-blob-1 pointer-events-none"></div>
  <div class="absolute -bottom-32 -right-32 w-[28rem] h-[28rem] rounded-full bg-brand-300/30 blur-3xl kz-blob-2 pointer-events-none"></div>

  <!-- ─── Header ───────────────────────────────────────────────── -->
  <header
    class="relative z-50 bg-white/80 backdrop-blur-md border-b border-brand-200 h-20 md:h-24 flex items-center justify-between px-4 md:px-10 shadow-sm sticky top-0"
  >
    <div class="flex items-center gap-3 md:gap-5">
      <button
        onclick={() => (isSidebarOpen = !isSidebarOpen)}
        class="p-2 md:p-2.5 bg-brand-soft/50 border border-brand-200 text-brand rounded-xl hover:bg-brand-soft transition-all active:scale-95"
        aria-label="القائمة"
      >
        <Menu size={24} />
      </button>
      <div class="flex items-center gap-3">
        <div
          class="w-10 h-10 md:w-12 md:h-12 rounded-xl bg-white flex items-center justify-center shadow-kz-brand overflow-hidden p-1"
        >
          <img
            src={logoImg}
            alt="Logo"
            class="w-full h-full object-contain"
            style="mix-blend-mode: multiply; filter: contrast(1.1);"
          />
        </div>
        <div class="flex items-center gap-2">
          <h1 class="text-lg md:text-xl font-black text-brand leading-none">
            زكاة العلم
          </h1>
          {#if isGuest}
            <span
              class="hidden sm:inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-brand-soft text-brand text-[10px] font-bold border-kz border-brand-200"
              in:fade={{ duration: 200 }}
            >
              <Eye size={11} />
              زائر
            </span>
          {/if}
        </div>
      </div>
    </div>

    <!-- Right-side cluster: differs for guest vs authed -->
    {#if isGuest}
      <div class="flex items-center gap-2 md:gap-3" in:fade={{ duration: 200 }}>
        <button
          onclick={goLogin}
          class="flex items-center gap-2 bg-brand text-white px-3 py-2 md:px-5 md:py-2.5 rounded-xl font-black text-xs md:text-sm shadow-kz-brand hover:bg-brand-dark transition-all active:scale-95"
        >
          <LogIn size={16} />
          <span>تسجيل الدخول</span>
        </button>
        <button
          onclick={goRegister}
          class="hidden sm:flex items-center gap-2 bg-brand-soft text-brand px-4 py-2.5 rounded-xl font-black text-sm border-kz border-brand-200 hover:bg-brand-100 transition-all active:scale-95"
        >
          <UserPlus size={16} />
          <span>إنشاء حساب</span>
        </button>
      </div>
    {:else}
      <div class="flex items-center gap-3 md:gap-6">
        <NotificationBell />

        <button
          onclick={() => navigate('student_profile')}
          class="flex items-center gap-3 hover:-translate-y-0.5 transition-transform"
        >
          <div
            class="text-left hidden sm:block border-l border-brand-200 pl-5"
          >
            <div class="text-brand font-black text-xs uppercase">
              {$user?.firstname || 'طالب'}
            </div>
          </div>
          <div
            class="w-10 h-10 md:w-12 md:h-12 bg-brand-soft rounded-xl flex items-center justify-center text-brand font-black shadow-inner border border-white overflow-hidden"
          >
            {#if $user?.profile_image}
              <img
                src={$user.profile_image}
                alt="Avatar"
                class="w-full h-full object-cover"
              />
            {:else}
              {$user?.firstname?.charAt(0).toUpperCase() || 'S'}
            {/if}
          </div>
        </button>

        <button
          onclick={handleLogout}
          class="flex items-center gap-2 bg-red-50 text-red-500 px-3 py-2 md:px-4 md:py-2.5 rounded-xl font-black text-xs hover:bg-red-500 hover:text-white transition-all group shadow-sm"
        >
          <span class="hidden sm:inline">خروج</span>
          <LogOut size={18} class="group-hover:-translate-x-1 transition-transform" />
        </button>
      </div>
    {/if}
  </header>

  <!-- ─── Body ─────────────────────────────────────────────────── -->
  <div class="flex flex-1 w-full max-w-[1600px] mx-auto overflow-hidden relative">
    {#if isSidebarOpen}
      <aside
        transition:fly={{ x: 300, duration: 400, easing: quintOut }}
        class="w-72 bg-white/90 backdrop-blur-xl border-l border-brand-200 shadow-xl flex flex-col shrink-0 sticky top-0 h-[calc(100vh-6rem)] z-40"
      >
        <nav class="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
          {#each navLinks as link (link.id)}
            {@const isActive = $route.name === link.id}
            {@const Icon = link.icon}
            <button
              onclick={() => go(link.id as RouteName)}
              class="w-full flex items-center gap-3 px-4 py-3.5 rounded-2xl transition-all duration-300 group font-bold text-sm {isActive
                ? 'bg-brand text-white shadow-kz-brand translate-x-[-4px]'
                : 'text-ink-secondary hover:text-brand hover:bg-brand-soft'}"
            >
              <Icon
                size={20}
                class="{isActive
                  ? 'text-white'
                  : 'text-brand opacity-60 group-hover:opacity-100'} transition-all"
              />
              <span>{link.label}</span>
              {#if isActive}
                <ChevronLeft size={14} class="mr-auto text-white/50" />
              {/if}
            </button>
          {/each}

          <!-- Guest-only CTA inside the sidebar -->
          {#if isGuest}
            <div
              class="mt-6 pt-6 border-t border-brand-200/60"
              in:fade={{ duration: 250, delay: 200 }}
            >
              <div
                class="bg-gradient-to-br from-brand-soft to-brand-100 rounded-2xl p-4 border-kz border-brand-200"
              >
                <p class="text-xs font-bold text-brand mb-1">
                  انضم إلى زكاة العلم
                </p>
                <p class="text-[11px] text-ink-secondary leading-relaxed mb-3">
                  أنشئ حسابك للتسجيل بالمحاضرات، التقييم، والتواصل مع
                  المعلمين.
                </p>
                <button
                  onclick={goRegister}
                  class="w-full flex items-center justify-center gap-2 bg-brand text-white px-3 py-2.5 rounded-xl font-bold text-xs shadow-kz-brand hover:bg-brand-dark transition-all"
                >
                  <UserPlus size={14} />
                  <span>إنشاء حساب مجاناً</span>
                </button>
              </div>
            </div>
          {/if}
        </nav>
        <div class="p-4 border-t border-brand-100 space-y-4">
          <div
            class="text-[10px] text-center font-bold text-ink-muted uppercase tracking-tighter opacity-60"
          >
            زكاة العلم — 2026
          </div>
        </div>
      </aside>
    {/if}
    <main
      class="flex-1 p-6 md:p-10 min-w-0 overflow-y-auto"
      in:fade={{ duration: 300, delay: 100 }}
    >
      <div class="max-w-6xl mx-auto">{@render children()}</div>
    </main>
  </div>
</div>