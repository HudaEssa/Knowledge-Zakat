<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, scale, slide, fly } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import api from '../lib/api';
  import { notify } from '../lib/notifications';
  import {
    FileText, UserCircle, X, ChevronRight, ChevronLeft,
    RotateCcw, Phone, Calendar, CheckCircle, XCircle, Clock, Eye
  } from 'lucide-svelte';

  interface TeacherRequest {
    id: number;
    firstname: string;
    lastname: string;
    email: string;
    bio: string;
    cv_link: string | null;
    phone: string;
    birthday_date: string;
    status: string;
    profile_image?: string | null;
  }

  let pendingRequests = $state<TeacherRequest[]>([]);
  let historyRequests = $state<TeacherRequest[]>([]);
  let totalPending = $state(0);
  let offset = $state(0);
  const limit = 5;
  let isFetching = $state(true);

  let selectedUser = $state<TeacherRequest | null>(null);
  let showModal = $state(false);
  let cvImageError = $state(false);

  async function loadData() {
    isFetching = true;
    try {
      const [pendingRes, approvedRes, rejectedRes] = await Promise.all([
        api.get(`/admin/teacher-requests?status=pending&offset=${offset}&limit=${limit}`),
        api.get(`/admin/teacher-requests?status=approved&limit=5`),
        api.get(`/admin/teacher-requests?status=rejected&limit=5`)
      ]);
      pendingRequests = pendingRes.data.items ?? pendingRes.data ?? [];
      totalPending = pendingRes.data.total ?? pendingRequests.length;
      const approved = approvedRes.data.items ?? approvedRes.data ?? [];
      const rejected = rejectedRes.data.items ?? rejectedRes.data ?? [];
      historyRequests = [...approved, ...rejected];
    } catch {
      notify.error('خطأ في جلب البيانات');
    } finally {
      isFetching = false;
    }
  }

  async function updateStatus(userId: number, action: string) {
    try {
      const ep =
        action === 'approve' ? 'promote-to-teacher' :
        action === 'reject'  ? 'reject-teacher-request' :
                               'reset-teacher-request';
      await api.post(`/admin/users/${userId}/${ep}`);
      notify.success('تم التحديث بنجاح');
      showModal = false;
      selectedUser = null;
      await loadData();
    } catch {
      notify.error('فشلت العملية');
    }
  }

  function getFullUrl(cvLink: string | null): string | null {
    if (!cvLink) return null;
    return cvLink.startsWith('http') ? cvLink : `http://localhost:8000${cvLink}`;
  }

  function openUser(user: TeacherRequest) {
    selectedUser = user;
    cvImageError = false;
    showModal = true;
  }

  onMount(loadData);
</script>

<!-- PAGE -->
<div class="page-wrap" dir="rtl">

  <!-- PENDING SECTION -->
  <section class="section">

    <div class="section-header">
      <div class="section-title">
        <span class="title-pill">
          <Clock size={14} />
          انتظار المراجعة
        </span>
        <span class="count-badge">{totalPending}</span>
      </div>

      <div class="pagination-btns">
        <button
          onclick={() => { offset = Math.max(0, offset - limit); loadData(); }}
          disabled={offset === 0}
          class="page-btn"
          aria-label="السابق"
        >
          <ChevronRight size={16} />
        </button>
        <span class="page-info">{Math.floor(offset / limit) + 1} / {Math.ceil(totalPending / limit) || 1}</span>
        <button
          onclick={() => { if (offset + limit < totalPending) { offset += limit; loadData(); } }}
          disabled={offset + limit >= totalPending}
          class="page-btn"
          aria-label="التالي"
        >
          <ChevronLeft size={16} />
        </button>
      </div>
    </div>

    {#if isFetching}
      <div class="skeleton-list">
        {#each Array(3) as _}
          <div class="skeleton-card"></div>
        {/each}
      </div>

    {:else if pendingRequests.length === 0}
      <div in:fade class="empty-state">
        
        <p>لا توجد طلبات جديدة حالياً</p>
      </div>

    {:else}
      <ul class="card-list">
        {#each pendingRequests as user (user.id)}
          <li in:fly={{ y: 16, duration: 350, easing: cubicOut }} class="request-card">
            <div class="avatar">
              {#if user.profile_image}
                <img src={user.profile_image} alt={user.firstname} />
              {:else}
                <span>{user.firstname[0]}</span>
              {/if}
              <div class="avatar-ring"></div>
            </div>

            <div class="user-info">
              <strong>{user.firstname} {user.lastname}</strong>
              <span>{user.email}</span>
            </div>

            <div class="card-actions">
              <button onclick={() => openUser(user)} class="btn-ghost">
                <Eye size={13} /> عرض
              </button>
              <button onclick={() => updateStatus(user.id, 'approve')} class="btn-accept">
                <CheckCircle size={13} /> قبول
              </button>
              <button onclick={() => updateStatus(user.id, 'reject')} class="btn-reject">
                <XCircle size={13} /> رفض
              </button>
            </div>
          </li>
        {/each}
      </ul>
    {/if}
  </section>

  <!-- HISTORY SECTION -->
  {#if historyRequests.length > 0}
    <section class="section history-section">
      <div class="history-title">
        <RotateCcw size={14} />
        سجل القرارات السابقة
      </div>

      <ul class="history-list">
        {#each historyRequests as h (h.id)}
          <li in:slide={{ duration: 250 }} class="history-item">
            <span class="status-chip {h.status === 'approved' ? 'chip-green' : 'chip-red'}">
              {h.status === 'approved' ? 'مقبول' : 'مرفوض'}
            </span>
            <span class="history-name">{h.firstname} {h.lastname}</span>
            <button onclick={() => updateStatus(h.id, 'reset')} class="reset-btn">
              إعادة مراجعة ↩
            </button>
          </li>
        {/each}
      </ul>
    </section>
  {/if}
</div>

<!-- MODAL -->
{#if showModal && selectedUser}
  {@const fullUrl = getFullUrl(selectedUser.cv_link)}

  <div
    in:fade={{ duration: 200 }}
    out:fade={{ duration: 180 }}
    class="backdrop"
    onclick={() => { showModal = false; selectedUser = null; }}
    role="presentation"
  ></div>

  <div
    in:scale={{ duration: 320, start: 0.93, easing: cubicOut }}
    out:scale={{ duration: 200, start: 0.96 }}
    class="modal-panel"
    dir="rtl"
  >
    <div class="modal-header">
      <div class="modal-avatar">
        {#if selectedUser.profile_image}
          <img src={selectedUser.profile_image} alt={selectedUser.firstname} />
        {:else}
          <span>{selectedUser.firstname[0]}</span>
        {/if}
      </div>
      <div>
        <h2 class="modal-name">{selectedUser.firstname} {selectedUser.lastname}</h2>
        <p class="modal-sub">طلب انضمام كمعلم</p>
      </div>
      <button class="close-btn" onclick={() => { showModal = false; selectedUser = null; }}>
        <X size={18} />
      </button>
    </div>

    <div class="modal-body">

      <div class="meta-grid">
        <div class="meta-cell">
          <Phone size={12} class="meta-icon" />
          <span class="meta-label">الهاتف</span>
          <span class="meta-value" dir="ltr">{selectedUser.phone || '—'}</span>
        </div>
        <div class="meta-cell">
          <Calendar size={12} class="meta-icon" />
          <span class="meta-label">الميلاد</span>
          <span class="meta-value">{selectedUser.birthday_date || '—'}</span>
        </div>
        <div class="meta-cell wide">
          <UserCircle size={12} class="meta-icon" />
          <span class="meta-label">البريد الإلكتروني</span>
          <span class="meta-value">{selectedUser.email}</span>
        </div>
      </div>

      {#if selectedUser.bio}
        <div class="bio-box">
          <p class="bio-label">النبذة الشخصية</p>
          <p class="bio-text">{selectedUser.bio}</p>
        </div>
      {/if}

      <div class="cv-section">
        <p class="cv-label"><FileText size={13} /> السيرة الذاتية / المرفق</p>
        <div class="cv-frame">
          {#if fullUrl && !cvImageError}
            <img
              src={fullUrl}
              alt="CV"
              class="cv-image"
              onclick={() => window.open(fullUrl, '_blank')}
              onerror={() => cvImageError = true}
            />
          {:else if fullUrl && cvImageError}
            <div class="cv-fallback">
              <span class="cv-fallback-icon">📎</span>
              <p>المرفق ليس صورة — اضغط لفتحه</p>
              <a href={fullUrl} target="_blank" rel="noopener noreferrer" class="cv-open-btn">
                فتح المرفق ↗
              </a>
            </div>
          {:else}
            <div class="cv-empty">
              <FileText size={36} />
              <p>لا يوجد مرفق</p>
            </div>
          {/if}
        </div>
      </div>

      <div class="modal-actions">
        <button onclick={() => { showModal = false; selectedUser = null; }} class="btn-modal-close">
          إغلاق
        </button>
        <button onclick={() => updateStatus(selectedUser!.id, 'reject')} class="btn-modal-reject">
          <XCircle size={15} /> رفض
        </button>
        <button onclick={() => updateStatus(selectedUser!.id, 'approve')} class="btn-modal-approve">
          <CheckCircle size={15} /> قبول كمعلم
        </button>
      </div>

    </div>
  </div>
{/if}

<style>
  :root {
    --blue:       #4a6fa5;
    --blue-light: #eef2fa;
    --blue-mid:   #c8d6ef;
    --ink:        #1e2d42;
    --ink-soft:   #4a5568;
    --ink-muted:  #94a3b8;
    --green:      #22c55e;
    --green-bg:   #f0fdf4;
    --red:        #ef4444;
    --red-bg:     #fef2f2;
    --surface:    #ffffff;
    --radius-xl:  1.5rem;
    --radius-lg:  1rem;
    --radius-md:  .6rem;
    --shadow-sm:  0 2px 8px rgba(74,111,165,.08);
    --shadow-md:  0 8px 32px rgba(74,111,165,.14);
    --shadow-lg:  0 20px 60px rgba(30,45,66,.18);
  }

  .page-wrap {
    max-width: 860px;
    margin: 0 auto;
    padding: 2rem 1.25rem 5rem;
    display: flex;
    flex-direction: column;
    gap: 2.5rem;
  }

  .section { display: flex; flex-direction: column; gap: 1rem; }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: .5rem;
  }

  .section-title { display: flex; align-items: center; gap: .5rem; }

  .title-pill {
    display: inline-flex; align-items: center; gap: .35rem;
    background: var(--blue-light);
    color: var(--blue);
    font-size: .75rem; font-weight: 800;
    padding: .3rem .75rem;
    border-radius: 99px;
    border: 1.5px solid var(--blue-mid);
  }

  .count-badge {
    background: var(--blue); color: #fff;
    font-size: .7rem; font-weight: 900;
    padding: .2rem .55rem;
    border-radius: 99px;
    min-width: 1.5rem; text-align: center;
  }

  .pagination-btns { display: flex; align-items: center; gap: .4rem; }

  .page-btn {
    width: 2rem; height: 2rem;
    background: var(--surface);
    border: 1.5px solid var(--blue-mid);
    border-radius: var(--radius-md);
    display: grid; place-items: center;
    color: var(--blue);
    cursor: pointer;
    transition: background .15s, transform .15s;
  }
  .page-btn:hover:not(:disabled) { background: var(--blue-light); transform: scale(1.08); }
  .page-btn:disabled { opacity: .3; cursor: not-allowed; }

  .page-info { font-size: .72rem; font-weight: 700; color: var(--ink-muted); }

  .skeleton-list { display: flex; flex-direction: column; gap: .75rem; }
  .skeleton-card {
    height: 5rem;
    background: linear-gradient(90deg, #e8eef8 25%, #f0f4fb 50%, #e8eef8 75%);
    background-size: 200% 100%;
    animation: shimmer 1.4s infinite;
    border-radius: var(--radius-xl);
  }
  @keyframes shimmer { to { background-position: -200% 0; } }

  .empty-state {
    padding: 3rem 1rem;
    text-align: center;
    border: 2px dashed var(--blue-mid);
    border-radius: var(--radius-xl);
    color: var(--ink-muted);
    font-weight: 700; font-size: .85rem;
  }
  .empty-icon { font-size: 2.5rem; margin-bottom: .5rem; }

  .card-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: .75rem; }

  .request-card {
    background: var(--surface);
    border: 1.5px solid #e6edf8;
    border-radius: var(--radius-xl);
    padding: 1rem 1.25rem;
    display: flex; align-items: center; gap: 1rem;
    box-shadow: var(--shadow-sm);
    transition: box-shadow .2s, transform .2s, border-color .2s;
  }
  .request-card:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
    border-color: var(--blue-mid);
  }

  .avatar {
    position: relative;
    width: 2.8rem; height: 2.8rem;
    flex-shrink: 0;
  }
  .avatar img {
    width: 100%; height: 100%;
    border-radius: .75rem;
    object-fit: cover;
  }
  .avatar span {
    width: 100%; height: 100%;
    border-radius: .75rem;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; font-weight: 900;
    background: var(--blue-light);
    color: var(--blue);
  }
  .avatar-ring {
    position: absolute; inset: -3px;
    border-radius: .9rem;
    border: 2px solid var(--blue-mid);
    pointer-events: none;
    opacity: 0;
    transition: opacity .2s;
  }
  .request-card:hover .avatar-ring { opacity: 1; }

  .user-info { flex: 1; min-width: 0; }
  .user-info strong {
    display: block;
    font-size: .85rem; font-weight: 800; color: var(--ink);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .user-info span { font-size: .72rem; font-weight: 600; color: var(--ink-muted); }

  .card-actions { display: flex; gap: .4rem; flex-shrink: 0; flex-wrap: wrap; }

  .btn-ghost, .btn-accept, .btn-reject {
    display: inline-flex; align-items: center; gap: .3rem;
    padding: .38rem .75rem;
    border-radius: var(--radius-md);
    font-size: .7rem; font-weight: 800;
    cursor: pointer;
    transition: all .15s;
    border: none;
  }
  .btn-ghost { background: var(--blue-light); color: var(--blue); border: 1.5px solid var(--blue-mid); }
  .btn-ghost:hover { background: var(--blue); color: #fff; }
  .btn-accept { background: var(--green-bg); color: var(--green); border: 1.5px solid #bbf7d0; }
  .btn-accept:hover { background: var(--green); color: #fff; transform: scale(1.04); }
  .btn-reject { background: var(--red-bg); color: var(--red); border: 1.5px solid #fecaca; }
  .btn-reject:hover { background: var(--red); color: #fff; }

  .history-section { border-top: 2px dashed var(--blue-mid); padding-top: 1.5rem; }
  .history-title {
    font-size: .78rem; font-weight: 800; color: var(--ink-muted);
    display: flex; align-items: center; gap: .4rem;
    margin-bottom: .5rem;
  }
  .history-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: .4rem; }
  .history-item {
    background: rgba(255,255,255,.6);
    border: 1px solid #e8edf6;
    border-radius: var(--radius-lg);
    padding: .6rem 1rem;
    display: flex; align-items: center; gap: .75rem;
    transition: background .15s;
  }
  .history-item:hover { background: var(--surface); }

  .status-chip {
    font-size: .65rem; font-weight: 900;
    padding: .2rem .55rem;
    border-radius: 99px; flex-shrink: 0;
  }
  .chip-green { background: var(--green-bg); color: #16a34a; }
  .chip-red   { background: var(--red-bg);   color: #dc2626; }

  .history-name { flex: 1; font-size: .78rem; font-weight: 700; color: var(--ink); }
  .reset-btn {
    font-size: .65rem; font-weight: 800; color: var(--blue);
    background: none; border: none; cursor: pointer;
    text-decoration: underline; opacity: .6;
    transition: opacity .15s;
  }
  .reset-btn:hover { opacity: 1; }

  /* MODAL */
  .backdrop {
    position: fixed; inset: 0; z-index: 100;
    background: rgba(20,30,48,.45);
    backdrop-filter: blur(8px);
  }

  .modal-panel {
    position: fixed;
    top: 50%; left: 50%;
    translate: -50% -50%;
    z-index: 101;
    width: min(520px, 96vw);
    max-height: 92vh;
    background: var(--surface);
    border-radius: 2rem;
    box-shadow: var(--shadow-lg);
    border: 1.5px solid #dde6f5;
    display: flex; flex-direction: column;
    overflow: hidden;
  }

  .modal-header {
    background: linear-gradient(135deg, var(--blue) 0%, #3a5a90 100%);
    padding: 1.4rem 1.5rem;
    display: flex; align-items: center; gap: 1rem;
    color: #fff; flex-shrink: 0;
  }

  .modal-avatar {
    width: 3.2rem; height: 3.2rem; flex-shrink: 0;
    border-radius: 1rem; overflow: hidden;
    background: rgba(255,255,255,.2);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.3rem; font-weight: 900;
    border: 2px solid rgba(255,255,255,.35);
  }
  .modal-avatar img { width: 100%; height: 100%; object-fit: cover; }

  .modal-name { font-size: 1rem; font-weight: 900; margin: 0 0 .1rem; }
  .modal-sub  { font-size: .7rem; font-weight: 600; opacity: .7; margin: 0; }

  .close-btn {
    margin-right: auto;
    width: 2rem; height: 2rem;
    border-radius: 50%;
    background: rgba(255,255,255,.15);
    border: none; color: #fff;
    display: grid; place-items: center;
    cursor: pointer;
    transition: background .15s;
  }
  .close-btn:hover { background: rgba(255,255,255,.3); }

  .modal-body {
    padding: 1.5rem;
    overflow-y: auto;
    display: flex; flex-direction: column; gap: 1.25rem;
    scrollbar-width: thin;
    scrollbar-color: var(--blue-mid) transparent;
  }

  .meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: .6rem; }
  .meta-cell {
    background: var(--blue-light);
    border: 1px solid var(--blue-mid);
    border-radius: var(--radius-lg);
    padding: .7rem .9rem;
    display: flex; flex-direction: column; gap: .2rem;
  }
  .meta-cell.wide { grid-column: span 2; }
  .meta-label { font-size: .65rem; font-weight: 700; color: var(--ink-muted); }
  .meta-value { font-size: .8rem; font-weight: 800; color: var(--ink); }

  .bio-box {
    background: #fafbff;
    border: 1px solid #e8edf6;
    border-radius: var(--radius-lg);
    padding: 1rem;
  }
  .bio-label { font-size: .68rem; font-weight: 800; color: var(--blue); margin-bottom: .4rem; }
  .bio-text  { font-size: .8rem; color: var(--ink-soft); line-height: 1.7; font-style: italic; }

  .cv-section { display: flex; flex-direction: column; gap: .6rem; }
  .cv-label {
    display: flex; align-items: center; gap: .35rem;
    font-size: .75rem; font-weight: 800; color: var(--ink);
  }

  .cv-frame {
    border: 2px dashed var(--blue-mid);
    border-radius: var(--radius-xl);
    min-height: 220px;
    overflow: hidden;
    display: flex; align-items: center; justify-content: center;
    background: var(--blue-light);
  }

  .cv-image {
    width: 100%; height: auto;
    object-fit: contain;
    cursor: pointer;
    transition: opacity .2s;
    border-radius: var(--radius-lg);
  }
  .cv-image:hover { opacity: .92; }

  .cv-fallback, .cv-empty {
    text-align: center; padding: 2rem;
    display: flex; flex-direction: column; align-items: center; gap: .6rem;
  }
  .cv-fallback-icon { font-size: 2.5rem; }
  .cv-fallback p, .cv-empty p { font-size: .75rem; font-weight: 700; color: var(--ink-muted); }

  .cv-open-btn {
    display: inline-flex; align-items: center; gap: .3rem;
    padding: .5rem 1.1rem;
    background: var(--blue); color: #fff;
    border-radius: var(--radius-md);
    font-size: .72rem; font-weight: 800;
    text-decoration: none;
    transition: opacity .15s, transform .15s;
  }
  .cv-open-btn:hover { opacity: .88; transform: scale(1.03); }

  .modal-actions {
    display: flex; gap: .6rem;
    padding-top: .75rem;
    border-top: 1px solid #e8edf6;
  }

  .btn-modal-close, .btn-modal-reject, .btn-modal-approve {
    flex: 1;
    display: inline-flex; align-items: center; justify-content: center; gap: .35rem;
    padding: .75rem .5rem;
    border-radius: var(--radius-lg);
    font-size: .75rem; font-weight: 900;
    cursor: pointer; border: none;
    transition: all .15s;
  }
  .btn-modal-close { background: #f1f5f9; color: var(--ink-soft); }
  .btn-modal-close:hover { background: #e2e8f0; }
  .btn-modal-reject { background: var(--red-bg); color: var(--red); border: 1.5px solid #fecaca; }
  .btn-modal-reject:hover { background: var(--red); color: #fff; }
  .btn-modal-approve {
    flex: 2;
    background: var(--green); color: #fff;
    box-shadow: 0 4px 16px rgba(34,197,94,.3);
  }
  .btn-modal-approve:hover { filter: brightness(1.06); transform: scale(1.02); }
</style>