<script>
  import { currentPage, user, token } from "../lib/stores"; // [cite: 64]
  
  // استخدام الـ Runes لـ Svelte 5 [cite: 65]
  let isMenuOpen = $state(true); 

  const navLinks = [
    { id: 'home', label: 'استكشاف المحاضرات', icon: '🌐' },
    { id: 'my_learning', label: 'جلساتي العلمية', icon: '📚' },
    { id: 'student_profile', label: 'ملفي الشخصي', icon: '👤' }
  ];

  function handleLogout() { 
    localStorage.clear(); 
    token.set(null); // [cite: 67]
    user.set(null);
    location.reload(); 
  }
</script>

<div dir="rtl" class="h-screen flex flex-col bg-[#f1f5f9] overflow-hidden font-sans">
  
 <header class="h-20 bg-[#2a3c54] px-8 flex justify-between items-center z-[120] shadow-md border-b border-white/5 shrink-0">
  <div class="flex items-center gap-6">
    <button onclick={() => isMenuOpen = !isMenuOpen} class="text-white p-2 hover:bg-white/10 rounded-xl transition-all">
      <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
      </svg>
    </button>
    <div class="flex flex-col">
      <span class="text-xs font-black text-[#acc2f0] uppercase tracking-tighter">Knowledge Zakat</span>
    </div>
  </div>

  <div class="flex items-center gap-5">
    <button 
      onclick={() => currentPage.set('student_profile')} 
      class="flex items-center gap-4 border-l pl-5 border-white/10 hover:opacity-80 transition-all group"
    >
      <span class="text-sm font-bold text-white group-hover:text-[#6b8cce]">{$user?.firstname}</span> 
      
      <div class="w-10 h-10 rounded-xl bg-white p-0.5 shadow-lg overflow-hidden border border-white/10 group-hover:ring-2 ring-[#6b8cce]">
        {#if $user?.profile_image}
          <img src={$user.profile_image} alt="User" class="w-full h-full object-cover rounded-lg" />
        {:else}
          <div class="w-full h-full bg-[#eff3fa] flex items-center justify-center text-[#6b8cce] font-black">
            {$user?.firstname?.charAt(0).toUpperCase()}
          </div>
        {/if}
      </div>
    </button>

    <button onclick={handleLogout} class="text-white/40 hover:text-red-400 transition-all">
      <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
      </svg>
    </button>
  </div>
</header>

  <div class="flex flex-1 overflow-hidden">
    <aside 
      class="bg-[#30445e] transition-all duration-300 ease-in-out shrink-0 z-[110] shadow-2xl border-l border-white/5 overflow-hidden
      {isMenuOpen ? 'w-72' : 'w-0'}" 
    >
      <div class="w-72 flex flex-col h-full"> 
        <nav class="flex-1 px-4 py-8 space-y-2">
          {#each navLinks as link}
            <button 
              onclick={() => currentPage.set(link.id)} 
              class="w-full flex items-center gap-4 px-6 py-4 rounded-2xl transition-all font-black text-sm
              {$currentPage === link.id ? 'bg-[#2a3c54] text-white shadow-lg border border-white/5' : 'text-white/50 hover:bg-white/5 hover:text-white'}"
            >
              <span class="text-xl opacity-70">{link.icon}</span>
              <span>{link.label}</span>
            </button>
          {/each}
        </nav>
        
       
      </div>
    </aside>

    <main class="flex-1 overflow-y-auto p-10">
      <div class="max-w-6xl mx-auto">
        <slot /> 
      </div>
    </main>
  </div>
</div>