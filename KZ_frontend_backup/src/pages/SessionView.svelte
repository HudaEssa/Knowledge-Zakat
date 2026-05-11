<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, fly, scale } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import {
    ArrowRight, BookOpen, User, Tag, Calendar,
    Clock, Timer, CheckCircle2, Send, Loader2,
    SearchX, ChevronLeft, GraduationCap, Layers,
    X, AlertCircle, Users, Infinity as InfinityIcon, LogIn
  } from 'lucide-svelte';
  import api from '../lib/api';
  import { user, token } from '../lib/stores';
  import { route, navigate } from '../lib/router';
  import { notify } from '../lib/notifications';
  import { authPrompt } from '../lib/authPrompt';
  import type { Session } from '../lib/types';
  import type { AxiosError } from 'axios';

  // ── Types ─────────────────────────────────────────────────────────────────
  interface SelectableSession extends Session {
    day_title: string;
    selected: boolean;
    enrollment_status: 'none' | 'pending' | 'approved';
    // الحقول الجديدة من الـ backend
    student_limit: number | null;
    accepted_count: number;
  }
  interface CourseDetails {
    title: string;
    description: string;
    teacher: string;
    teacher_id: number | null;
    category: string;
    cover: string | null;
  }

  // ── State ─────────────────────────────────────────────────────────────────
  let courseTitle   = $derived($route.param ?? '');
  let courseDetails = $state<CourseDetails | null>(null);
  let sessions      = $state<SelectableSession[]>([]);
  let isLoading     = $state(true);
  let isSubmitting  = $state(false);
  let cancellingId  = $state<number | null>(null); 

  // Modal State
  let showCancelModal = $state(false);
  let sessionToCancel = $state<number | null>(null);

  // Guest = no token. Used to short-circuit auth-only flows.
  let isGuest = $derived(!$token);

  // ── Helpers ───────────────────────────────────────────────────────────────
  function getArabicDay(dateStr: string | null): string {
    if (!dateStr) return 'غير محدد';
    const d = new Date(dateStr);
    if (Number.isNaN(d.getTime())) return 'غير محدد';
    return ['الأحد','الاثنين','الثلاثاء','الأربعاء','الخميس','الجمعة','السبت'][d.getDay()];
  }
  function safeTime(dateStr: string | null): string {
    if (!dateStr || !dateStr.includes('T')) return '00:00';
    return dateStr.split('T')[1].substring(0, 5);
  }
  function safeDate(dateStr: string | null): string {
    if (!dateStr) return '';
    return dateStr.split('T')[0];
  }
  function hideBrokenImg(e: Event) {
    const img = e.currentTarget as HTMLImageElement;
    img.style.display = 'none';
    const fb = img.nextElementSibling as HTMLElement | null;
    if (fb) fb.style.display = 'flex';
  }

  // ── Capacity helpers ─────────────────────────────────────────────────────
  // Single source of truth for "is this session full?" so the template
  // doesn't have to repeat the logic across the badge, the checkbox,
  // and the label class.
  function isFull(s: SelectableSession): boolean {
    return s.student_limit !== null && s.accepted_count >= s.student_limit;
  }

  // A row is interactive only if it's not full AND not already enrolled.
  function isRowSelectable(s: SelectableSession): boolean {
    return s.enrollment_status === 'none' && !isFull(s);
  }

  let selectedCount = $derived(sessions.filter(s => s.selected).length);
  let availableToSelect = $derived(
    sessions.filter(s => isRowSelectable(s)).length
  );

  // ── Load ──────────────────────────────────────────────────────────────────
  async function loadCourse(): Promise<void> {
    if (!courseTitle) {
      notify.error('لم يتم تحديد المحاضرة المطلوبة');
      navigate('home', null, true);
      return;
    }
    isLoading = true;
    try {
      const res = await api.get<Session[]>('/sessions/');
      const related = res.data.filter((s) => {
        if (!s.title) return false;
        const prefix = s.title.includes(' - ') ? s.title.split(' - ')[0].trim() : s.title.trim();
        return prefix === courseTitle;
      });

      if (related.length === 0) {
        notify.warning('لم يتم العثور على هذه المحاضرة');
        courseDetails = null; sessions = []; return;
      }

      let approvedSessionIds: number[] = [];
      let pendingSessionIds: number[] = [];
      
      // Guests skip the auth-only enrollment lookup entirely — saves
      // the 401 round-trip we used to spam in the console.
      if ($user && !isGuest) {
        try {
          const enrollRes = await api.get('/enrollments/my-sessions/');
          approvedSessionIds = enrollRes.data.map((e: any) => e.id || e.session_id);
        } catch (err) {
          console.error("لم نتمكن من جلب حالة الانضمام", err);
        }
      }

      const first = related[0];
      courseDetails = {
        title:       courseTitle,
        description: first.description ?? 'لا يوجد وصف متاح لهذه المحاضرة',
        teacher:     first.teacher_name ? ` ${first.teacher_name}` : 'قيد التحديث',
        // 👈 التعديل هنا: قراءة user_id كبديل إذا teacher_id مفقود
        teacher_id:  (first as any).user_id ?? first.teacher_id ?? null,
        category:    first.categories?.map((c) => c.category_name).join('، ') || 'عام',
        cover:       first.cover_image_url ?? null,
      };

      sessions = related.map((s) => {
        const isApproved = approvedSessionIds.includes(s.id);
        const isPending = pendingSessionIds.includes(s.id);
        
        return {
          ...s,
          day_title: s.title.includes(' - ') ? s.title.split(' - ')[1].trim() : s.title,
          selected: false,
          enrollment_status: isApproved ? 'approved' : (isPending ? 'pending' : 'none'),
          // الـ fallbacks لو السيرفر مرجّع الحقلين الجديدين بعد
          student_limit: (s as any).student_limit ?? null,
          accepted_count: (s as any).accepted_count ?? 0,
        };
      });

    } catch {
      notify.error('تعذّر تحميل بيانات المحاضرة');
    } finally {
      isLoading = false;
    }
  }

  // ── Enroll ────────────────────────────────────────────────────────────────
  async function sendEnrollmentRequests(): Promise<void> {
    // Guest guard — invite to sign in instead of failing silently.
    if (isGuest) {
      authPrompt.show('سجّل دخولك لإرسال طلب الانضمام للمحاضرات');
      return;
    }
    if (!$user) { notify.warning('يرجى تسجيل الدخول أولاً'); return; }
    const selected = sessions.filter((s) => s.selected);
    if (selected.length === 0) { notify.warning('يرجى تحديد جلسة واحدة على الأقل'); return; }
    if (isSubmitting) return;
    
    isSubmitting = true;
    try {
      const results = await Promise.allSettled(
        selected.map((s) => api.post('/enrollments/request', { session_id: s.id }))
      );
      
      const succeeded      = results.filter((r) => r.status === 'fulfilled').length;
      const failed         = results.filter((r) => r.status === 'rejected');
      const alreadyReq     = failed.filter((r) => {
        const reason = r.status === 'rejected' ? (r.reason as AxiosError) : null;
        return reason?.response?.status === 400;
      }).length;

      if (succeeded > 0) {
        notify.success(`تم إرسال ${succeeded} طلب بنجاح`);
        sessions = sessions.map(s => 
          s.selected ? { ...s, selected: false, enrollment_status: 'pending' } : s
        );
      } else if (alreadyReq === selected.length) {
        notify.warning('لقد أرسلت طلب الانضمام لهذه الجلسات مسبقاً');
        sessions = sessions.map(s => 
          s.selected ? { ...s, selected: false, enrollment_status: 'pending' } : s
        );
      } else {
        // Inspect the failures — most likely now is "session full" (400 from
        // the capacity check on the backend).
        const fullFailures = failed.filter((r) => {
          const reason = r.status === 'rejected' ? (r.reason as AxiosError) : null;
          const detail = String((reason?.response?.data as { detail?: string })?.detail ?? '');
          return detail.includes('اكتمل العدد');
        }).length;
        if (fullFailures > 0) {
          notify.error('بعض الجلسات اكتمل العدد فيها — حاولي تحديد أخرى');
        } else {
          notify.error('تعذّر إرسال بعض الطلبات، يرجى المحاولة لاحقاً');
        }
      }
    } finally {
      isSubmitting = false;
    }
  }

  // ── Cancel Enrollment Logic ───────────────────────────────────────────────
  function promptCancel(e: Event, sessionId: number): void {
    e.preventDefault();
    e.stopPropagation();
    sessionToCancel = sessionId;
    showCancelModal = true;
  }

  function closeCancelModal(): void {
    showCancelModal = false;
    sessionToCancel = null;
  }

  async function confirmCancel(): Promise<void> {
    if (!sessionToCancel) return;
    
    const sessionId = sessionToCancel;
    cancellingId = sessionId;
    showCancelModal = false;
    sessionToCancel = null;

    try {
      await api.delete(`/enrollments/${sessionId}`);
      notify.success('تم إلغاء الانضمام بنجاح');
      
      sessions = sessions.map(s => 
        s.id === sessionId ? { ...s, enrollment_status: 'none', selected: false } : s
      );
    } catch (err) {
      notify.error('تعذّر إلغاء الانضمام، يرجى المحاولة لاحقاً');
    } finally {
      cancellingId = null;
    }
  }

  function openTeacher(): void {
    if (courseDetails?.teacher_id) navigate('teacher_view', courseDetails.teacher_id);
  }

  function toggleAll() {
    // Only consider rows that are actually selectable (not enrolled, not full).
    const available = sessions.filter(s => isRowSelectable(s));
    const allSelected = available.every(s => s.selected);
    sessions = sessions.map(s => 
      isRowSelectable(s) ? { ...s, selected: !allSelected } : s
    );
  }

  onMount(loadCourse);
</script>

<div class="sv-page" dir="rtl">

  <div class="back-row" in:fly={{ x: 20, duration: 350, easing: cubicOut }}>
    <button class="back-btn" onclick={() => navigate('home')}>
      <ArrowRight size={17} strokeWidth={2.5} />
      العودة للمحاضرات
    </button>
  </div>

  {#if isLoading}
    <div class="skel-header">
      <div class="skel-cover"></div>
      <div class="skel-info">
        <div class="skel-line w-55"></div>
        <div class="skel-line w-80"></div>
        <div class="skel-line w-40"></div>
      </div>
    </div>
    <div class="skel-list">
      {#each Array(3) as _, i}
        <div class="skel-row" style="animation-delay:{i*90}ms"></div>
      {/each}
    </div>

  {:else if !courseDetails}
    <div class="not-found" in:fly={{ y: 24, duration: 420 }}>
      <SearchX size={56} color="var(--primary)" strokeWidth={1.2} />
      <p class="nf-title">لم يتم العثور على هذه المحاضرة</p>
      <button class="btn-back-home" onclick={() => navigate('home')}>
        <ChevronLeft size={16} /> العودة للرئيسية
      </button>
    </div>

  {:else}
    <div class="sv-content" in:fade={{ duration: 380 }}>

      <header class="header-card" in:fly={{ y: 30, duration: 450, easing: cubicOut }}>
        <div class="header-cover">
          {#if courseDetails.cover}
            <img src={`http://127.0.0.1:8000/pics/${courseDetails.cover}`} alt={courseDetails.title} onerror={hideBrokenImg} />
          {/if}
          <div class="cover-fallback" style={courseDetails.cover ? 'display:none' : 'display:flex'}>
            <BookOpen size={64} color="white" strokeWidth={1} />
          </div>
          <div class="cover-overlay"></div>
          <div class="cover-badges">
            <span class="badge badge--sessions"><Layers size={12} strokeWidth={2.5} />عدد المحاضرات  : {sessions.length}</span>
            <span class="badge badge--cat"><Tag size={11} strokeWidth={2.5} />  التصنيف : {courseDetails.category}</span>
          </div>
        </div>

        <div class="header-info">
          <h1 class="course-title">{courseDetails.title}</h1>
          <p class="course-desc">{courseDetails.description}</p>
          <button class="teacher-row" onclick={openTeacher} disabled={!courseDetails.teacher_id}>
            <div class="teacher-avatar">
              {#if courseDetails.teacher_id}
                <img src={`http://127.0.0.1:8000/users/${courseDetails.teacher_id}/profile_image`} alt="teacher" onerror={hideBrokenImg} />
                <div class="avatar-fb" style="display:none"><User size={22} color="var(--primary)" strokeWidth={1.5} /></div>
              {:else}
                <div class="avatar-fb" style="display:flex"><User size={22} color="var(--primary)" strokeWidth={1.5} /></div>
              {/if}
            </div>
            <div class="teacher-text">
           
              <span class="teacher-name">{courseDetails.teacher}</span>
            </div>
          
          </button>
        </div>
      </header>

      <section class="sessions-card" in:fly={{ y: 40, delay: 120, duration: 450, easing: cubicOut }}>
        <div class="sessions-head">
          <div class="sessions-head-text">
            <h2 class="sessions-title">الجلسات المتاحة</h2>
            <p class="sessions-sub">اختر الجلسات التي تودّ حضورها ثم أرسل طلبك</p>
          </div>
          {#if availableToSelect > 1}
            <button class="select-all-btn" onclick={toggleAll}>
              <CheckCircle2 size={15} strokeWidth={2.5} />
              {sessions.filter(s => isRowSelectable(s)).every(s => s.selected) ? 'إلغاء الكل' : 'تحديد المتاح'}
            </button>
          {/if}
        </div>

        <div class="sessions-list">
          {#each sessions as session, i (session.id)}
            {@const full = isFull(session)}
            <label
              class="session-row 
                {session.selected ? 'session-row--active' : ''}
                {session.enrollment_status === 'pending' ? 'session-row--pending' : ''}
                {session.enrollment_status === 'approved' ? 'session-row--approved' : ''}
                {full && session.enrollment_status === 'none' ? 'session-row--full' : ''}"
              in:fly={{ x: -20, delay: i * 60, duration: 380, easing: cubicOut }}
            >
              <div class="cb-wrap">
                {#if session.enrollment_status === 'none' && !full}
                  <input type="checkbox" bind:checked={session.selected} class="cb-real" />
                  <div class="cb-box {session.selected ? 'cb-box--checked' : ''}">
                    {#if session.selected}<CheckCircle2 size={18} strokeWidth={2.5} color="white" />{/if}
                  </div>
                {:else if session.enrollment_status === 'approved'}
                  <CheckCircle2 size={24} strokeWidth={2.5} color="var(--success)" />
                {:else if session.enrollment_status === 'pending'}
                  <Timer size={24} strokeWidth={2.5} color="#f59e0b" />
                {:else if full}
                  <!-- Full and not enrolled → show a lock-like icon -->
                  <X size={22} strokeWidth={2.5} color="#94a3b8" />
                {/if}
              </div>

              <div class="row-info">
                <p class="row-title">{session.day_title}</p>
                <div class="row-meta">
                  <span class="meta-chip">
                    <Calendar size={11} strokeWidth={2.5} /> {getArabicDay(session.date_time)}
                    {#if safeDate(session.date_time)} — {safeDate(session.date_time)}{/if}
                  </span>
                  <span class="meta-chip"><Clock size={11} strokeWidth={2.5} /> {safeTime(session.date_time)}</span>
                  {#if session.session_duration}
                    <span class="meta-chip"><Timer size={11} strokeWidth={2.5} /> {session.session_duration} دقيقة</span>
                  {/if}

                  <!-- Capacity badge: unlimited / X-of-Y / full -->
                  {#if session.student_limit === null}
                    <span class="meta-chip cap-chip cap-chip--unlimited">
                      <InfinityIcon size={11} strokeWidth={2.5} />
                      السعة: غير محدودة
                    </span>
                  {:else if full}
                    <span class="meta-chip cap-chip cap-chip--full">
                      <Users size={11} strokeWidth={2.5} />
                      ممتلئ ({session.accepted_count} / {session.student_limit})
                    </span>
                  {:else}
                    <span class="meta-chip cap-chip cap-chip--available" dir="ltr">
                      <Users size={11} strokeWidth={2.5} />
                      <span>{session.accepted_count} / {session.student_limit}</span>
                    </span>
                  {/if}
                </div>
              </div>

              {#if session.enrollment_status === 'none' && session.selected}
                <span class="row-selected-badge" in:scale={{ duration: 250 }}>محدد ✓</span>
              
              {:else if session.enrollment_status === 'approved' || session.enrollment_status === 'pending'}
                <div class="status-group" in:scale={{ duration: 250 }}>
                  {#if session.enrollment_status === 'approved'}
                    <span class="status-badge approved">تم الانضمام</span>
                  {:else}
                    <span class="status-badge pending">قيد الانتظار</span>
                  {/if}
                  
                  <button 
                    class="cancel-btn" 
                    title="إلغاء الانضمام"
                    onclick={(e) => promptCancel(e, session.id)}
                    disabled={cancellingId === session.id}
                  >
                    {#if cancellingId === session.id}
                      <span class="spin"><Loader2 size={14} /></span>
                    {:else}
                      <X size={15} strokeWidth={2.5} />
                    {/if}
                  </button>
                </div>
              {:else if full}
                <span class="status-badge full">اكتمل العدد</span>
              {/if}
            </label>
          {/each}
        </div>

        <div class="submit-area">
          {#if selectedCount > 0}
            <p class="selected-hint" in:fade={{ duration: 250 }}>تم تحديد <strong>{selectedCount}</strong> جلسة</p>
          {/if}

          {#if isGuest}
            <!-- Guest CTA replaces the enroll button -->
            <button class="submit-btn submit-btn--guest" onclick={() => navigate('login', null, true)}>
              <LogIn size={18} strokeWidth={2.5} />
              سجّل دخولك للتسجيل في المحاضرات
            </button>
          {:else}
            <button class="submit-btn" onclick={sendEnrollmentRequests} disabled={isSubmitting || selectedCount === 0}>
              {#if isSubmitting}
                <span class="spin"><Loader2 size={20} strokeWidth={2.5} /></span> جاري إرسال الطلب...
              {:else}
                <Send size={18} strokeWidth={2.5} /> إرسال طلب الانضمام
                {#if selectedCount > 0}<span class="submit-count">{selectedCount}</span>{/if}
              {/if}
            </button>
          {/if}
        </div>
      </section>
    </div>
  {/if}
</div>

{#if showCancelModal}
  <div class="modal-overlay" in:fade={{ duration: 200 }} out:fade={{ duration: 150 }} dir="rtl">
    <div class="modal-box" in:scale={{ start: 0.95, duration: 250, easing: cubicOut }}>
      <div class="modal-icon">
        <AlertCircle size={32} color="#ef4444" strokeWidth={2} />
      </div>
      <h3 class="modal-title">إلغاء الانضمام</h3>
      <p class="modal-desc">هل أنت متأكد من إلغاء الانضمام لهذه الجلسة؟ لا يمكن التراجع عن هذا الإجراء وسيتم مسح طلبك نهائياً.</p>
      
      <div class="modal-actions">
        <button class="modal-btn modal-btn--secondary" onclick={closeCancelModal}>تراجع</button>
        <button class="modal-btn modal-btn--danger" onclick={confirmCancel}>تأكيد الإلغاء</button>
      </div>
    </div>
  </div>
{/if}

<style>
  :root {
    --primary:   #6b8cce;
    --dark:      #2a3c54;
    --light-bg:  #f4f6fb;
    --card-bg:   #ffffff;
    --border:    #e8edf5;
    --muted:     #8a96a8;
    --success:   #22c55e;
    --danger:    #ef4444;
    --radius-xl: 2.25rem;
    --radius-lg: 1.5rem;
    --radius-md: .875rem;
    --shadow-sm: 0 2px 10px rgba(42,60,84,.06);
    --shadow-lg: 0 20px 56px rgba(42,60,84,.12);
    --trans:     all .3s cubic-bezier(.4,0,.2,1);
  }

  .sv-page { direction: rtl; max-width: 860px; margin: 0 auto; padding: 1.5rem 1.25rem 5rem; display: flex; flex-direction: column; gap: 1.5rem; }
  .back-row { display: flex; }
  .back-btn { display: inline-flex; align-items: center; gap: .5rem; padding: .6rem 1.25rem; background: var(--card-bg); border: 1px solid var(--border); border-radius: var(--radius-md); color: var(--dark); font-weight: 800; font-size: .85rem; cursor: pointer; transition: var(--trans); box-shadow: var(--shadow-sm); font-family: inherit; }
  .back-btn:hover { background: var(--dark); color: white; border-color: var(--dark); transform: translateX(3px); }
  .sv-content { display: flex; flex-direction: column; gap: 1.5rem; }

  /* Header */
  .header-card { background: var(--card-bg); border-radius: var(--radius-xl); border: 1px solid var(--border); overflow: hidden; box-shadow: var(--shadow-lg); }
  .header-cover { height: 220px; position: relative; overflow: hidden; background: var(--light-bg); }
  .header-cover img { width: 100%; height: 100%; object-fit: cover; display: block; transition: transform .7s ease; }
  .header-card:hover .header-cover img { transform: scale(1.04); }
  .cover-fallback { position: absolute; inset: 0; background: linear-gradient(135deg, var(--primary) 0%, var(--dark) 100%); align-items: center; justify-content: center; }
  .cover-overlay { position: absolute; inset: 0; background: linear-gradient(to top, rgba(42,60,84,.75) 0%, rgba(42,60,84,.1) 60%, transparent 100%); pointer-events: none; }
  .cover-badges { position: absolute; bottom: .9rem; right: 1rem; display: flex; gap: .5rem; flex-wrap: wrap; }
  .badge { display: inline-flex; align-items: center; gap: .3rem; padding: .3em .8em; border-radius: 99px; font-size: .72rem; font-weight: 800; backdrop-filter: blur(8px); border: 1px solid rgba(255,255,255,.25); }
  .badge--sessions { background: rgba(255,255,255,.92); color: var(--dark); }
  .badge--cat      { background: rgba(107,140,206,.85); color: white; }
  .header-info { padding: 1.75rem 2rem 2rem; display: flex; flex-direction: column; gap: 1rem; }
  .course-title { font-size: clamp(1.4rem, 4vw, 2rem); font-weight: 900; color: var(--dark); margin: 0; letter-spacing: -.02em; line-height: 1.2; }
  .course-desc { font-size: .9rem; color: var(--muted); font-weight: 500; line-height: 1.65; margin: 0; }

  /* Teacher */
  .teacher-row { display: inline-flex; align-items: center; gap: .85rem; padding: .75rem 1rem; background: var(--light-bg); border: 1px solid var(--border); border-radius: var(--radius-md); cursor: pointer; transition: var(--trans); font-family: inherit; width: fit-content; }
  .teacher-row:hover:not(:disabled) { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(107,140,206,.12); transform: translateY(-1px); }
  .teacher-row:disabled { cursor: default; }
  .teacher-avatar { width: 2.75rem; height: 2.75rem; border-radius: .75rem; background: white; border: 2px solid var(--border); overflow: hidden; position: relative; flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
  .teacher-avatar img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .avatar-fb { position: absolute; inset: 0; background: var(--light-bg); align-items: center; justify-content: center; }
  .teacher-text { display: flex; flex-direction: column; gap: .1rem; text-align: right; }
  .teacher-name  { font-size: .9rem; font-weight: 800; color: var(--dark); }

  /* Sessions List */
  .sessions-card { background: var(--card-bg); border-radius: var(--radius-xl); border: 1px solid var(--border); box-shadow: var(--shadow-lg); overflow: hidden; }
  .sessions-head { display: flex; align-items: center; justify-content: space-between; padding: 1.75rem 2rem 1.25rem; border-bottom: 1px solid var(--border); gap: 1rem; flex-wrap: wrap; }
  .sessions-head-text { display: flex; flex-direction: column; gap: .2rem; }
  .sessions-title { font-size: 1.1rem; font-weight: 900; color: var(--dark); margin: 0; }
  .sessions-sub   { font-size: .8rem; color: var(--muted); font-weight: 500; margin: 0; }
  .select-all-btn { display: inline-flex; align-items: center; gap: .4rem; padding: .5rem 1rem; background: var(--light-bg); border: 1px solid var(--border); border-radius: var(--radius-md); font-size: .78rem; font-weight: 800; color: var(--dark); cursor: pointer; transition: var(--trans); font-family: inherit; }
  .select-all-btn:hover { background: var(--dark); color: white; border-color: var(--dark); }
  .sessions-list { padding: 1.25rem 1.5rem; display: flex; flex-direction: column; gap: .75rem; }
  
  .session-row { display: flex; align-items: center; gap: 1rem; padding: 1rem 1.25rem; border-radius: var(--radius-md); border: 1.5px solid var(--border); background: var(--card-bg); cursor: pointer; transition: var(--trans); position: relative; }
  .session-row:hover { border-color: rgba(107,140,206,.4); background: #fafbfd; }
  
  /* Status specific styles */
  .session-row--active { border-color: var(--primary); background: linear-gradient(135deg, #f0f5ff 0%, #f5f8ff 100%); box-shadow: 0 0 0 3px rgba(107,140,206,.1); }
  .session-row--pending { border-color: rgba(245, 158, 11, 0.4) !important; background: #fffbeb !important; cursor: default; }
  .session-row--approved { border-color: rgba(34, 197, 94, 0.4) !important; background: #f0fdf4 !important; cursor: default; }
  /* Full sessions look "dimmed" — visible but clearly not interactive. */
  .session-row--full {
    border-color: #e2e8f0 !important;
    background: #f8fafc !important;
    cursor: not-allowed;
    opacity: .75;
  }
  .session-row--full:hover { border-color: #e2e8f0 !important; background: #f8fafc !important; }
  .session-row--full .row-title { color: var(--muted); }

  .cb-wrap { position: relative; flex-shrink: 0; }
  .cb-real { position: absolute; opacity: 0; width: 0; height: 0; }
  .cb-box { width: 1.5rem; height: 1.5rem; border-radius: .45rem; border: 2px solid var(--border); background: white; display: flex; align-items: center; justify-content: center; transition: var(--trans); }
  .cb-box--checked { background: var(--dark); border-color: var(--dark); }

  .row-info { flex: 1; display: flex; flex-direction: column; gap: .4rem; }
  .row-title { font-size: .95rem; font-weight: 800; color: var(--dark); margin: 0; }
  .row-meta { display: flex; flex-wrap: wrap; gap: .4rem; }
  .meta-chip { display: inline-flex; align-items: center; gap: .3rem; padding: .25em .65em; background: var(--light-bg); border-radius: 99px; font-size: .72rem; font-weight: 700; color: var(--muted); border: 1px solid var(--border); }
  
  .session-row--active .meta-chip { background: rgba(107,140,206,.1); border-color: rgba(107,140,206,.2); }
  .session-row--pending .meta-chip { background: rgba(245, 158, 11, 0.1); border-color: rgba(245, 158, 11, 0.2); color: #b45309; }
  .session-row--approved .meta-chip { background: rgba(34, 197, 94, 0.1); border-color: rgba(34, 197, 94, 0.2); color: #15803d; }

  /* Capacity chips — distinct from the date/time chips so they pop visually. */
  .cap-chip { font-weight: 800; }
  .cap-chip--unlimited { background: rgba(107, 140, 206, .08); color: var(--primary); border-color: rgba(107, 140, 206, .25); }
  .cap-chip--available { background: rgba(34, 197, 94, .08); color: #15803d; border-color: rgba(34, 197, 94, .25); }
  .cap-chip--full { background: rgba(239, 68, 68, .08); color: var(--danger); border-color: rgba(239, 68, 68, .25); }

  /* ── Status & Cancel Group ── */
  .status-group { display: flex; align-items: center; gap: 0.4rem; flex-shrink: 0; }
  .row-selected-badge { font-size: .7rem; font-weight: 800; color: var(--primary); background: rgba(107,140,206,.12); padding: .25em .7em; border-radius: 99px; flex-shrink: 0; }
  .status-badge { font-size: .7rem; font-weight: 800; padding: .35em .8em; border-radius: 99px; flex-shrink: 0; }
  .status-badge.approved { background: rgba(34, 197, 94, 0.15); color: #15803d; }
  .status-badge.pending { background: rgba(245, 158, 11, 0.15); color: #b45309; }
  .status-badge.full { background: rgba(239, 68, 68, .12); color: var(--danger); }

  .cancel-btn { display: flex; align-items: center; justify-content: center; background: white; border: 1px solid var(--border); color: var(--muted); border-radius: 50%; width: 28px; height: 28px; cursor: pointer; transition: all 0.2s ease; }
  .cancel-btn:hover:not(:disabled) { background: rgba(239, 68, 68, 0.1); color: var(--danger); border-color: var(--danger); }
  .cancel-btn:disabled { opacity: 0.5; cursor: not-allowed; }

  /* Submit Area */
  .submit-area { padding: 1.25rem 1.5rem 1.75rem; border-top: 1px solid var(--border); display: flex; flex-direction: column; gap: .75rem; }
  .selected-hint { font-size: .82rem; color: var(--muted); font-weight: 600; text-align: center; margin: 0; }
  .selected-hint strong { color: var(--dark); }
  .submit-btn { width: 100%; padding: 1rem 1.5rem; background: var(--dark); color: white; border: none; border-radius: var(--radius-lg); font-size: 1rem; font-weight: 900; cursor: pointer; transition: var(--trans); display: inline-flex; align-items: center; justify-content: center; gap: .6rem; font-family: inherit; position: relative; overflow: hidden; }
  .submit-btn::before { content: ''; position: absolute; inset: 0; background: linear-gradient(135deg, rgba(255,255,255,.08) 0%, transparent 100%); }
  .submit-btn:hover:not(:disabled) { background: var(--primary); transform: translateY(-2px); box-shadow: 0 8px 24px rgba(107,140,206,.35); }
  .submit-btn:active:not(:disabled) { transform: translateY(0) scale(.99); }
  .submit-btn:disabled { opacity: .5; cursor: not-allowed; }
  .submit-btn--guest { background: var(--primary); }
  .submit-btn--guest:hover { background: var(--dark); }
  .submit-count { background: rgba(255,255,255,.2); padding: .1em .55em; border-radius: 99px; font-size: .8rem; font-weight: 900; }
  .spin { animation: spin 1s linear infinite; display: flex; }
  
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Custom Modal Styles ── */
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 1.5rem;
  }
  .modal-box {
    background: var(--card-bg);
    width: 100%;
    max-width: 400px;
    border-radius: 1.5rem;
    padding: 2rem;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    border: 1px solid var(--border);
  }
  .modal-icon {
    width: 64px;
    height: 64px;
    background: #fef2f2;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 0.5rem;
  }
  .modal-title {
    font-size: 1.25rem;
    font-weight: 900;
    color: var(--dark);
    margin: 0;
  }
  .modal-desc {
    font-size: 0.9rem;
    color: var(--muted);
    line-height: 1.6;
    margin: 0 0 1rem 0;
  }
  .modal-actions {
    display: flex;
    gap: 0.75rem;
    width: 100%;
  }
  .modal-btn {
    flex: 1;
    padding: 0.85rem;
    border-radius: var(--radius-md);
    font-size: 0.95rem;
    font-weight: 800;
    cursor: pointer;
    transition: var(--trans);
    font-family: inherit;
    border: none;
  }
  .modal-btn--secondary {
    background: var(--light-bg);
    color: var(--dark);
    border: 1px solid var(--border);
  }
  .modal-btn--secondary:hover {
    background: #e2e8f0;
  }
  .modal-btn--danger {
    background: var(--danger);
    color: white;
  }
  .modal-btn--danger:hover {
    background: #dc2626;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.25);
  }

  /* Loading & Not Found */
  .skel-header { background: var(--card-bg); border-radius: var(--radius-xl); border: 1px solid var(--border); overflow: hidden; }
  .skel-cover { height: 220px; background: linear-gradient(90deg, #edf0f7 25%, #f4f6fb 50%, #edf0f7 75%); background-size: 200% 100%; animation: shimmer 1.7s infinite; }
  .skel-info { padding: 1.75rem 2rem; display: flex; flex-direction: column; gap: .75rem; }
  .skel-line { height: .85rem; background: #edf0f7; border-radius: 99px; animation: pulse 1.6s ease-in-out infinite; }
  .w-55 { width: 55%; } .w-80 { width: 80%; } .w-40 { width: 40%; }
  .skel-list { background: var(--card-bg); border-radius: var(--radius-xl); border: 1px solid var(--border); padding: 1.75rem 1.5rem; display: flex; flex-direction: column; gap: .75rem; }
  .skel-row { height: 4.5rem; background: #edf0f7; border-radius: var(--radius-md); animation: pulse 1.6s ease-in-out infinite; }
  @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .65; } }
  .not-found { padding: 5rem 2rem; text-align: center; background: var(--card-bg); border-radius: var(--radius-xl); border: 2px dashed var(--border); display: flex; flex-direction: column; align-items: center; gap: 1rem; }
  .nf-title { font-size: 1.1rem; font-weight: 800; color: var(--dark); margin: 0; }
  .btn-back-home { padding: 0.65rem 1.5rem; background: var(--dark); color: white; border: none; border-radius: var(--radius-md); font-weight: 800; font-size: 0.875rem; cursor: pointer; transition: var(--trans); display: inline-flex; align-items: center; gap: 0.4rem; font-family: inherit; }
  .btn-back-home:hover { background: var(--primary); transform: scale(1.04); }

  @media (max-width: 640px) {
    .sv-page { padding: 1rem .75rem 4rem; }
    .header-cover { height: 170px; }
    .header-info { padding: 1.25rem 1.25rem 1.5rem; }
    .sessions-head { padding: 1.25rem 1.25rem 1rem; }
    .sessions-list { padding: 1rem 1rem; }
    .submit-area { padding: 1rem 1rem 1.5rem; }
    .session-row { padding: .85rem 1rem; }
  }
</style>