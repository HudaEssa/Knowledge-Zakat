<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, scale, fly } from 'svelte/transition';
  import api from '../lib/api';
  import { route, navigate } from '../lib/router';
  import { notify } from '../lib/notifications';
  
  // 👈 التأكد من استيراد كل الأيقونات الضرورية
  import { 
    ChevronRight, ChevronLeft, Star, BookOpen, 
    UserCircle, Layers, Users, ShieldCheck, PlayCircle 
  } from 'lucide-svelte';

  // ---- Local types --------------------------------------------------------
  interface TeacherSessionStat {
    id: number;
    title: string;
    description: string | null;
    cover: string | null;
    avg_rating: number;
  }

  interface TeacherProfilePayload {
    id: number;
    name: string;
    bio: string;
    image: string | null;
    avg_rating: number;
    sessions_count: number;
    sessions: TeacherSessionStat[];
  }

  // ---- State --------------------------------------------------------------
  let teacher = $state<TeacherProfilePayload | null>(null);
  let isLoading = $state(true);

  let teacherId = $derived.by(() => {
    const raw = $route.param;
    if (!raw) return null;
    const n = Number(raw);
    return Number.isFinite(n) ? n : null;
  });

  async function loadProfile(): Promise<void> {
    if (!teacherId) {
      notify.error('لم يتم تحديد المعلم المطلوب');
      navigate('home', null, true);
      return;
    }

    isLoading = true;
    try {
      const res = await api.get<TeacherProfilePayload>(
        `/teachers/${teacherId}/profile`,
      );
      teacher = res.data;
    } catch {
      notify.error('تعذّر تحميل ملف المعلم');
      teacher = null;
    } finally {
      isLoading = false;
    }
  }

  function openCourseFromSession(sessionTitle: string): void {
    const coursePrefix = sessionTitle.includes(' - ')
      ? sessionTitle.split(' - ')[0].trim()
      : sessionTitle.trim();
    navigate('session_view', coursePrefix);
  }

  function openSessionDetails(sessionId: number): void {
    navigate('session_details', sessionId);
  }

  function hideBrokenImg(e: Event) {
    const img = e.currentTarget as HTMLImageElement;
    img.style.display = 'none';
    const fallback = img.nextElementSibling as HTMLElement | null;
    if (fallback) fallback.style.display = 'flex';
  }

  onMount(loadProfile);
</script>

<div class="min-h-screen bg-slate-50 text-right pb-12 md:pb-20 font-sans" dir="rtl">
  {#if isLoading}
    <div class="flex flex-col items-center justify-center h-[80vh] gap-6" in:fade>
      <div class="w-14 h-14 md:w-16 md:h-16 border-8 border-[#6b8cce] border-t-transparent rounded-full animate-spin"></div>
      <p class="font-black text-[#6b8cce] text-lg md:text-2xl animate-pulse italic">
        جاري تحميل السيرة العلمية...
      </p>
    </div>
  {:else if !teacher}
    <div class="flex flex-col items-center justify-center h-[80vh] gap-6 px-4 text-center">
      <div class="text-6xl opacity-40">🚫</div>
      <p class="text-slate-500 font-black text-xl">لم يتم العثور على هذا المعلم</p>
      <button onclick={() => navigate('home')} class="px-8 py-3 bg-[#2a3c54] text-white rounded-2xl font-black text-sm hover:bg-[#1a2a3a] transition-all shadow-md">
        العودة للرئيسية
      </button>
    </div>
  {:else}
    
    <div class="max-w-5xl mx-auto pt-6 px-4 mb-4 relative z-20">
      <button onclick={() => window.history.back()} class="flex items-center gap-2 bg-white px-4 py-2 rounded-2xl shadow-sm text-[#4a6583] font-black hover:bg-[#6b8cce] hover:text-white transition-all border border-slate-200 text-sm w-fit">
        <ChevronRight size={18} /> رجوع
      </button>
    </div>

    <main class="max-w-5xl mx-auto px-4 pb-16 relative z-10">
      <div class="relative mt-2 mb-16" in:fly={{ y: 20, duration: 600 }}>
        
        <div class="h-48 md:h-64 w-full rounded-[2.5rem] bg-gradient-to-r from-[#2a3c54] to-[#6b8cce] overflow-hidden relative shadow-lg">
          <div class="absolute inset-0 opacity-10" style="background-image: radial-gradient(circle at 2px 2px, white 1px, transparent 0); background-size: 24px 24px;"></div>
        </div>

        <div class="absolute -bottom-16 left-0 right-0 px-6 flex justify-center">
          <div class="bg-white rounded-[2rem] p-6 shadow-xl border border-slate-100 flex flex-col md:flex-row items-center gap-6 w-full max-w-4xl">
            
            <div class="w-32 h-32 md:w-36 md:h-36 rounded-[1.5rem] bg-slate-50 border-[6px] border-white shadow-md overflow-hidden shrink-0 -mt-20 md:mt-0 relative flex items-center justify-center">
              {#if teacher.image && teacher.image !== "data:image/jpeg;base64,null"}
                <img src={teacher.image} alt={teacher.name} class="w-full h-full object-cover" onerror={hideBrokenImg} />
                <div class="absolute inset-0 bg-slate-50 hidden flex-col items-center justify-center"><UserCircle size={48} class="text-slate-300" /></div>
              {:else}
                <div class="w-full h-full bg-[#6b8cce] flex items-center justify-center text-white text-5xl font-black">
                  {teacher.name.charAt(0).toUpperCase()}
                </div>
              {/if}
            </div>

            <div class="flex-1 text-center md:text-right">
              <div class="flex items-center justify-center md:justify-start gap-2 mb-1">
                <h1 class="text-2xl md:text-3xl font-black text-[#2a3c54]">{teacher.name}</h1>
                <span title="محاضر معتمد"><ShieldCheck size={20} class="text-emerald-500" /></span>
              </div>
              <p class="text-xs font-black text-[#6b8cce] mb-3 uppercase tracking-wide">محاضر في زكاة العلم</p>
              <p class="text-sm text-slate-500 font-medium leading-relaxed max-w-2xl">{teacher.bio || 'معلم خبير مكرّس لنشر المعرفة في مجتمع زكاة العلم.'}</p>
            </div>

            <div class="flex md:flex-col gap-4 md:gap-3 shrink-0 border-t md:border-t-0 md:border-r border-slate-100 pt-4 md:pt-0 md:pr-6 w-full md:w-auto justify-center">
              <div class="flex items-center justify-center md:justify-start gap-3 bg-amber-50 px-5 py-3 rounded-2xl border border-amber-100 w-full md:w-44">
                <Star size={24} class="fill-amber-500 text-amber-500 shrink-0" />
                <div class="text-right">
                  <div class="text-lg font-black text-amber-700 leading-none">{teacher.avg_rating > 0 ? teacher.avg_rating.toFixed(1) : 'جديد'}</div>
                  <div class="text-[10px] font-bold text-amber-600/70 mt-1">متوسط التقييم</div>
                </div>
              </div>
              <div class="flex items-center justify-center md:justify-start gap-3 bg-[#eff3fa] px-5 py-3 rounded-2xl border border-[#dbe7fa] w-full md:w-44">
                <Layers size={24} class="text-[#6b8cce] shrink-0" />
                <div class="text-right">
                  <div class="text-lg font-black text-[#2a3c54] leading-none">{teacher.sessions_count}</div>
                  <div class="text-[10px] font-bold text-[#6b8cce]/80 mt-1">دورة علمية</div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>

      <div class="mt-28 pt-8" in:fade={{ delay: 300 }}>
        <h3 class="flex items-center gap-2 text-2xl font-black text-[#2a3c54] mb-8 border-r-4 border-[#6b8cce] pr-4">
          <PlayCircle size={26} class="text-[#6b8cce]" /> محاضرات الأستاذ
        </h3>

        {#if teacher.sessions.length === 0}
          <div class="bg-white rounded-3xl p-10 text-center border-2 border-dashed border-slate-200 shadow-sm flex flex-col items-center gap-3">
            <BookOpen size={48} class="text-slate-300" />
            <p class="text-slate-500 font-bold text-lg">لم يقم الأستاذ بنشر أي محاضرات بعد.</p>
          </div>
        {:else}
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {#each teacher.sessions as s, i}
              <button 
                onclick={() => openCourseFromSession(s.title)} 
                class="bg-white rounded-[2rem] border border-slate-100 overflow-hidden shadow-sm hover:shadow-xl hover:-translate-y-2 transition-all duration-300 text-right group flex flex-col w-full"
                in:fly={{ y: 20, delay: i * 50 }}
              >
                <div class="h-44 w-full bg-slate-100 relative overflow-hidden shrink-0 block">
                  {#if s.cover}
                    <img src={`http://127.0.0.1:8000/pics/${s.cover}`} alt={s.title} class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" />
                  {:else}
                    <div class="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-[#6b8cce] to-[#2a3c54] text-white"><BookOpen size={40} opacity={0.5} /></div>
                  {/if}
                  <div class="absolute top-3 right-3 bg-white/95 backdrop-blur text-[#2a3c54] text-[11px] font-black px-3 py-1.5 rounded-full flex items-center gap-1.5 shadow-sm">
                    <Star size={14} class="fill-amber-400 text-amber-400" /> {s.avg_rating > 0 ? s.avg_rating.toFixed(1) : 'جديد'}
                  </div>
                </div>
                
                <div class="p-6 flex-1 flex flex-col w-full">
                  <h4 class="font-black text-[#2a3c54] text-lg mb-2 line-clamp-1 group-hover:text-[#6b8cce] transition-colors">{s.title}</h4>
                  <p class="text-slate-500 text-sm leading-relaxed font-medium line-clamp-2 mb-6 flex-1">{s.description || 'لا يوجد وصف متاح.'}</p>
                  
                  <div class="pt-4 border-t border-slate-100 text-xs font-black text-[#6b8cce] flex items-center justify-between group-hover:px-2 transition-all">
                    <span>شارك في الدورة</span>
                    <ChevronLeft size={16} strokeWidth={3} />
                  </div>
                </div>
              </button>
            {/each}
          </div>
        {/if}
      </div>
    </main>
  {/if}
</div>

<style>
  /* تم إزالة الاستايلات المكررة لأنها موجودة كـ Tailwind Classes في الـ HTML */
</style>