<!--
  Knowledge Zakat — Public Teacher Profile Page.

  Shows a teacher's profile (name, bio, rating, avatar) plus a grid of
  all their published sessions. Used both by students browsing the
  teacher directory and by guests checking out a teacher before
  registering.

  BUG FIXES (May 2026):
   1. Replaced hard-coded `http://localhost:8000/pics/...` URLs with the
      VITE_API_URL env variable (falls back to 127.0.0.1:8000). The
      hard-coded version broke as soon as the backend was hosted on any
      other origin, or accessed from a phone on the LAN.
   2. Replaced the legacy `currentPage.set(...)` calls with the new
      `navigate(...)` router API. The old code didn't update the URL
      hash, so a browser refresh on this page dumped the user back at
      Home.
   3. Migrated to <script lang="ts"> for consistency with the rest of
      the migrated frontend, and typed the `teacher` payload.
-->

<script lang="ts">
  import { onMount } from 'svelte';
  import { fade } from 'svelte/transition';

  import api from '../lib/api';
  import { navigate, route } from '../lib/router';
  import { notify } from '../lib/notifications';

  // ---- Local types --------------------------------------------------------
  interface TeacherSession {
    id: number;
    title: string;
    description: string;
    cover: string | null;
    avg_rating: number;
  }

  interface TeacherProfile {
    id: number;
    name: string;
    bio: string;
    image: string | null;
    avg_rating: number;
    sessions_count: number;
    sessions: TeacherSession[];
  }

  // ---- Props / route param ------------------------------------------------
  // The teacher id comes from the URL hash (#/teacher_view/42), parsed
  // by router.ts into `route.param`. We accept an explicit prop as well
  // so the page is still drivable from a parent component in tests.
  let { teacherId: propTeacherId = null }: { teacherId?: number | null } = $props();
  let teacherId = $derived(propTeacherId ?? ($route.param ? parseInt($route.param, 10) : null));

  // ---- State --------------------------------------------------------------
  let teacher = $state<TeacherProfile | null>(null);
  let isLoading = $state(true);

  // ---- Helpers ------------------------------------------------------------
  // Centralised base URL — same fallback as lib/api.ts. Reading it once
  // here means swapping the deploy host requires editing only `.env`.
  const API_BASE: string =
    (import.meta as ImportMeta & { env?: Record<string, string> }).env?.VITE_API_URL
    ?? 'http://127.0.0.1:8000';

  function coverUrl(cover: string | null): string {
    if (!cover) return '';
    // Tolerate both absolute and bare-filename values from the backend.
    if (cover.startsWith('http://') || cover.startsWith('https://')) return cover;
    return `${API_BASE}/pics/${cover}`;
  }

  function navigateToDetails(sessionId: number): void {
    navigate('session_details', String(sessionId));
  }

  function goHome(): void {
    navigate('home');
  }

  // ---- Lifecycle ----------------------------------------------------------
  onMount(async () => {
    if (!teacherId) {
      notify.error('لم يتم تحديد الأستاذ المطلوب');
      navigate('home', null, true);
      return;
    }
    try {
      const res = await api.get<TeacherProfile>(`/teachers/${teacherId}/profile`);
      teacher = res.data;
    } catch {
      notify.error('تعذّر تحميل بيانات الأستاذ');
    } finally {
      isLoading = false;
    }
  });
</script>

<div class="min-h-screen bg-slate-50 py-10 px-4 md:px-10 font-sans text-right" dir="rtl">

  <div class="max-w-5xl mx-auto mb-6 flex justify-start">
    <button
      onclick={goHome}
      class="flex items-center gap-2 bg-white px-6 py-3 rounded-2xl shadow-sm text-[#4a6583] font-black hover:bg-[#6b8cce] hover:text-white transition-all border border-slate-200"
    >
      <span>رجوع للرئيسية</span>
      <svg class="w-5 h-5 rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
      </svg>
    </button>
  </div>

  {#if isLoading}
    <div class="text-center mt-20 text-[#6b8cce] font-black animate-pulse text-xl">
      جاري تحميل بروفايل الأستاذ...
    </div>
  {:else if teacher}
    <div class="max-w-5xl mx-auto space-y-8">

      <!-- Profile header -->
      <div class="bg-gradient-to-bl from-[#2a3c54] to-[#4a6583] p-10 rounded-[3rem] shadow-lg text-white flex flex-col md:flex-row gap-8 items-center md:items-start relative overflow-hidden">
        <div class="absolute top-0 left-0 w-64 h-64 bg-white opacity-5 rounded-full -ml-20 -mt-20 blur-3xl"></div>

        <div class="w-40 h-40 bg-slate-200 rounded-full overflow-hidden shrink-0 border-4 border-white/20 shadow-2xl flex items-center justify-center text-6xl text-[#6b8cce] font-black z-10">
          {#if teacher.image}
            <img src={teacher.image} alt={teacher.name} class="w-full h-full object-cover" />
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
              <span class="font-black text-xl text-amber-400">
                ⭐ {teacher.avg_rating > 0 ? teacher.avg_rating : 'جديد'}
              </span>
            </div>
            <div class="bg-white/10 px-5 py-2.5 rounded-2xl border border-white/10 backdrop-blur-md">
              <span class="block text-xs font-bold text-slate-300 mb-1">عدد المحاضرات</span>
              <span class="font-black text-xl text-white">📚 {teacher.sessions_count}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Sessions grid -->
      <div>
        <h2 class="text-2xl font-black text-[#2a3c54] mb-6 border-r-8 border-[#6b8cce] pr-4">
          محاضرات الأستاذ
        </h2>

        {#if teacher.sessions.length === 0}
          <div class="text-center py-10 bg-white rounded-3xl border border-slate-200 text-slate-400 font-bold">
            لا توجد محاضرات حالياً.
          </div>
        {:else}
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {#each teacher.sessions as session (session.id)}
              <div in:fade class="bg-white rounded-[2.5rem] p-6 shadow-sm border border-slate-100 hover:shadow-xl transition-all flex flex-col group">
                <div class="h-40 bg-slate-100 rounded-2xl overflow-hidden mb-4 relative">
                  {#if session.cover}
                    <img
                      src={coverUrl(session.cover)}
                      class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                      alt={session.title}
                    />
                  {:else}
                    <div class="w-full h-full bg-gradient-to-br from-[#6b8cce] to-[#2a3c54]"></div>
                  {/if}
                  <div class="absolute top-3 right-3 bg-white/90 backdrop-blur px-3 py-1 rounded-xl text-[10px] font-black text-[#2a3c54]">
                    ⭐ {session.avg_rating}
                  </div>
                </div>
                <h3 class="text-lg font-black text-[#2a3c54] mb-2 line-clamp-1">{session.title}</h3>
                <p class="text-xs text-slate-400 font-bold line-clamp-2 mb-6 flex-1">{session.description}</p>
                <button
                  onclick={() => navigateToDetails(session.id)}
                  class="w-full py-3 bg-[#eff3fa] text-[#6b8cce] rounded-xl font-black text-sm hover:bg-[#6b8cce] hover:text-white transition-all"
                >
                  التفاصيل 👁️
                </button>
              </div>
            {/each}
          </div>
        {/if}
      </div>

    </div>
  {/if}
</div>