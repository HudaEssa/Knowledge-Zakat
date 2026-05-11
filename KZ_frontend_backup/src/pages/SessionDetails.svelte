<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, slide, scale, fly } from 'svelte/transition';
  import api from '../lib/api';
  import { user, hasRole, token } from '../lib/stores';
  import { route, navigate } from '../lib/router';
  import { notify } from '../lib/notifications';
  import { authPrompt } from '../lib/authPrompt';
  import {
    Pencil, Trash2, Check, X, Search, BookOpen, Star,
    Link, MessageSquare, CornerDownLeft, ThumbsUp,
    Heart, Flame, Lightbulb, Loader2, ArrowRight, UserCircle,
    ChevronLeft, Lock, LogIn, UserPlus, Users, ShieldAlert, CheckCircle2
  } from 'lucide-svelte';

  // ---- Local types --------------------------------------------------------
  interface Comment {
    id: number;
    content: string;
    created_at: string;
    user_id: number | null;
    user_name: string;
    user_image: string | null;
    replies: Comment[];
  }

  interface SessionMeta {
    id: number;
    title: string;
    description: string | null;
    cover: string | null;
    display_cover: string | null;
    meeting_link: string | null;
    student_limit: number | null; // 👈 مضاف
  }

  interface SessionDetailsPayload {
    session: SessionMeta;
    teacher_id: number | null;
    teacher_name: string;
    avg_session_rating: number;
    avg_teacher_rating: number;
    ratings_count: number;
    comments: Comment[];
    accepted_count: number; // 👈 مضاف من الباك إند
  }

  // ---- State --------------------------------------------------------------
  let details = $state<SessionDetailsPayload | null>(null);
  let isLoading = $state(true);
  let isEnrolling = $state(false);

  let newComment = $state('');
  let replyContent = $state('');
  let replyingTo = $state<number | null>(null);

  let editingCommentId = $state<number | null>(null);
  let editContent = $state('');
  let commentToDelete = $state<number | null>(null);
  let isDeletingComment = $state(false);

  let sessionRate = $state(0);
  let teacherRate = $state(0);
  let hasRated = $state(false);
  let isPostingComment = $state(false);
  let isPostingRating = $state(false);

  let isEnrolled = $state(false);
  let enrollmentChecked = $state(false);

  let sessionId = $derived.by(() => {
    const raw = $route.param;
    if (!raw) return null;
    const n = Number(raw);
    return Number.isFinite(n) ? n : null;
  });

  // ---- Logic الذكي للسعة --------------------------------------------------
  let occupancyRate = $derived.by(() => {
    if (!details?.session.student_limit || !details.accepted_count) return 0;
    return Math.round((details.accepted_count / details.session.student_limit) * 100);
  });

  let isFull = $derived.by(() => {
    if (!details?.session.student_limit) return false;
    return details.accepted_count >= details.session.student_limit;
  });

  let isGuest = $derived(!$token);
  let isStudent = $derived(
    !isGuest && !hasRole($user, 'teacher') && !hasRole($user, 'admin'),
  );

  // ---- Loaders & Actions --------------------------------------------------
  async function loadDetails(): Promise<void> {
    if (!sessionId) return;
    isLoading = true;
    try {
      const res = await api.get<SessionDetailsPayload>(`/sessions/${sessionId}/details`);
      details = res.data;
    } catch { notify.error('تعذّر تحميل البيانات'); }
    finally { isLoading = false; }
  }

  async function verifyEnrollment(): Promise<void> {
    if (isGuest || !isStudent || !sessionId) {
      enrollmentChecked = true;
      return;
    }
    try {
      const res = await api.get('/enrollments/my-sessions/');
      isEnrolled = res.data.some((s: any) => s.id === sessionId || s.session_id === sessionId);
    } catch { isEnrolled = false; }
    finally { enrollmentChecked = true; }
  }

  // دالة طلب الانضمام
  async function handleEnroll() {
    if (isGuest) {
      authPrompt.show('سجّل دخولك لتتمكن من الانضمام للمحاضرة ✨');
      return;
    }
    if (isFull) {
      notify.warning("المحاضرة مكتملة العدد حالياً 🔒");
      return;
    }
    isEnrolling = true;
    try {
      await api.post(`/enrollments/join/${sessionId}`);
      notify.success("تم إرسال طلب الانضمام، انتظر موافقة المعلم ✅");
      await verifyEnrollment();
    } catch (err: any) {
      notify.error(err.response?.data?.detail || "حدث خطأ أثناء الطلب");
    } finally { isEnrolling = false; }
  }

  async function refreshComments(): Promise<void> {
    if (!sessionId) return;
    try {
      const res = await api.get<SessionDetailsPayload>(`/sessions/${sessionId}/details`);
      if (details) details.comments = res.data.comments;
    } catch { }
  }

  async function submitComment(parentId: number | null = null): Promise<void> {
    if (isGuest) {
      authPrompt.show('سجّل دخولك للمشاركة بالنقاش والتعليقات');
      return;
    }
    if (!sessionId || isPostingComment) return;
    const content = parentId ? replyContent : newComment;
    if (!content.trim()) return;
    isPostingComment = true;
    try {
      await api.post('/sessions/comments/', { session_id: sessionId, content, parent_id: parentId });
      newComment = ''; replyContent = ''; replyingTo = null;
      await refreshComments();
    } catch { notify.error('فشل الإرسال'); }
    finally { isPostingComment = false; }
  }

  function requestDelete(id: number) { commentToDelete = id; }

  async function executeDelete() {
    if (commentToDelete === null || isDeletingComment) return;
    isDeletingComment = true;
    try {
      await api.delete(`/sessions/comments/${commentToDelete}`);
      notify.success('تم الحذف بنجاح');
      await refreshComments();
    } catch { notify.error('فشل الحذف'); }
    finally { isDeletingComment = false; commentToDelete = null; }
  }

  async function handleEditSave(id: number) {
    if (!editContent.trim()) return;
    try {
      await api.put(`/sessions/comments/${id}`, { content: editContent });
      editingCommentId = null;
      notify.success('تم التعديل بنجاح');
      await refreshComments();
    } catch { notify.error('فشل التعديل'); }
  }

  async function submitRating(): Promise<void> {
    if (isGuest) {
      authPrompt.show('سجّل دخولك لتتمكن من تقييم المحاضرة');
      return;
    }
    if (sessionRate === 0 || teacherRate === 0) {
      notify.warning('يرجى تقييم كل من المحتوى والمعلم');
      return;
    }
    if (!sessionId || isPostingRating) return;
    isPostingRating = true;
    try {
      await api.post('/sessions/ratings/', {
        session_id: sessionId,
        teacher_id: details?.teacher_id,
        session_rate: sessionRate,
        teacher_rate: teacherRate,
      });
      hasRated = true;
      notify.success('شكراً لتقييمك!');
      await loadDetails();
    } catch (err: any) {
      notify.error(err.response?.data?.detail || 'فشل إرسال التقييم');
    }
    finally { isPostingRating = false; }
  }

  function addEmoji(emoji: string): void {
    if (replyingTo) replyContent += emoji;
    else newComment += emoji;
  }

  function formatDate(iso: string): string {
    if (!iso) return 'الآن';
    try {
      const d = new Date(iso);
      return d.toLocaleString('ar-IQ', { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' });
    } catch { return 'الآن'; }
  }

  function goBack(): void { window.history.back(); }
  function goLogin(): void { navigate('login', null, true); }
  function goRegister(): void { navigate('register', null, true); }

  onMount(() => {
    loadDetails();
    verifyEnrollment();
  });
</script>

{#if commentToDelete !== null}
  <div in:fade out:fade class="fixed inset-0 z-[8000] flex items-center justify-center p-4 bg-[#2a3c54]/60 backdrop-blur-sm" dir="rtl" onclick={(e) => { if (e.target === e.currentTarget && !isDeletingComment) commentToDelete = null; }} role="presentation">
    <div in:scale={{ start: 0.92, duration: 250 }} class="bg-white rounded-[2.5rem] p-8 md:p-10 max-w-md w-full text-center shadow-2xl">
      <div class="w-16 h-16 bg-red-50 text-red-500 rounded-full flex items-center justify-center mx-auto mb-6"><Trash2 size={32} /></div>
      <h3 class="text-xl md:text-2xl font-black text-[#2a3c54] mb-2">تأكيد الحذف</h3>
      <p class="text-slate-500 font-bold mb-8 text-sm md:text-base">هل أنت متأكد من حذف هذا التعليق نهائياً؟</p>
      <div class="flex gap-3 md:gap-4">
        <button onclick={executeDelete} disabled={isDeletingComment} class="flex-1 py-3 bg-red-500 text-white rounded-2xl font-black text-sm shadow-lg hover:bg-red-600 transition-all flex items-center justify-center gap-2">
          {#if isDeletingComment} <Loader2 size={16} class="animate-spin" /> {:else} حذف نهائي {/if}
        </button>
        <button onclick={() => commentToDelete = null} class="flex-1 py-3 bg-slate-100 text-slate-500 rounded-2xl font-black text-sm">إلغاء</button>
      </div>
    </div>
  </div>
{/if}

<div class="min-h-screen bg-slate-100 py-6 md:py-8 px-3 md:px-10 text-right pb-20" dir="rtl">
  <div class="max-w-5xl mx-auto mb-6">
    <button onclick={goBack} class="flex items-center gap-2 bg-white px-5 py-2.5 rounded-2xl shadow-sm text-[#4a6583] font-black hover:bg-[#6b8cce] hover:text-white transition-all border border-slate-200 text-sm">
      رجوع <ArrowRight size={16} />
    </button>
  </div>

  {#if isLoading}
    <div class="max-w-5xl mx-auto"><div class="bg-white rounded-[2rem] h-80 animate-pulse flex items-center justify-center"><Loader2 size={40} class="animate-spin text-slate-300" /></div></div>
  {:else if !details}
    <div class="max-w-5xl mx-auto py-20 text-center bg-white rounded-[2.5rem] flex flex-col items-center gap-4">
      <Search size={64} class="text-slate-200" />
      <span class="text-slate-500 font-black text-xl">لم يتم العثور على الجلسة</span>
    </div>
  {:else}
    <div class="max-w-5xl mx-auto space-y-8">
      
      <div class="bg-white rounded-[2.5rem] shadow-sm border border-slate-200 overflow-hidden">
        <div class="w-full h-48 md:h-80 bg-slate-200 relative">
          {#if details.session.cover}
            <img src={`http://127.0.0.1:8000/pics/${details.session.cover}`} alt="Cover" class="w-full h-full object-cover" />
          {:else}
            <div class="w-full h-full bg-[#6b8cce] flex items-center justify-center text-white"><BookOpen size={64} opacity={0.5} /></div>
          {/if}
        </div>

        <div class="p-6 md:p-10">
          <div class="flex flex-col md:flex-row justify-between items-start gap-6">
            <div class="flex-1">
              <h1 class="text-2xl md:text-3xl font-black text-[#2a3c54] mb-4">{details.session.title}</h1>
              <button onclick={() => details?.teacher_id && navigate('teacher_view', details.teacher_id)} class="flex items-center gap-4 bg-[#f4f6fb] hover:bg-[#e8edf5] border border-slate-100 px-4 py-3 rounded-2xl w-fit mb-6 transition-all group">
                <div class="bg-white p-1.5 rounded-xl shadow-sm"><UserCircle size={28} class="text-[#6b8cce]" /></div>
                <div class="text-right">
                  <span class="block text-[10px] font-bold text-slate-400 uppercase">المحاضر</span>
                  <span class="block text-sm font-black text-[#2a3c54] group-hover:text-[#6b8cce]">{details.teacher_name}</span>
                </div>
              </button>
              <p class="text-slate-600 leading-relaxed">{details.session.description || 'لا يوجد وصف متاح.'}</p>
            </div>

            <div class="w-full md:w-72 shrink-0 bg-[#f8fafc] p-6 rounded-[2rem] border border-slate-100 shadow-inner">
              {#if details.session.student_limit}
                <div class="mb-5">
                  <div class="flex justify-between items-center mb-2">
                    <span class="text-[11px] font-black text-slate-500 flex items-center gap-1.5"><Users size={14} /> سعة الطلاب</span>
                    <span class="text-[10px] font-black {isFull ? 'text-rose-500' : 'text-emerald-500'} bg-white px-2 py-0.5 rounded-full border border-slate-100">{isFull ? 'مكتمل' : 'متاح'}</span>
                  </div>
                  <div class="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
                    <div class="h-full transition-all duration-1000 {isFull ? 'bg-rose-500' : 'bg-[#6b8cce]'}" style="width: {occupancyRate}%"></div>
                  </div>
                  <div class="flex justify-between mt-2 text-[10px] font-bold text-slate-400">
                    <span>مقبول: {details.accepted_count}</span>
                    <span>الكلي: {details.session.student_limit}</span>
                  </div>
                </div>
              {/if}

              {#if isEnrolled}
                <div class="bg-emerald-50 text-emerald-600 p-3 rounded-xl flex items-center justify-center gap-2 font-black text-sm">
                  <CheckCircle2 size={18} /> أنت مشترك في الجلسة
                </div>
              {:else}
                <button 
                  onclick={handleEnroll}
                  disabled={isEnrolling || (isFull && !isEnrolled)}
                  class="w-full py-3.5 rounded-2xl font-black text-sm flex items-center justify-center gap-2 transition-all shadow-md active:scale-95
                  {isFull ? 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none' : 'bg-[#2a3c54] text-white hover:bg-[#6b8cce]'}"
                >
                  {#if isEnrolling} <Loader2 size={18} class="animate-spin" /> {:else if isFull} <ShieldAlert size={18} /> اكتمل العدد {:else} <UserPlus size={18} /> انضمام الآن {/if}
                </button>
              {/if}
              <p class="text-[9px] text-slate-400 mt-3 text-center font-bold">زكاة العلم نشره — المحاضرات مجانية بالكامل</p>
            </div>
          </div>

          <div class="flex flex-wrap gap-4 items-center mt-6 border-t border-slate-100 pt-6">
            <div class="bg-amber-50 text-amber-700 px-4 py-2.5 rounded-2xl text-sm font-black border border-amber-100 flex items-center gap-1.5">
              <Star size={16} class="fill-amber-500 text-amber-500" /> المحتوى: {details.avg_session_rating > 0 ? Number(details.avg_session_rating).toFixed(1) : 'جديد'}
            </div>
            <div class="bg-[#eff3fa] text-[#2a3c54] px-4 py-2.5 rounded-2xl text-sm font-black border border-[#6b8cce]/20 flex items-center gap-1.5">
              <Star size={16} class="fill-[#6b8cce] text-[#6b8cce]" /> المعلم: {details.avg_teacher_rating > 0 ? Number(details.avg_teacher_rating).toFixed(1) : 'جديد'}
            </div>
            <span class="text-xs font-bold text-slate-400">({details.ratings_count} مقيّم)</span>

            {#if details.session.meeting_link && details.session.meeting_link.trim() !== '' && details.session.meeting_link !== 'null'}
              {@const cleanLink = details.session.meeting_link.startsWith('http') ? details.session.meeting_link : `https://${details.session.meeting_link}`}
              <a href={cleanLink} target="_blank" rel="noopener noreferrer" class="mr-auto bg-emerald-500 text-white px-6 py-2.5 rounded-2xl font-black text-sm flex items-center gap-2 hover:bg-emerald-600 shadow-md">
                <Link size={16} /> الدخول للجلسة
              </a>
            {:else}
              <button type="button" onclick={() => notify.info('لا يوجد رابط مباشر حالياً')} class="mr-auto bg-slate-100 text-slate-400 px-6 py-2.5 rounded-2xl font-black text-sm flex items-center gap-2 cursor-not-allowed">
                <Link size={16} /> لا يوجد رابط
              </button>
            {/if}
          </div>
        </div>
      </div>

      {#if isGuest}
        <div in:fade class="bg-gradient-to-br from-[#eff3fa] to-white p-6 md:p-8 rounded-[2.5rem] shadow-sm border border-[#6b8cce]/20 relative overflow-hidden">
          <div class="absolute top-0 right-0 w-40 h-40 bg-[#6b8cce]/10 rounded-full blur-3xl -mr-10 -mt-10"></div>
          <div class="relative z-10 flex flex-col md:flex-row md:items-center gap-5 text-right">
            <div class="bg-[#6b8cce] text-white p-4 rounded-2xl shrink-0 w-fit shadow-md"><Star size={28} class="fill-white" /></div>
            <div class="flex-1">
              <h3 class="text-lg md:text-xl font-black text-[#2a3c54] mb-1.5">شارك تجربتك مع هذه المحاضرة</h3>
              <p class="text-sm text-slate-600 font-medium">سجّل دخولك أو أنشئ حساباً جديداً لتقييم المحتوى والمعلم والمشاركة بالنقاش.</p>
            </div>
            <div class="flex gap-2">
              <button onclick={goLogin} class="bg-[#2a3c54] text-white px-4 py-2.5 rounded-xl font-black text-xs md:text-sm shadow-md hover:bg-[#1a2a3a] transition-all flex items-center gap-2"><LogIn size={14} /> دخول</button>
              <button onclick={goRegister} class="bg-white text-[#2a3c54] px-4 py-2.5 rounded-xl font-black text-xs md:text-sm border border-slate-200 hover:bg-slate-50 transition-all flex items-center gap-2"><UserPlus size={14} /> حساب جديد</button>
            </div>
          </div>
        </div>
      {:else if !hasRated && isStudent && enrollmentChecked}
        <div in:fade class="bg-white p-6 md:p-8 rounded-[2.5rem] shadow-sm border border-slate-200 relative overflow-hidden">
          <h3 class="flex items-center gap-2 text-xl font-black text-[#2a3c54] mb-6 relative z-10"><Star size={24} class="text-amber-500 fill-amber-500" /> شاركنا رأيك</h3>
          {#if isEnrolled}
            <div class="grid md:grid-cols-2 gap-6 relative z-10">
              <div class="bg-[#f4f6fb] p-5 rounded-2xl border border-slate-100 flex flex-col items-center">
                <p class="text-sm font-black text-slate-600 mb-3">جودة المحتوى؟</p>
                <div class="flex gap-1 flex-row-reverse" dir="ltr">
                  {#each [1, 2, 3, 4, 5] as star}<button onclick={() => (sessionRate = star)} class="p-1 transition-transform hover:scale-125"><Star size={32} class="transition-colors {sessionRate >= star ? 'fill-amber-400 text-amber-400' : 'text-slate-300'}" /></button>{/each}
                </div>
              </div>
              <div class="bg-[#f4f6fb] p-5 rounded-2xl border border-slate-100 flex flex-col items-center">
                <p class="text-sm font-black text-slate-600 mb-3">أداء المعلم؟</p>
                <div class="flex gap-1 flex-row-reverse" dir="ltr">
                  {#each [1, 2, 3, 4, 5] as star}<button onclick={() => (teacherRate = star)} class="p-1 transition-transform hover:scale-125"><Star size={32} class="transition-colors {teacherRate >= star ? 'fill-amber-400 text-amber-400' : 'text-slate-300'}" /></button>{/each}
                </div>
              </div>
            </div>
            <div class="mt-6 flex justify-end relative z-10">
              <button onclick={submitRating} disabled={isPostingRating || sessionRate === 0 || teacherRate === 0} class="bg-[#2a3c54] text-white px-8 py-3 rounded-xl font-black text-sm hover:bg-[#6b8cce] shadow-md transition-all flex items-center gap-2">
                {#if isPostingRating} <Loader2 size={16} class="animate-spin" /> {:else} تأكيد التقييم <Check size={16} /> {/if}
              </button>
            </div>
          {:else}
            <div class="bg-slate-50 p-8 rounded-2xl border border-slate-100 flex flex-col items-center text-center gap-3">
              <div class="bg-slate-200 p-4 rounded-full text-slate-500"><Lock size={28} /></div>
              <p class="font-black text-slate-700 text-lg">يجب الانضمام أولاً للتقييم</p>
            </div>
          {/if}
        </div>
      {/if}

      <div class="bg-white p-6 md:p-8 rounded-[2.5rem] shadow-sm border border-slate-200">
        <h3 class="flex items-center gap-2 text-xl font-black text-[#2a3c54] mb-8 border-r-8 border-[#6b8cce] pr-4"><MessageSquare size={24} class="text-[#6b8cce]" /> ساحة النقاش</h3>
        {#if isGuest}
          <div class="mb-8 bg-gradient-to-br from-slate-50 to-[#eff3fa] p-5 rounded-3xl border border-slate-200 flex flex-col sm:flex-row items-center gap-4 text-right">
            <div class="bg-white p-3 rounded-2xl shadow-sm"><MessageSquare size={22} class="text-[#6b8cce]" /></div>
            <div class="flex-1"><p class="font-black text-[#2a3c54] text-sm">انضم للنقاش</p><p class="text-xs text-slate-500 font-medium">سجّل دخولك للتعليق والمشاركة برأيك</p></div>
            <div class="flex gap-2"><button onclick={goLogin} class="bg-[#6b8cce] text-white px-4 py-2 rounded-xl font-black text-xs hover:bg-[#5a7bbb] shadow-sm flex items-center gap-1.5"><LogIn size={13} /> دخول</button><button onclick={goRegister} class="bg-white text-[#2a3c54] px-4 py-2 rounded-xl font-black text-xs border border-slate-200 hover:bg-slate-50 transition-colors flex items-center gap-1.5"><UserPlus size={13} /> تسجيل</button></div>
          </div>
        {:else}
          <div class="mb-8 bg-slate-100 p-4 rounded-3xl border shadow-inner focus-within:ring-2 focus-within:ring-[#6b8cce]/20 transition-all">
            <textarea bind:value={newComment} placeholder="شاركنا استفسارك..." class="w-full bg-transparent outline-none resize-none h-20 p-2 text-right text-sm font-medium"></textarea>
            <div class="flex justify-between items-center border-t pt-3 border-slate-200">
              <div class="flex gap-3 text-slate-400">
                <button onclick={() => addEmoji('👍')} class="hover:text-[#6b8cce] hover:scale-110 transition-all"><ThumbsUp size={18} /></button>
                <button onclick={() => addEmoji('❤️')} class="hover:text-red-500 hover:scale-110 transition-all"><Heart size={18} /></button>
                <button onclick={() => addEmoji('🔥')} class="hover:text-orange-500 hover:scale-110 transition-all"><Flame size={18} /></button>
                <button onclick={() => addEmoji('💡')} class="hover:text-yellow-500 hover:scale-110 transition-all"><Lightbulb size={18} /></button>
              </div>
              <button onclick={() => submitComment(null)} disabled={isPostingComment || !newComment.trim()} class="px-6 py-2 bg-[#6b8cce] text-white font-black rounded-xl text-sm flex items-center gap-2 hover:bg-[#5a7bbb] transition-colors shadow-sm disabled:opacity-50">
                {#if isPostingComment} <Loader2 size={16} class="animate-spin" /> {:else} نشر {/if}
              </button>
            </div>
          </div>
        {/if}

        <div class="space-y-6">
          {#if details.comments.length === 0}
            <div class="py-12 text-center flex flex-col items-center gap-3"><MessageSquare size={48} class="text-slate-200" /><p class="text-slate-400 font-bold">لا توجد تعليقات بعد</p></div>
          {/if}
          {#each details.comments as comment (comment.id)}
            <div class="flex gap-4">
              <div class="w-12 h-12 bg-slate-100 rounded-2xl overflow-hidden shrink-0 text-[#6b8cce] border border-slate-200 flex items-center justify-center font-black">
                {#if comment.user_image}<img src={comment.user_image} alt="U" class="w-full h-full object-cover" />{:else}{comment.user_name.charAt(0)}{/if}
              </div>
              <div class="flex-1">
                <div class="bg-slate-50 p-4 rounded-2xl rounded-tr-none border border-slate-100">
                  <h4 class="font-black text-sm mb-1 text-[#2a3c54]">{comment.user_name}</h4>
                  <p class="text-slate-600 text-sm whitespace-pre-wrap leading-relaxed">{comment.content}</p>
                </div>
                <div class="flex gap-4 mt-2 px-2 items-center flex-row-reverse">
                  {#if !isGuest}<button onclick={() => (replyingTo = replyingTo === comment.id ? null : comment.id)} class="text-[10px] flex items-center gap-1 font-bold text-slate-500 hover:text-[#6b8cce] transition-colors"><CornerDownLeft size={12} /> رد</button>{/if}
                  {#if comment.user_id === $user?.id}<button onclick={() => { editingCommentId = comment.id; editContent = comment.content; }} class="text-slate-400 hover:text-blue-500 transition-all"><Pencil size={12} /></button><button onclick={() => requestDelete(comment.id)} class="text-slate-400 hover:text-red-500 transition-all"><Trash2 size={12} /></button>{/if}
                  <span class="text-[10px] font-bold text-slate-300 mr-auto">{formatDate(comment.created_at)}</span>
                </div>
                {#if editingCommentId === comment.id}
                  <div in:slide class="mt-2 flex gap-2"><input bind:value={editContent} class="flex-1 p-2 text-xs border border-slate-200 rounded-xl focus:border-[#6b8cce] outline-none" /><button onclick={() => handleEditSave(comment.id)} class="text-emerald-500"><Check size={16} /></button><button onclick={() => (editingCommentId = null)} class="text-red-500"><X size={16} /></button></div>
                {/if}
                {#if comment.replies?.length > 0}
                  <div class="mt-4 space-y-4 pr-6 border-r-2 border-slate-200">
                    {#each comment.replies as reply}
                      <div class="flex gap-3 flex-row-reverse text-right">
                        <div class="flex-1"><div class="bg-white p-3 rounded-xl border border-slate-100 shadow-sm text-xs"><h4 class="font-bold text-[#2a3c54] mb-1">{reply.user_name}</h4><p class="text-slate-600 leading-relaxed">{reply.content}</p></div><div class="flex gap-3 mt-1 px-2 items-center flex-row-reverse">{#if reply.user_id === $user?.id}<button onclick={() => { editingCommentId = reply.id; editContent = reply.content; }} class="text-slate-300 hover:text-blue-500"><Pencil size={10} /></button><button onclick={() => requestDelete(reply.id)} class="text-slate-300 hover:text-red-500"><Trash2 size={10} /></button>{/if}<span class="text-[9px] text-slate-300 mr-auto">{formatDate(reply.created_at)}</span></div></div>
                      </div>
                    {/each}
                  </div>
                {/if}
                {#if replyingTo === comment.id && !isGuest}
                  <div in:slide class="mt-4 flex gap-2"><input bind:value={replyContent} placeholder="اكتب ردك..." class="flex-1 p-2 border border-slate-200 rounded-xl text-xs focus:border-[#6b8cce] outline-none" /><button onclick={() => submitComment(comment.id)} disabled={isPostingComment || !replyContent.trim()} class="bg-[#6b8cce] text-white px-5 py-1.5 rounded-xl text-xs font-bold shadow-sm">رد</button></div>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  textarea::placeholder, input::placeholder { text-align: right; }
  /* Custom scrollbar and alignment tweaks */
</style>