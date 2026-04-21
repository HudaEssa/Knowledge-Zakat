<script>
  import { onMount } from 'svelte';
  import { fade, scale } from 'svelte/transition';
  import api from '../lib/api'; 
  import { selectedSessionId, currentPage, selectedTeacherId } from '../lib/stores'; 

  let sessions = $state([]);
  let categories = $state([]);
  let allTeachers = $state([]); 
  let searchTerm = $state("");
  let selectedCatId = $state(null);
  let isLoading = $state(true);

  let catPage = $state(0);
  let sessPage = $state(0);
  let teacherPage = $state(0);
  const itemsPerPage = 6; 
  const teachersPerPage = 4;

  async function loadData() {
    try {
      isLoading = true;
      const [sRes, cRes, tRes] = await Promise.all([
        api.get('/sessions/').catch(() => ({data: []})), 
        api.get('/categories/').catch(() => ({data: []})),
        api.get('/users/').catch(() => ({data: []}))
      ]);
      
      const rawSessions = sRes.data || [];
      const groups = {};
      rawSessions.forEach(s => {
        if (!s.title) return;
        let courseTitle = s.title.includes(' - ') ? s.title.split(' - ')[0].trim() : s.title.trim();
        let groupKey = `${courseTitle}-${s.teacher_name}`;
        if (!groups[groupKey]) {
          groups[groupKey] = {
            id: s.id, course_title: courseTitle, description: s.description,
            display_cover: s.cover_image_url, teacher_name: s.teacher_name,
            teacher_id: s.user_id, categories: s.categories || [], session_count: 0
          };
        }
        groups[groupKey].session_count += 1;
      });
      sessions = Object.values(groups).sort((a, b) => a.course_title.localeCompare(b.course_title, 'ar'));
      categories = cRes.data || [];
      allTeachers = (tRes.data || []).filter(u => u.roles?.some(r => r.role_name === 'teacher'));
    } catch (e) { console.error(e); }
    finally { isLoading = false; }
  }

  let filteredSessions = $derived(
    sessions.filter(s => 
      s.course_title.toLowerCase().includes(searchTerm.toLowerCase()) && 
      (selectedCatId === null || s.categories.some(c => c.id === selectedCatId))
    )
  );

  let visibleCats = $derived(categories.slice(catPage * itemsPerPage, (catPage + 1) * itemsPerPage));
  let visibleSessions = $derived(filteredSessions.slice(sessPage * itemsPerPage, (sessPage + 1) * itemsPerPage));
  let visibleTeachers = $derived(allTeachers.slice(teacherPage * teachersPerPage, (teacherPage + 1) * teachersPerPage));
  let totalSessPages = $derived(Math.ceil(filteredSessions.length / itemsPerPage));

  onMount(loadData);
</script>

<div class="max-w-7xl mx-auto px-4 md:px-8 py-10 space-y-20 text-right" dir="rtl">
  
  <section class="bg-white p-8 md:p-12 rounded-[3.5rem] shadow-sm border border-slate-100 flex flex-col items-center gap-10">
    <div class="relative w-full max-w-4xl">
      <input bind:value={searchTerm} oninput={() => sessPage = 0} placeholder="عن ماذا تود أن تبحث في زكاة العلم؟" 
             class="w-full bg-slate-50 border-2 border-transparent focus:border-[#6b8cce] focus:bg-white px-16 py-6 rounded-[2.5rem] outline-none font-bold text-xl shadow-inner transition-all text-right">
      <span class="absolute right-6 top-1/2 -translate-y-1/2 text-3xl opacity-20">🔍</span>
    </div>

    <div class="flex items-center gap-6">
      <button disabled={catPage === 0} onclick={() => catPage--} class="w-12 h-12 rounded-2xl bg-white border border-slate-200 text-[#2a3c54] hover:bg-[#6b8cce] hover:text-white disabled:opacity-20 transition-all font-black shadow-sm">{'<'}</button>
      <div class="flex gap-3 p-2 bg-slate-100/50 rounded-[2rem] border border-slate-100">
        <button onclick={() => { selectedSessionId.set(s.id); currentPage.set('session_view'); }}
                class="px-8 py-3 rounded-2xl text-sm font-black transition-all {selectedCatId === null ? 'bg-[#2a3c54] text-white shadow-lg' : 'text-slate-400 hover:text-[#2a3c54]'}"> الكل </button>
        {#each visibleCats as cat}
          <button onclick={() => { selectedCatId = cat.id; sessPage = 0; }} 
                  class="px-8 py-3 rounded-2xl text-sm font-black transition-all {selectedCatId === cat.id ? 'bg-[#2a3c54] text-white shadow-lg' : 'text-slate-400 hover:text-[#2a3c54]'}"> {cat.category_name} </button>
        {/each}
      </div>
      <button disabled={(catPage + 1) * itemsPerPage >= categories.length} onclick={() => catPage++} 
              class="w-12 h-12 rounded-2xl bg-white border border-slate-200 text-[#2a3c54] hover:bg-[#6b8cce] hover:text-white disabled:opacity-20 transition-all font-black shadow-sm">{'>'}</button>
    </div>
  </section>

  {#if isLoading}
    <div class="py-40 text-center flex flex-col items-center gap-6">
        <div class="w-16 h-16 border-8 border-[#6b8cce] border-t-transparent rounded-full animate-spin"></div>
        <p class="text-slate-400 font-black animate-pulse text-2xl italic">جاري تحضير محفل العلم...</p>
    </div>
  {:else}
    
    <section class="space-y-12" in:fade>
        <h2 class="text-4xl font-black text-[#2a3c54] border-r-[12px] border-[#6b8cce] pr-6">استكشف المحاضرات العلمية 📚</h2>
        <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-12">
          {#each visibleSessions as s (s.id + s.course_title)}
            <div class="group bg-white rounded-[3.5rem] border border-slate-50 overflow-hidden flex flex-col hover:shadow-2xl transition-all duration-500">
              <div class="h-60 relative overflow-hidden bg-slate-100">
                <img src={`http://127.0.0.1:8000/pics/${s.display_cover}`} 
                     alt={s.course_title} 
                     class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                     onerror={(e) => { e.currentTarget.src = 'https://via.placeholder.com/600x400?text=Knowledge+Zakat' }} />
                <div class="absolute top-5 right-6">
                  <span class="bg-white/95 backdrop-blur-sm text-[#2a3c54] text-xs font-black px-6 py-2.5 rounded-2xl shadow-xl border border-white">تتضمن {s.session_count} جلسات</span>
                </div>
              </div>

              <div class="p-10 flex-1 flex flex-col justify-between">
                <div>
                  <h3 class="text-2xl font-black text-[#2a3c54] mb-4 line-clamp-1">{s.course_title}</h3>
                  <p class="text-sm text-slate-400 font-medium line-clamp-3 leading-relaxed mb-8 italic">{s.description || 'لا يوجد وصف متاح حالياً.'}</p>
                </div>
                
                <div class="pt-8 border-t border-slate-50 flex justify-between items-center">
                  <div class="flex items-center gap-4">
                    <div class="w-14 h-14 rounded-2xl bg-[#eff3fa] flex items-center justify-center overflow-hidden border-2 border-white shadow-sm">
    <img src={`http://127.0.0.1:8000/users/${s.teacher_id}/profile_image`} 
         alt="teacher" 
         class="w-full h-full object-cover"
         onerror={(e) => { 
             e.currentTarget.src = `https://ui-avatars.com/api/?name=${s.teacher_name}&background=eff3fa&color=2a3c54`;
         }} />
</div>
                    <div class="flex flex-col text-right">
                        <span class="text-[10px] text-slate-300 font-black uppercase">المحاضر</span>
                        <span class="text-base font-black text-[#2a3c54]">{s.teacher_name}</span>
                    </div>
                  </div>
                  <button onclick={() => { selectedSessionId.set(s.course_title); currentPage.set('session_view'); }} 
                          class="w-16 h-16 rounded-[1.5rem] bg-[#2a3c54] text-white font-black text-3xl hover:bg-[#6b8cce] hover:scale-110 transition-all shadow-lg"> ← </button>
                </div>
              </div>
            </div>
          {/each}
        </div>

        {#if totalSessPages > 1}
          <div class="flex justify-center items-center gap-6 pt-10">
            <button disabled={sessPage === 0} onclick={() => { sessPage--; window.scrollTo({top: 0, behavior: 'smooth'}); }} 
                    class="px-10 py-4 bg-white rounded-2xl font-black text-sm shadow-sm border border-slate-100 disabled:opacity-20 transition-all">السابق</button>
            <div class="flex gap-3">
              {#each Array(totalSessPages) as _, i}
                <button onclick={() => { sessPage = i; window.scrollTo({top: 0, behavior: 'smooth'}); }} 
                        class="w-12 h-12 rounded-2xl font-black transition-all shadow-sm {sessPage === i ? 'bg-[#2a3c54] text-white scale-110' : 'bg-white text-slate-300'}">{i+1}</button>
              {/each}
            </div>
            <button disabled={(sessPage + 1) >= totalSessPages} onclick={() => { sessPage++; window.scrollTo({top: 0, behavior: 'smooth'}); }} 
                    class="px-10 py-4 bg-[#2a3c54] text-white rounded-2xl font-black text-sm shadow-xl">التالي</button>
          </div>
        {/if}
    </section>

    <section class="space-y-10 bg-[#eff3fa]/30 p-12 rounded-[4rem] border border-white/50" in:fade>
        <div class="flex justify-between items-center px-4">
            <div class="space-y-2 text-right">
                <h2 class="text-4xl font-black text-[#2a3c54]">المعلمون في المنصة 👨‍🏫</h2>
                <p class="text-slate-400 font-bold italic">نخبة من الأساتذة والخبراء المساهمين في زكاة العلم</p>
            </div>
            <div class="flex gap-4">
                <button disabled={teacherPage === 0} onclick={() => teacherPage--} class="w-12 h-12 rounded-2xl bg-white border border-slate-100 shadow-sm disabled:opacity-30 hover:bg-[#6b8cce] hover:text-white transition-all">←</button>
                <button disabled={(teacherPage + 1) * teachersPerPage >= allTeachers.length} onclick={() => teacherPage++} class="w-12 h-12 rounded-2xl bg-white border border-slate-100 shadow-sm disabled:opacity-30 hover:bg-[#6b8cce] hover:text-white transition-all">→</button>
            </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {#each visibleTeachers as teacher}
                <div in:scale class="bg-white p-8 rounded-[3.5rem] border border-slate-50 shadow-sm hover:shadow-2xl transition-all text-center group relative overflow-hidden">
                    <div class="w-32 h-32 mx-auto mb-6 rounded-[2.5rem] overflow-hidden border-4 border-[#eff3fa] shadow-inner group-hover:scale-110 transition-transform duration-500 bg-slate-100">
                        <img src={`http://127.0.0.1:8000/users/${teacher.id}/profile_image`} 
                             alt={teacher.firstname} 
                             class="w-full h-full object-cover"
                             onerror={(e) => { e.currentTarget.src = `https://ui-avatars.com/api/?name=${teacher.firstname}+${teacher.lastname}&background=eff3fa&color=2a3c54` }} />
                    </div>
                    <h4 class="font-black text-[#2a3c54] text-2xl">{teacher.firstname} {teacher.lastname}</h4>
                    <p class="text-xs text-slate-400 font-bold mt-4 line-clamp-2 italic leading-relaxed h-10">{teacher.bio || 'معلم شغوف بنشر العلم.'}</p>
                   
                </div>
            {/each}
        </div>
    </section>

  {/if}
</div>