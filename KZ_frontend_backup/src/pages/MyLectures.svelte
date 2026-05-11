<!--
  Knowledge Zakat — Teacher's "My Lectures" page.

  Lists every session the current teacher has authored, with quick
  actions (view details, edit, delete) and a modal that shows the
  enrolled students per session.

  BUG FIX (May 2026):
   - The cover image src was `http://127.0.0.1:8000/pics/${cover}`,
     hard-coded. That broke any time the backend was hosted on a
     different origin (LAN IP for phone testing, staging URL, etc.).
     Replaced with VITE_API_URL — same env variable used everywhere
     else in the frontend — so the build picks up the right host
     automatically.
-->

<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, scale } from 'svelte/transition';
  import api from '../lib/api';
  import { navigate } from '../lib/router';
  import { notify } from '../lib/notifications';
  import {
    Users,
    BookOpen,
    Plus,
    Trash2,
    Edit3,
    Eye,
    X,
    UserCircle,
  } from 'lucide-svelte';

  // ---- Local types --------------------------------------------------------
  interface LectureCard {
    id: number;
    title: string;
    description: string;
    date_time: string | null;
    duration: number;
    cover: string | null;
    enrollments_count: number;
  }

  interface EnrolledStudent {
    id: number;
    name: string;
    email: string;
    image: string | null;
  }

  interface ApprovedRow {
    session_id: number;
    student: EnrolledStudent;
  }

  // ---- Constants ----------------------------------------------------------
  // Base URL for the backend's static `/pics/` route. Single source of
  // truth — see lib/api.ts for the same fallback used by axios calls.
  const API_BASE: string =
    (import.meta as ImportMeta & { env?: Record<string, string> }).env?.VITE_API_URL
    ?? 'http://127.0.0.1:8000';

  function coverUrl(cover: string | null): string {
    if (!cover) return '';
    if (cover.startsWith('http://') || cover.startsWith('https://')) return cover;
    return `${API_BASE}/pics/${cover}`;
  }

  // ---- State --------------------------------------------------------------
  let lectures = $state<LectureCard[]>([]);
  let approved = $state<ApprovedRow[]>([]);
  let isLoading = $state(true);

  let pendingDelete = $state<LectureCard | null>(null);
  let isDeleting = $state(false);

  let showStudentsModal = $state(false);
  let modalStudents = $state<EnrolledStudent[]>([]);
  let modalSessionTitle = $state('');

  // ---- Data loading -------------------------------------------------------
  async function loadData(): Promise<void> {
    try {
      const [lectRes, approvedRes] = await Promise.all([
        api.get<LectureCard[]>('/me/sessions/'),
        api.get<ApprovedRow[]>('/teacher/enrollments/approved'),
      ]);
      lectures = lectRes.data ?? [];
      approved = approvedRes.data ?? [];
    } catch {
      notify.error('تعذّر تحميل المحاضرات والطلاب');
    } finally {
      isLoading = false;
    }
  }

  function openStudentsList(sessionId: number, title: string): void {
    modalStudents = approved
      .filter((r) => r.session_id === sessionId)
      .map((r) => r.student);
    modalSessionTitle = title;
    showStudentsModal = true;
  }

  function askDelete(lecture: LectureCard): void {
    if (lecture.enrollments_count > 0) {
      notify.warning('لا يمكن حذف محاضرة بها طلاب مسجّلون');
      return;
    }
    pendingDelete = lecture;
  }

  async function confirmDelete(): Promise<void> {
    if (!pendingDelete || isDeleting) return;
    isDeleting = true;
    try {
      await api.delete(`/sessions/${pendingDelete.id}`);
      lectures = lectures.filter((l) => l.id !== pendingDelete!.id);
      notify.success('تم حذف المحاضرة بنجاح');
    } catch {
      notify.error('تعذّر حذف المحاضرة');
    } finally {
      isDeleting = false;
      pendingDelete = null;
    }
  }

  onMount(loadData);
</script>

{#if showStudentsModal}
  <div
    in:fade
    class="fixed inset-0 z-[8000] flex items-center justify-center p-4 bg-[#2a3c54]/60 backdrop-blur-sm"
    dir="rtl"
    onclick={(e) => e.target === e.currentTarget && (showStudentsModal = false)}
    role="presentation"
  >
    <div
      in:scale={{ start: 0.92 }}
      class="bg-white rounded-[2.5rem] p-6 md:p-8 max-w-md w-full shadow-2xl flex flex-col max-h-[80vh]"
    >
      <div class="flex justify-between items-center mb-6 border-b pb-4">
        <h3 class="text-lg font-black text-[#2a3c54] line-clamp-1">الطلاب في: {modalSessionTitle}</h3>
        <button onclick={() => (showStudentsModal = false)} class="text-slate-400 hover:text-red-500" aria-label="إغلاق">
          <X size={24} />
        </button>
      </div>

      <div class="overflow-y-auto space-y-3 custom-scrollbar">
        {#if modalStudents.length === 0}
          <p class="text-center py-10 text-slate-400 font-bold text-sm">لا يوجد طلاب مقبولون في هذه الجلسة بعد</p>
        {:else}
          {#each modalStudents as student (student.id)}
            <div class="flex items-center gap-4 bg-slate-50 p-3 rounded-2xl border border-slate-100">
              <div class="w-10 h-10 rounded-xl bg-[#6b8cce] text-white flex items-center justify-center font-black overflow-hidden shrink-0">
                {#if student.image}
                  <img src={`data:image/jpeg;base64,${student.image}`} alt={student.name} class="w-full h-full object-cover" />
                {:else}
                  <UserCircle size={24} />
                {/if}
              </div>
              <div class="min-w-0 flex-1">
                <h4 class="font-black text-[#2a3c54] text-sm line-clamp-1">{student.name}</h4>
                <p class="text-[10px] text-slate-500 line-clamp-1">{student.email}</p>
              </div>
            </div>
          {/each}
        {/if}
      </div>
      <button onclick={() => (showStudentsModal = false)} class="mt-6 w-full py-3 bg-[#2a3c54] text-white rounded-xl font-black text-sm">إغلاق</button>
    </div>
  </div>
{/if}

{#if pendingDelete}
  <div in:fade class="fixed inset-0 z-[8000] flex items-center justify-center p-4 bg-[#2a3c54]/60 backdrop-blur-sm" dir="rtl">
    <div in:scale class="bg-white rounded-[2.5rem] p-8 max-w-md w-full text-center shadow-2xl">
      <div class="w-16 h-16 bg-red-50 text-red-500 rounded-full flex items-center justify-center mx-auto mb-6">
        <Trash2 size={32} />
      </div>
      <h3 class="text-xl font-black text-[#2a3c54] mb-2">تأكيد الحذف</h3>
      <p class="text-slate-500 font-bold mb-8 text-sm">هل أنت متأكد من حذف "{pendingDelete.title}"؟</p>
      <div class="flex gap-4">
        <button onclick={confirmDelete} disabled={isDeleting} class="flex-1 py-3 bg-red-500 text-white rounded-2xl font-black text-sm">
          {isDeleting ? 'جاري الحذف...' : 'حذف نهائي'}
        </button>
        <button onclick={() => (pendingDelete = null)} class="flex-1 py-3 bg-slate-100 text-slate-500 rounded-2xl font-black text-sm">إلغاء</button>
      </div>
    </div>
  </div>
{/if}

<div class="max-w-6xl mx-auto pb-12 text-right" dir="rtl">
  <header class="mb-8 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
    <div>
      <h1 class="text-3xl md:text-4xl font-black text-[#2a3c54]">إدارة محاضراتي</h1>
      <p class="text-slate-400 font-bold mt-2 italic">تحكم في محتواك الأكاديمي وتابع طلابك</p>
    </div>
    <button onclick={() => navigate('create_session')} class="flex items-center gap-2 px-6 py-3 bg-[#2a3c54] text-white rounded-2xl font-black text-sm shadow-md hover:scale-105 transition-all">
      <Plus size={18} /> محاضرة جديدة
    </button>
  </header>

  {#if isLoading}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {#each Array(3) as _}
        <div class="bg-white rounded-[2.5rem] h-80 animate-pulse"></div>
      {/each}
    </div>
  {:else if lectures.length === 0}
    <div class="bg-white rounded-[2.5rem] p-20 text-center border-2 border-dashed border-slate-200">
      <div class="flex justify-center text-slate-200 mb-6"><BookOpen size={64} /></div>
      <h2 class="text-xl font-black text-slate-400 mb-6">لم تنشر أي محاضرة حتى الآن</h2>
      <button onclick={() => navigate('create_session')} class="px-8 py-3 bg-[#2a3c54] text-white rounded-2xl font-black">ابدأ الآن</button>
    </div>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
      {#each lectures as lecture (lecture.id)}
        <article in:fade class="bg-white rounded-[2.5rem] shadow-md hover:shadow-2xl transition-all border border-slate-100 overflow-hidden flex flex-col group">
          <div class="h-48 bg-slate-100 relative overflow-hidden">
            {#if lecture.cover}
              <img src={coverUrl(lecture.cover)} alt={lecture.title} class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" />
            {:else}
              <div class="w-full h-full bg-gradient-to-br from-[#6b8cce] to-[#2a3c54] flex items-center justify-center text-white"><BookOpen size={48} /></div>
            {/if}
            <button onclick={() => openStudentsList(lecture.id, lecture.title)} class="absolute top-4 right-4 bg-white/95 px-4 py-2 rounded-2xl text-xs font-black text-[#2a3c54] flex items-center gap-2 shadow-sm hover:bg-[#6b8cce] hover:text-white transition-all">
              <Users size={14} /> {lecture.enrollments_count} طالب
            </button>
          </div>

          <div class="p-6 flex-1 flex flex-col">
            <h3 class="text-lg font-black text-[#2a3c54] mb-3 line-clamp-1">{lecture.title}</h3>
            <p class="text-slate-400 text-sm font-bold mb-6 line-clamp-2 italic flex-1">{lecture.description}</p>
            <div class="space-y-3">
              <button onclick={() => navigate('session_details', String(lecture.id))} class="w-full py-3 bg-[#6b8cce] text-white rounded-xl font-black text-sm flex items-center justify-center gap-2">
                <Eye size={16} /> عرض التفاصيل
              </button>
              <div class="flex gap-2">
                <button onclick={() => navigate('update_session', String(lecture.id))} class="flex-1 py-3 bg-[#eff3fa] text-[#2a3c54] rounded-xl font-black text-xs flex items-center justify-center gap-1">
                  <Edit3 size={14} /> تعديل
                </button>
                <button onclick={() => askDelete(lecture)} class="px-4 py-3 bg-red-50 text-red-500 rounded-xl font-black text-xs" aria-label="حذف">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          </div>
        </article>
      {/each}
    </div>
  {/if}
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar { width: 5px; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
</style>