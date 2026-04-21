<script>
  import { currentPage, token, user } from "../lib/stores";
  
  let isDropdownOpen = false; // للتحكم بالقائمة المنسدلة

  function logout() {
    token.set(null);
    user.set(null); // نصفر اليوزر هم
    currentPage.set("login");
  }

  function navigateTo(page) {
    currentPage.set(page);
    isDropdownOpen = false; // نسد القائمة اذا حولنا صفحة
  }
</script>

<div class="min-h-screen bg-slate-50 flex flex-col">
  
  <header class="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-20 items-center">
        
        <button on:click={() => navigateTo('home')} class="flex items-center gap-3 hover:opacity-80 transition">
          <div class="w-10 h-10 bg-blue-900 rounded-xl flex items-center justify-center text-white text-2xl shadow-lg">
            🎓
          </div>
          <h1 class="text-2xl font-bold text-blue-900 tracking-tight">زكاة العلم</h1>
        </button>

        <nav class="hidden md:flex items-center gap-8 font-medium text-gray-600">
          <button 
            on:click={() => navigateTo('home')} 
            class:text-blue-900={$currentPage === 'home'} 
            class:bg-blue-50={$currentPage === 'home'}
            class="px-4 py-2 rounded-lg hover:bg-slate-50 hover:text-blue-900 transition-all"
          >
            الرئيسية
          </button>
          
          <button 
            on:click={() => navigateTo('sessions')} 
            class:text-blue-900={$currentPage === 'sessions'}
            class:bg-blue-50={$currentPage === 'sessions'}
            class="px-4 py-2 rounded-lg hover:bg-slate-50 hover:text-blue-900 transition-all"
          >
            كل الجلسات
          </button>

          <button 
            on:click={() => navigateTo('my_sessions')} 
            class:text-blue-900={$currentPage === 'my_sessions'}
            class:bg-blue-50={$currentPage === 'my_sessions'}
            class="px-4 py-2 rounded-lg hover:bg-slate-50 hover:text-blue-900 transition-all"
          >
            جلساتي المشتركة
          </button>
        </nav>

        <div class="relative">
          <button 
            on:click={() => isDropdownOpen = !isDropdownOpen}
            class="flex items-center gap-3 pl-2 pr-1 py-1 rounded-full border border-gray-200 hover:shadow-md transition bg-white"
          >
            <span class="text-sm font-bold text-gray-700 hidden sm:block pl-2">
              {$user ? $user.firstname : 'User'}
            </span>
            {#if $user && $user.profile_image_url}
              <img src={$user.profile_image_url} alt="Profile" class="w-10 h-10 rounded-full object-cover border-2 border-white shadow-sm" />
            {:else}
              <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-900 font-bold border-2 border-white shadow-sm">
                {$user ? $user.firstname[0].toUpperCase() : 'U'}
              </div>
            {/if}
            <svg class="w-4 h-4 text-gray-400 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
          </button>

          {#if isDropdownOpen}
            <div class="absolute left-0 mt-3 w-48 bg-white rounded-xl shadow-xl border border-gray-100 overflow-hidden animate-fade-in z-50">
              <div class="py-1">
                <button 
                  on:click={() => navigateTo('profile')}
                  class="flex items-center w-full px-4 py-3 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-900 transition"
                >
                  <span class="ml-2">👤</span> الملف الشخصي
                </button>
                <button 
                  on:click={() => navigateTo('my_sessions')}
                  class="flex items-center w-full px-4 py-3 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-900 transition"
                >
                  <span class="ml-2">📚</span> جلساتي
                </button>
                <div class="border-t border-gray-100 my-1"></div>
                <button 
                  on:click={logout}
                  class="flex items-center w-full px-4 py-3 text-sm text-red-600 hover:bg-red-50 transition"
                >
                  <span class="ml-2">🚪</span> تسجيل الخروج
                </button>
              </div>
            </div>
          <button 
  class="fixed inset-0 z-40 w-full h-full cursor-default focus:outline-none" 
  on:click={() => isDropdownOpen = false} 
  type="button"
  aria-label="Close menu"
></button>
          {/if}
        </div>

      </div>
    </div>
  </header>

  <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <slot />
  </main>

  <footer class="bg-white border-t border-gray-200 py-6 text-center text-gray-500 text-sm">
    © 2025 منصة زكاة العلم. جميع الحقوق محفوظة.
  </footer>
</div>