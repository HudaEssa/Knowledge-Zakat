<script>
  import { onMount } from "svelte";
  import api from "../lib/api";
  import { currentPage } from "../lib/stores";
  import { fade, slide } from "svelte/transition";

  let { teacherId } = $props(); // نستلم رقم الأستاذ
  
  let teacher = $state(null);
  let isLoading = $state(true);

  onMount(async () => {
    try {
      const res = await api.get(`/teachers/${teacherId}/profile`);
      teacher = res.data;
    } catch (e) {
      console.error(e);
    } finally {
      isLoading = false;
    }
  });

  function navigateToDetails(sessionId) {
    currentPage.set({ name: 'session_details', data: { sessionId: sessionId } });
  }
</script>

<div class="min-h-screen bg-slate-50 py-10 px-4 md:px-10 font-sans text-right" dir="rtl">
  
  <div class="max-w-5xl mx-auto mb-6 flex justify-start">
    <button onclick={() => currentPage.set('home')} class="flex items-center gap-2 bg-white px-6 py-3 rounded-2xl shadow-sm text-[#4a6583] font-black hover:bg-[#6b8cce] hover:text-white transition-all border border-slate-200">
      <span>رجوع للرئيسية</span>
      <svg class="w-5 h-5 rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
    </button>
  </div>

  {#if isLoading}
    <div class="text-center mt-20 text-[#6b8cce] font-black animate-pulse text-xl">جاري تحميل بروفايل الأستاذ...</div>
  {:else if teacher}
    <div class="max-w-5xl mx-auto space-y-8">
      
      <div class="bg-gradient-to-bl from-[#2a3c54] to-[#4a6583] p-10 rounded-[3rem] shadow-lg text-white flex flex-col md:flex-row gap-8 items-center md:items-start relative overflow-hidden">
        <div class="absolute top-0 left-0 w-64 h-64 bg-white opacity-5 rounded-full -ml-20 -mt-20 blur-3xl"></div>
        
        <div class="w-40 h-40 bg-slate-200 rounded-full overflow-hidden shrink-0 border-4 border-white/20 shadow-2xl flex items-center justify-center text-6xl text-[#6b8cce] font-black z-10">
         
          {#if teacher.image}
            <img src={teacher.image} alt="Teacher" class="w-full h-full object-cover" />
          {:else}
            {teacher.name.charAt(0)}
          {/if}
        </div>
        
        <div class="flex-1 z-10 text-center md:text-right">
          <h1 class="text-4xl font-black mb-2">{teacher.name}</h1>
          <p class="text-slate-300 font-bold mb-6 italic leading-relaxed">{teacher.bio}</p>
          
          <div class="flex flex-wrap justify-center md:justify-start gap-4">
            <div class="bg-white/10 px-5 py-2.5 rounded-2xl border border-white/10 backdrop-blur-md">
              <span class="block text-xs font-bold text-slate-300 mb-1">التقييم العام</span>
              <span class="font-black text-xl text-amber-400">⭐ {teacher.avg_rating > 0 ? teacher.avg_rating : 'جديد'}</span>
            </div>
            <div class="bg-white/10 px-5 py-2.5 rounded-2xl border border-white/10 backdrop-blur-md">
              <span class="block text-xs font-bold text-slate-300 mb-1">عدد المحاضرات</span>
              <span class="font-black text-xl text-white">📚 {teacher.sessions_count}</span>
            </div>
          </div>
        </div>
      </div>

      <div>
        <h2 class="text-2xl font-black text-[#2a3c54] mb-6 border-r-8 border-[#6b8cce] pr-4">محاضرات الأستاذ</h2>
        {#if teacher.sessions.length === 0}
           <div class="text-center py-10 bg-white rounded-3xl border border-slate-200 text-slate-400 font-bold">لا توجد محاضرات حالياً.</div>
        
           {:else}
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {#each teacher.sessions as session}
              <div in:fade class="bg-white rounded-[2.5rem] p-6 shadow-sm border border-slate-100 hover:shadow-xl transition-all flex flex-col group">
                <div class="h-40 bg-slate-100 rounded-2xl overflow-hidden mb-4 relative">
                  <img src={`http://localhost:8000/pics/${session.cover}`} class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" alt="cover"/>
                  <div class="absolute top-3 right-3 bg-white/90 backdrop-blur px-3 py-1 rounded-xl text-[10px] font-black text-[#2a3c54]">⭐ {session.avg_rating}</div>
                </div>
                <h3 class="text-lg font-black text-[#2a3c54] mb-2 line-clamp-1">{session.title}</h3>
                <p class="text-xs text-slate-400 font-bold line-clamp-2 mb-6 flex-1">{session.description}</p>
                <button onclick={() => navigateToDetails(session.id)} class="w-full py-3 bg-[#eff3fa] text-[#6b8cce] rounded-xl font-black text-sm hover:bg-[#6b8cce] hover:text-white transition-all">التفاصيل 👁️</button>
              </div>
            {/each}
          </div>
        {/if}
      </div>

    </div>
  {/if}
</div>