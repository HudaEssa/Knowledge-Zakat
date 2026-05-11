<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import { user, logout } from '../lib/stores';
  import { route, navigate } from '../lib/router';
  import { notify } from '../lib/notifications';
  import type { RouteName } from '../lib/types';
  import NotificationBell from './NotificationBell.svelte'; // 👈 استيراد الجرس
  
  import logoImg from '../assets/logo.jpg'; 
  import { 
    LogOut, LayoutDashboard, PlusCircle, BookOpen, 
    Users, User as UserIcon, Menu, ChevronRight, X
  } from 'lucide-svelte';

  let { children } = $props();
  let isSidebarOpen = $state(true);

  const navLinks = [
    { id: 'teacher_home', label: 'لوحة الإحصائيات', icon: LayoutDashboard },
    { id: 'create_session', label: 'إنشاء محاضرة جديدة', icon: PlusCircle },
    { id: 'my_lectures', label: 'محاضراتي', icon: BookOpen },
    { id: 'teacher_requests', label: 'طلبات الانضمام', icon: Users },
    { id: 'profile', label: 'الملف الشخصي', icon: UserIcon },
  ];

  function go(id: RouteName): void {
    navigate(id);
    if (window.innerWidth < 1024) isSidebarOpen = false;
  }

  function handleLogout(): void {
    logout();
    navigate('login', null, true);
    notify.info('تم تسجيل الخروج بنجاح');
  }
</script>

<div dir="rtl" class="min-h-screen bg-brand-100 font-sans text-[#2a3c54] relative overflow-hidden flex flex-col">
  <div class="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-brand-200/40 blur-3xl kz-blob-1 pointer-events-none"></div>
  <div class="absolute -bottom-32 -right-32 w-[28rem] h-[28rem] rounded-full bg-brand-300/30 blur-3xl kz-blob-2 pointer-events-none"></div>

  <header class="relative z-50 bg-white/80 backdrop-blur-md border-b border-brand-200 h-20 md:h-24 flex items-center justify-between px-4 md:px-10 shadow-sm sticky top-0">
    <div class="flex items-center gap-3 md:gap-5">
      <button onclick={() => isSidebarOpen = !isSidebarOpen} class="p-2 md:p-2.5 bg-brand-soft/50 border border-brand-200 text-brand rounded-xl hover:bg-brand-soft transition-all active:scale-95">
        <Menu size={24} />
      </button>
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 md:w-12 md:h-12 rounded-xl bg-white flex items-center justify-center shadow-kz-brand overflow-hidden p-1">
          <img src={logoImg} alt="Logo" class="w-full h-full object-contain" style="mix-blend-mode: multiply; filter: contrast(1.1);" />
        </div>
        <div class="flex flex-col">
          <h1 class="text-lg md:text-xl font-black text-brand leading-none">زكاة العلم</h1>
          <span class="text-[10px] font-bold text-ink-muted tracking-widest uppercase mt-1">بوابة المعلم</span>
        </div>
      </div>
    </div>

    <div class="flex items-center gap-3 md:gap-6">
      <NotificationBell />

      <button onclick={() => navigate('profile')} class="flex items-center gap-3 hover:-translate-y-0.5 transition-transform">
        <div class="text-left hidden sm:block border-r border-brand-200 pr-5">
          <div class="text-brand font-black text-xs uppercase">{$user?.firstname || 'معلم'}</div>
          <div class="text-[10px] font-bold text-ink-muted">حساب معلم</div>
        </div>
        <div class="w-10 h-10 md:w-12 md:h-12 bg-brand-soft rounded-xl flex items-center justify-center text-brand font-black shadow-inner border border-white overflow-hidden">
          {#if $user?.profile_image}
            <img src={$user.profile_image} alt="Avatar" class="w-full h-full object-cover" />
          {:else}
            {$user?.firstname?.charAt(0).toUpperCase() || 'T'}
          {/if}
        </div>
      </button>

      <button onclick={handleLogout} class="flex items-center gap-2 bg-red-50 text-red-500 px-3 py-2 md:px-4 md:py-2.5 rounded-xl font-black text-xs hover:bg-red-500 hover:text-white transition-all group shadow-sm">
        <span class="hidden sm:inline">خروج</span>
        <LogOut size={18} class="group-hover:-translate-x-1 transition-transform" />
      </button>
    </div>
  </header>

  <div class="flex flex-1 w-full max-w-[1600px] mx-auto overflow-hidden relative">
    {#if isSidebarOpen}
      <aside transition:fly={{ x: 300, duration: 400, easing: quintOut }} class="w-72 bg-white/90 backdrop-blur-xl border-l border-brand-200 shadow-xl flex flex-col shrink-0 sticky top-0 h-[calc(100vh-6rem)] z-40">
        <nav class="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
          {#each navLinks as link (link.id)}
            {@const isActive = $route.name === link.id}
            {@const Icon = link.icon}
            <button onclick={() => go(link.id as RouteName)} class="w-full flex items-center gap-3 px-4 py-3.5 rounded-2xl transition-all duration-300 group font-bold text-sm {isActive ? 'bg-brand text-white shadow-kz-brand translate-x-[-4px]' : 'text-ink-secondary hover:text-brand hover:bg-brand-soft'}">
              <Icon size={20} class="{isActive ? 'text-white' : 'text-brand opacity-60 group-hover:opacity-100'} transition-all" />
              <span>{link.label}</span>
              {#if isActive}<ChevronRight size={14} class="mr-auto text-white/50" />{/if}
            </button>
          {/each}
        </nav>
        <div class="p-4 border-t border-brand-100 space-y-4">
          <button onclick={handleLogout} class="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-2xl text-red-500 hover:bg-red-50 transition-all font-black text-sm group">
            <LogOut size={20} class="group-hover:-translate-x-1 transition-transform" />
            <span>تسجيل الخروج</span>
          </button>
          <div class="text-[10px] text-center font-bold text-ink-muted uppercase tracking-tighter opacity-60">زكاة العلم — 2026</div>
        </div>
      </aside>
    {/if}
    <main class="flex-1 p-6 md:p-10 min-w-0 overflow-y-auto" in:fade={{ duration: 300, delay: 100 }}>
      <div class="max-w-6xl mx-auto">{@render children()}</div>
    </main>
  </div>
</div>