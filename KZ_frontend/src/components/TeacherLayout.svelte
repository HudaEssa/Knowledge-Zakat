<script>
  import { currentPage, user, token } from "../lib/stores";
  import { fly, fade } from 'svelte/transition';
  
  let { children } = $props();
  let isMenuOpen = $state(false); 

  const navLinks = [
    { id: 'teacher_home', label: 'لوحة التحكم' },
    { id: 'create_session', label: 'إنشاء جلسة جديدة' },
    { id: 'my_lectures', label: 'محاضراتي' },
    { id: 'student_requests', label: 'طلبات الانضمام' },
    { id: 'profile', label: 'الملف الشخصي' }
  ];

  function handleLogout() { 
    localStorage.clear(); 
    token.set(null);
    user.set(null);
    location.reload(); 
  }
</script>

<div dir="rtl" class="min-h-screen w-full bg-gradient-to-b from-slate-100 to-slate-200 font-sans text-[#2a3c54] relative">
  
  <header class="fixed top-0 left-0 right-0 h-24 px-10 flex justify-between items-center z-[100] bg-white/80 backdrop-blur-md border-b border-slate-200">
    <div class="flex items-center gap-8 pointer-events-auto">
      <button onclick={() => isMenuOpen = !isMenuOpen} class="flex flex-col gap-1.5 group">
        <div class="w-8 h-1 bg-[#2a3c54] rounded-full transition-all {isMenuOpen ? 'rotate-45 translate-y-2.5' : ''}"></div>
        <div class="w-8 h-1 bg-[#2a3c54] rounded-full transition-all {isMenuOpen ? 'opacity-0' : ''}"></div>
        <div class="w-8 h-1 bg-[#2a3c54] rounded-full transition-all {isMenuOpen ? '-rotate-45 -translate-y-2.5' : ''}"></div>
      </button>
      <h1 class="text-xl font-black tracking-tighter">زكاة العلم <span class="text-[#6b8cce] text-xs block font-bold">بوابة المعلم</span></h1>
    </div>

    <div class="flex items-center gap-4">
      <button onclick={() => currentPage.set('profile')} class="w-12 h-12 rounded-2xl bg-[#2a3c54] flex items-center justify-center shadow-lg border-2 border-white overflow-hidden">
        {#if $user?.profile_image}
          <img src={$user.profile_image} alt="profile" class="w-full h-full object-cover" />
        {:else}
          <span class="text-white font-black">{$user?.firstname?.charAt(0).toUpperCase()}</span>
        {/if}
      </button>
      <button onclick={handleLogout} class="p-2 text-slate-400 hover:text-red-500 transition-all">
        <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg>
      </button>
    </div>
  </header>

  {#if isMenuOpen}
    <div transition:fade class="fixed inset-0 bg-[#2a3c54]/40 backdrop-blur-sm z-[150]" onclick={() => isMenuOpen = false}></div>
    
    <aside 
      transition:fly={{ x: 320, duration: 400 }} 
      class="fixed top-0 right-0 h-full w-80 bg-[#2a3c54] z-[200] shadow-2xl p-10 pt-32 flex flex-col border-l border-white/10 text-white"
    >
      <nav class="space-y-6">
        {#each navLinks as link}
          <button 
            onclick={() => { currentPage.set(link.id); isMenuOpen = false; }} 
            class="w-full text-right text-lg font-bold py-3 transition-all flex items-center justify-between group
            {$currentPage === link.id ? 'text-[#acc2f0] pr-4 border-r-4 border-[#acc2f0]' : 'opacity-50 hover:opacity-100 hover:pr-2'}">
            {link.label}
          </button>
        {/each}
      </nav>
      
      <div class="mt-auto pt-10 border-t border-white/10 opacity-30 text-[10px] text-center font-bold">
        لوحة تحكم المعلم - 2026
      </div>
    </aside>
  {/if}

  <main class="pt-32 px-6 md:px-16 w-full max-w-[1400px] mx-auto">
    {@render children()}
  </main>
</div>