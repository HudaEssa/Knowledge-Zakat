<script>
  import { token, user, currentPage } from "../lib/stores";
  import api from "../lib/api";
  let { children } = $props();

  function handleLogout() {
    localStorage.clear();
    token.set(null);
    user.set(null);
    currentPage.set('login');
  }
</script>

<div dir="rtl" class="min-h-screen bg-[#f8fafc] font-sans text-[#2a3c54]">
  <header class="bg-white border-b border-slate-100 sticky top-0 z-50 shadow-sm">
    <div class="max-w-7xl mx-auto px-8 h-24 flex justify-between items-center">
      
      <div class="flex flex-col">
          <span class="text-xs font-black text-[#6b8cce] uppercase tracking-tighter">Knowledge Zakat</span>
          <span class="text-sm font-bold opacity-30 tracking-widest">ADMIN PANEL</span>
      </div>

      <div class="flex items-center gap-6 border-r pr-8 border-slate-100">
        <button onclick={handleLogout} class="text-slate-300 hover:text-red-500 transition-all p-2 group" title="تسجيل الخروج">
          <svg class="w-7 h-7 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
          </svg>
        </button>

        <div class="w-12 h-12 bg-[#eff3fa] rounded-2xl flex items-center justify-center text-[#6b8cce] font-black shadow-inner border border-white">
          {$user?.firstname?.substring(0, 1).toUpperCase() || 'A'}
        </div>

        <div class="flex flex-col text-right">
          <span class="text-[10px] font-black uppercase text-[#6b8cce] tracking-widest">Administrator</span>
          <span class="text-sm font-bold text-slate-600">{$user?.firstname}</span>
        </div>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto p-10">
    {@render children()}
  </main>
</div>