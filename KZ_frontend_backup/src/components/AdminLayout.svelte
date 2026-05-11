<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import { user, logout } from '../lib/stores';
  import { navigate } from '../lib/router';
  import { notify } from '../lib/notifications';
  
  // 1. استيراد الصورة كـ متغير (هذا هو الحل لمشكلة عدم الظهور)
  import logoImg from '../assets/logo.jpg'; 

  // 2. استيراد أيقونات احترافية (Lucide) بدلاً من الأيموجيات
  import { 
    LogOut, 
    Users, 
    LayoutDashboard, 
    Activity, 
    Tags, 
    User as UserIcon,
    ShieldCheck
  } from 'lucide-svelte';

  let { children } = $props();

  function handleLogout(): void {
    logout();
    navigate('login', null, true);
    notify.info('تم تسجيل الخروج');
  }
</script>

<div dir="rtl" class="min-h-screen bg-brand-100 font-sans text-[#2a3c54] relative overflow-hidden flex flex-col">
  <div class="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-brand-200/40 blur-3xl kz-blob-1 pointer-events-none"></div>
  <div class="absolute -bottom-32 -right-32 w-[28rem] h-[28rem] rounded-full bg-brand-300/30 blur-3xl kz-blob-2 pointer-events-none"></div>

  <header class="relative z-50 bg-white/70 backdrop-blur-md border-b border-brand-200 sticky top-0 shadow-sm">
    <div class="max-w-7xl mx-auto px-6 md:px-10 h-20 md:h-24 flex justify-between items-center">
      
      <div class="flex items-center gap-4">
        <div class="w-14 h-14 md:w-16 md:h-16 rounded-2xl bg-white flex items-center justify-center shadow-kz-brand overflow-hidden p-1">
          <img 
            src={logoImg} 
            alt="Zakat Logo" 
            class="w-full h-full object-contain"
            style="mix-blend-mode: multiply; filter: contrast(1.1);" 
          />
        </div>
        <div class="flex flex-col">
          <h1 class="text-xl font-black text-brand leading-none">زكاة العلم</h1>
          <span class="text-[10px] font-bold text-ink-muted tracking-[0.2em] uppercase mt-1">Admin Panel</span>
        </div>
      </div>

      <div class="flex items-center gap-4">
        <div class="hidden sm:flex items-center gap-4 border-l pl-6 border-brand-200">
          <div class="text-left text-brand font-black text-xs">ADMINISTRATOR</div>
          <div class="w-12 h-12 bg-brand-soft rounded-2xl flex items-center justify-center text-brand font-black shadow-inner border border-white">
            {$user?.firstname?.charAt(0).toUpperCase() || 'A'}
          </div>
        </div>

        <button onclick={handleLogout} class="flex items-center gap-2 bg-red-50 text-red-500 px-4 py-2.5 rounded-xl font-black text-xs hover:bg-red-500 hover:text-white transition-all group">
          <span>خروج</span>
          <LogOut size={18} class="group-hover:translate-x-1 transition-transform" />
        </button>
      </div>
    </div>
  </header>

  <main class="relative z-10 flex-1 max-w-7xl mx-auto w-full p-6 md:p-10" in:fade>
    {@render children()}
  </main>
</div>

<style>
  :global(.kz-blob-1), :global(.kz-blob-2) {
    will-change: transform;
    animation: blob-float 20s infinite alternate ease-in-out;
  }
  @keyframes blob-float {
    from { transform: translate(0, 0) scale(1); }
    to { transform: translate(5%, 10%) scale(1.1); }
  }
  .shadow-kz-brand { box-shadow: 0 8px 20px -4px rgba(107, 140, 206, 0.4); }
</style>