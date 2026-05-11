<script>
  import { onMount } from 'svelte';
  import { fade, fly, scale } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import { BookOpen, AlertTriangle, Link2, LogIn, GraduationCap } from 'lucide-svelte';

  // ─── Props ───────────────────────────────────────────────────────────────
  export let navigate = (page, id) => console.log('navigate', page, id);
  export let token = '';   // JWT token — مررّه من الـ parent

  // ─── State ───────────────────────────────────────────────────────────────
  let enrollments = [];
  let loading = true;
  let error = '';

  const BASE = 'http://127.0.0.1:8000';

  // ─── Fetch ────────────────────────────────────────────────────────────────
  onMount(async () => {
    await fetchMyLectures();
  });

  async function fetchMyLectures() {
    loading = true;
    error = '';
    try {
      const res = await fetch(`${BASE}/enrollments/my-sessions/`, {
        headers: {
          'Authorization': `Bearer ${token || localStorage.getItem('kz.token') || ''}`,
          'Content-Type': 'application/json',
        },
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `خطأ ${res.status}`);
      }

      const data = await res.json();

      // ─── نوحّد الشكل بغض النظر عن صيغة الـ response ─────────────────
      // الصيغة الجديدة (بعد تعديل الـ backend): [{session_id, session:{...}}]
      // الصيغة القديمة (قبل التعديل):            [{id, title, description, cover_image_url, ...}]
      enrollments = data.map((item) => {
        if (item.session) {
          // ✅ الصيغة الجديدة
          return {
            session_id: item.session_id,
            title:       item.session.title       ?? 'محاضرة',
            description: item.session.description ?? '',
            cover:       item.session.cover       ?? null,
            meeting_link:item.session.meeting_link?? null,
          };
        } else {
          // ✅ الصيغة القديمة (SessionResponse مباشرة)
          return {
            session_id:  item.id,
            title:       item.title               ?? 'محاضرة',
            description: item.description         ?? '',
            cover:       item.cover_image_url     ?? null,
            meeting_link:item.meeting_link        ?? null,
          };
        }
      });
    } catch (e) {
      error = e.message || 'حدث خطأ غير متوقع';
    } finally {
      loading = false;
    }
  }
</script>

<!-- ═══════════════════════════════ MARKUP ══════════════════════════════════ -->
<section class="my-lectures" in:fade={{ duration: 400 }}>

  <!-- Header -->
  <header class="lectures-header">
    <div class="header-accent"></div>
    <h2>محاضراتي <span class="header-icon"><BookOpen size={28} strokeWidth={2.5} /></span></h2>
    {#if !loading && enrollments.length > 0}
      <span class="count-badge" in:scale={{ duration: 300 }}>
        {enrollments.length}
      </span>
    {/if}
  </header>

  <!-- Loading -->
  {#if loading}
    <div class="skeleton-grid">
      {#each Array(6) as _, i}
        <div class="skeleton-card" style="animation-delay:{i * 80}ms">
          <div class="skeleton-img"></div>
          <div class="skeleton-body">
            <div class="skeleton-line w-70"></div>
            <div class="skeleton-line w-50"></div>
            <div class="skeleton-line w-90"></div>
            <div class="skeleton-btn"></div>
          </div>
        </div>
      {/each}
    </div>

  <!-- Error -->
  {:else if error}
    <div class="error-state" in:fly={{ y: 20, duration: 400 }}>
      <div class="error-icon"><AlertTriangle size={42} color="#c0392b" strokeWidth={2} /></div>
      <p class="error-msg">{error}</p>
      <button class="retry-btn" onclick={fetchMyLectures}>إعادة المحاولة</button>
    </div>

  <!-- Empty -->
  {:else if enrollments.length === 0}
    <div class="empty-state" in:fly={{ y: 30, duration: 500 }}>
      <div class="empty-illustration">
        <GraduationCap size={64} color="var(--primary)" strokeWidth={1.5} />
      </div>
      <p class="empty-title">ما عندك محاضرات حالياً</p>
      <p class="empty-sub">انضم لمحاضرة وستظهر هنا فور قبول طلبك</p>
    </div>

  <!-- Grid -->
  {:else}
    <div class="lectures-grid">
      {#each enrollments as item, i (item.session_id)}
        <article
          class="lecture-card"
          in:fly={{ y: 40, delay: i * 70, duration: 450, easing: cubicOut }}
        >
          <!-- Cover -->
          <div class="card-cover">
            {#if item.cover}
              <img
                src={`${BASE}/pics/${item.cover}`}
                alt={item.title}
                loading="lazy"
                onerror={(e) => { e.target.style.display='none'; e.target.nextElementSibling.style.display='flex'; }}
              />
              <div class="cover-fallback" style="display:none"><BookOpen size={48} color="white" strokeWidth={1.5} /></div>
            {:else}
              <div class="cover-fallback"><BookOpen size={48} color="white" strokeWidth={1.5} /></div>
            {/if}
            <div class="cover-overlay"></div>
            <span class="card-num">{String(i + 1).padStart(2, '0')}</span>
          </div>

          <!-- Body -->
          <div class="card-body">
            <h3 class="card-title" title={item.title}>{item.title}</h3>
            <p class="card-desc">
              {item.description || 'لا يوجد وصف للمحاضرة'}
            </p>

            <div class="card-footer">
              {#if item.meeting_link}
                <a
                  href={item.meeting_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  class="btn btn-link"
                  title="رابط الاجتماع"
                >
                  <Link2 size={18} strokeWidth={2.5} />
                </a>
              {/if}
              <button
                class="btn btn-enter"
                onclick={() => navigate('session_view', item.session_id)}
              >
                <LogIn size={16} strokeWidth={2.5} />
                دخول للمحاضرة
              </button>
            </div>
          </div>
        </article>
      {/each}
    </div>
  {/if}
</section>

<!-- ═══════════════════════════════ STYLES ══════════════════════════════════ -->
<style>
  /* ── Tokens ── */
  :root {
    --primary:   #6b8cce;
    --dark:      #2a3c54;
    --light-bg:  #f5f7fc;
    --card-bg:   #ffffff;
    --border:    #e8edf5;
    --muted:     #8a96a8;
    --radius:    2.5rem;
    --radius-sm: 0.875rem;
    --shadow-sm: 0 2px 8px rgba(42,60,84,.06);
    --shadow-lg: 0 16px 48px rgba(42,60,84,.14);
    --trans:     all .35s cubic-bezier(.4,0,.2,1);
  }

  /* ── Section ── */
  .my-lectures {
    padding: 2rem 0 4rem;
    direction: rtl;
  }

  /* ── Header ── */
  .lectures-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 2.5rem;
    position: relative;
  }
  .header-accent {
    width: 10px;
    height: 2.6rem;
    background: linear-gradient(to bottom, var(--primary), var(--dark));
    border-radius: 99px;
    flex-shrink: 0;
  }
  .lectures-header h2 {
    font-size: clamp(1.6rem, 4vw, 2.4rem);
    font-weight: 900;
    color: var(--dark);
    margin: 0;
    letter-spacing: -.02em;
  }
  .header-icon {
    display: inline-flex;
    align-items: center;
    vertical-align: middle;
    color: var(--primary);
    margin-right: .25rem;
  }
  .count-badge {
    background: var(--primary);
    color: #fff;
    font-size: .8rem;
    font-weight: 800;
    padding: .25em .65em;
    border-radius: 99px;
    margin-right: .25rem;
    line-height: 1.5;
  }

  /* ── Grid ── */
  .lectures-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1.75rem;
  }

  /* ── Card ── */
  .lecture-card {
    background: var(--card-bg);
    border-radius: var(--radius);
    border: 1px solid var(--border);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    box-shadow: var(--shadow-sm);
    transition: var(--trans);
    position: relative;
  }
  .lecture-card:hover {
    transform: translateY(-6px) scale(1.015);
    box-shadow: var(--shadow-lg);
    border-color: rgba(107,140,206,.3);
  }

  /* Cover */
  .card-cover {
    position: relative;
    height: 190px;
    background: var(--light-bg);
    overflow: hidden;
    flex-shrink: 0;
  }
  .card-cover img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform .6s ease;
    display: block;
  }
  .lecture-card:hover .card-cover img {
    transform: scale(1.08);
  }
  .cover-fallback {
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, var(--primary), var(--dark));
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .cover-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(to top, rgba(42,60,84,.55) 0%, transparent 55%);
    pointer-events: none;
  }
  .card-num {
    position: absolute;
    top: .9rem;
    left: .9rem;
    background: rgba(255,255,255,.18);
    backdrop-filter: blur(8px);
    color: #fff;
    font-size: .7rem;
    font-weight: 800;
    padding: .25em .55em;
    border-radius: 99px;
    border: 1px solid rgba(255,255,255,.25);
    letter-spacing: .05em;
  }

  /* Body */
  .card-body {
    padding: 1.35rem 1.5rem 1.5rem;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: .6rem;
  }
  .card-title {
    font-size: 1.05rem;
    font-weight: 900;
    color: var(--dark);
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    overflow: hidden;
    letter-spacing: -.01em;
  }
  .card-desc {
    font-size: .85rem;
    color: var(--muted);
    font-weight: 600;
    line-height: 1.55;
    margin: 0;
    flex: 1;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  /* Footer */
  .card-footer {
    display: flex;
    gap: .6rem;
    align-items: center;
    margin-top: .4rem;
  }
  .btn {
    border: none;
    cursor: pointer;
    font-weight: 800;
    transition: var(--trans);
    border-radius: var(--radius-sm);
    font-family: inherit;
  }
  .btn-enter {
    flex: 1;
    padding: .75rem 1rem;
    background: var(--primary);
    color: #fff;
    font-size: .875rem;
    letter-spacing: .01em;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: .4rem;
  }
  .btn-enter:hover {
    background: var(--dark);
    transform: scale(1.04);
  }
  .btn-enter:active {
    transform: scale(.97);
  }
  .btn-link {
    padding: .7rem .85rem;
    background: var(--light-bg);
    color: var(--dark);
    font-size: 1rem;
    border: 1px solid var(--border);
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .btn-link:hover {
    background: var(--border);
    transform: scale(1.06);
  }

  /* ── Skeleton ── */
  .skeleton-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1.75rem;
  }
  .skeleton-card {
    background: var(--card-bg);
    border-radius: var(--radius);
    border: 1px solid var(--border);
    overflow: hidden;
    animation: pulse 1.5s ease-in-out infinite both;
  }
  .skeleton-img {
    height: 190px;
    background: linear-gradient(90deg, #eef0f5 25%, #f5f7fc 50%, #eef0f5 75%);
    background-size: 200% 100%;
    animation: shimmer 1.6s infinite;
  }
  .skeleton-body {
    padding: 1.35rem 1.5rem 1.5rem;
    display: flex;
    flex-direction: column;
    gap: .7rem;
  }
  .skeleton-line {
    height: .85rem;
    background: #eef0f5;
    border-radius: 99px;
  }
  .w-70  { width: 70%; }
  .w-50  { width: 50%; }
  .w-90  { width: 90%; }
  .skeleton-btn {
    height: 2.6rem;
    background: #eef0f5;
    border-radius: var(--radius-sm);
    margin-top: .4rem;
  }
  @keyframes shimmer {
    0%   { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: .75; }
  }

  /* ── Empty ── */
  .empty-state {
    padding: 5rem 2rem;
    text-align: center;
    background: var(--card-bg);
    border-radius: var(--radius);
    border: 2px dashed var(--border);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }
  .empty-illustration {
    margin-bottom: .5rem;
    opacity: .7;
  }
  .empty-title {
    font-size: 1.25rem;
    font-weight: 900;
    color: var(--dark);
    margin: 0;
  }
  .empty-sub {
    font-size: .9rem;
    color: var(--muted);
    font-weight: 600;
    margin: 0;
  }

  /* ── Error ── */
  .error-state {
    padding: 4rem 2rem;
    text-align: center;
    background: #fff8f8;
    border-radius: var(--radius);
    border: 2px solid #fde8e8;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }
  .error-icon { display: flex; justify-content: center; }
  .error-msg  { font-size: .95rem; font-weight: 700; color: #c0392b; margin: 0; }
  .retry-btn  {
    padding: .65rem 1.5rem;
    background: var(--dark);
    color: #fff;
    border: none;
    border-radius: var(--radius-sm);
    font-weight: 800;
    font-size: .875rem;
    cursor: pointer;
    transition: var(--trans);
    font-family: inherit;
  }
  .retry-btn:hover { background: var(--primary); transform: scale(1.04); }

  /* ── Responsive ── */
  @media (max-width: 640px) {
    .lectures-grid, .skeleton-grid {
      grid-template-columns: 1fr;
    }
    .lecture-card {
      border-radius: 1.5rem;
    }
    .empty-state {
      padding: 3rem 1.5rem;
    }
  }
</style>