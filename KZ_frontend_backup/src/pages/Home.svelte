<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, fly, scale } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import {
    Search, BookOpen, ChevronLeft, ChevronRight,
    ArrowLeft, Users, GraduationCap, AlertCircle,
    Inbox, SlidersHorizontal, UserCircle, Layers, Star
  } from 'lucide-svelte';
  import api from '../lib/api';
  import { navigate } from '../lib/router';
  import { notify } from '../lib/notifications';
  import type { Session, Category, User } from '../lib/types';

  // ── Types ────────────────────────────────────────────────────────────────
  interface CourseGroup {
    id: number;
    course_title: string;
    description: string | null;
    display_cover: string | null;
    teacher_name: string | null;
    teacher_id: number | null;
    categories: Category[];
    session_count: number;
  }

  interface TeacherProfile {
    id: number;
    name: string;
    bio: string;
    image: string | null;
    avg_rating: number;
    ratings_count: number;
  }

  // ── State ────────────────────────────────────────────────────────────────
  let courses     = $state<CourseGroup[]>([]);
  let categories  = $state<Category[]>([]);
  let allTeachers = $state<TeacherProfile[]>([]);
  let isLoading   = $state(true);

  // Search Terms
  let searchTerm        = $state('');
  let teacherSearchTerm = $state('');

  let selectedCatId = $state<number | null>(null);

  // Pagination
  let catPage      = $state(0);
  let coursePage   = $state(0);
  let teacherPage  = $state(0);

  const itemsPerPage    = 6;
  const teachersPerPage = 4;

  // ── Load ─────────────────────────────────────────────────────────────────
  async function loadData(): Promise<void> {
    isLoading = true;
    try {
      const [sRes, cRes, tRes] = await Promise.all([
        api.get<Session[]>('/sessions/').catch(() => ({ data: [] as Session[] })),
        api.get<Category[]>('/sessions/categories/').catch(() => ({ data: [] as Category[] })),
        // نستخدم نفس المسار مالتج بس نتوقع يرجع بيانات المعلم مباشرة
        api.get<any[]>('/teachers/').catch(() => ({ data: [] as any[] })),
      ]);

      const groups: Record<string, CourseGroup> = {};
      for (const s of sRes.data) {
        if (!s.title) continue;
        const courseTitle = s.title.includes(' - ')
          ? s.title.split(' - ')[0].trim()
          : s.title.trim();
        const key = `${courseTitle}::${s.teacher_name ?? '?'}`;
        if (!groups[key]) {
          groups[key] = {
            id: s.id,
            course_title: courseTitle,
            description: s.description,
            display_cover: s.cover_image_url,
            teacher_name: s.teacher_name,
            teacher_id: (s as any).user_id ?? s.teacher_id ?? null,
            categories: s.categories ?? [],
            session_count: 0,
          };
        }
        groups[key].session_count += 1;
      }

      courses = Object.values(groups).sort((a, b) =>
        a.course_title.localeCompare(b.course_title, 'ar'),
      );
      categories = cRes.data;
      
      // مطابقة البيانات حتى تشتغل بغض النظر عن شكل الـ API القديم أو الجديد
      allTeachers = (tRes.data ?? []).map((t: any) => ({
        id: t.id,
        name: t.name || `${t.firstname || ''} ${t.lastname || ''}`.trim(),
        bio: t.bio || '',
        image: t.image || t.profile_image || null,
        avg_rating: t.avg_rating || 0,
        ratings_count: t.ratings_count || 0
      })).filter(t => t.name);

    } catch {
      notify.error('تعذّر تحميل الصفحة الرئيسية، يرجى المحاولة لاحقاً');
    } finally {
      isLoading = false;
    }
  }

  // ── Derived ───────────────────────────────────────────────────────────────
  let filteredCourses = $derived(
    courses.filter((c) => {
      const matchesSearch = c.course_title.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCat = selectedCatId === null || c.categories.some((x) => x.id === selectedCatId);
      return matchesSearch && matchesCat;
    }),
  );

  let visibleCats      = $derived(categories.slice(catPage * itemsPerPage, (catPage + 1) * itemsPerPage));
  let visibleCourses   = $derived(filteredCourses.slice(coursePage * itemsPerPage, (coursePage + 1) * itemsPerPage));
  let totalCoursePages = $derived(Math.ceil(filteredCourses.length / itemsPerPage));

  // فلترة وتقسيم المعلمين
  let filteredTeachers = $derived(
    allTeachers.filter(t => t.name.toLowerCase().includes(teacherSearchTerm.toLowerCase()))
  );
  let visibleTeachers   = $derived(filteredTeachers.slice(teacherPage * teachersPerPage, (teacherPage + 1) * teachersPerPage));
  let totalTeacherPages = $derived(Math.ceil(filteredTeachers.length / teachersPerPage));

  // ── Actions ───────────────────────────────────────────────────────────────
  function openCourse(c: CourseGroup)      { navigate('session_view', c.course_title); }
  function openTeacher(id: number)         { navigate('teacher_view', id); }
  function selectCategory(id: number|null) { selectedCatId = id; coursePage = 0; }
  function scrollToTop()                   { window.scrollTo({ top: 0, behavior: 'smooth' }); }

  function hideBrokenImg(e: Event) {
    const img = e.currentTarget as HTMLImageElement;
    img.style.display = 'none';
    const fallback = img.nextElementSibling as HTMLElement | null;
    if (fallback) fallback.style.display = 'flex';
  }

  function hideTeacherImg(e: Event) {
    const img = e.currentTarget as HTMLImageElement;
    img.style.display = 'none';
    const fallback = img.nextElementSibling as HTMLElement | null;
    if (fallback) fallback.style.display = 'flex';
  }

  onMount(loadData);
</script>

<div class="home-page" dir="rtl">

  <section class="search-section">
    <div class="search-inner">
      <div class="hero-text">
        <h1>اكتشف علماً <span class="accent">ينتفع به</span></h1>
      </div>

      <div class="search-bar-wrap">
        <span class="search-icon"><Search size={20} strokeWidth={2.5} /></span>
        <input
          bind:value={searchTerm}
          oninput={() => (coursePage = 0)}
          placeholder="ابحث عن محاضرة أو موضوع..."
          class="search-input"
          aria-label="البحث"
        />
        {#if searchTerm}
          <button class="search-clear" onclick={() => { searchTerm = ''; coursePage = 0; }}>✕</button>
        {/if}
      </div>

      {#if categories.length > 0}
        <div class="cats-row">
          <button class="cat-nav" disabled={catPage === 0} onclick={() => catPage--} aria-label="السابق">
            <ChevronRight size={18} />
          </button>

          <div class="cats-chips">
            <button class="chip {selectedCatId === null ? 'chip--active' : ''}" onclick={() => selectCategory(null)}>
              <Layers size={13} strokeWidth={2.5} /> الكل
            </button>
            {#each visibleCats as cat (cat.id)}
              <button class="chip {selectedCatId === cat.id ? 'chip--active' : ''}" onclick={() => selectCategory(cat.id)}>
                {cat.category_name}
              </button>
            {/each}
          </div>

          <button class="cat-nav" disabled={(catPage + 1) * itemsPerPage >= categories.length} onclick={() => catPage++} aria-label="التالي">
            <ChevronLeft size={18} />
          </button>
        </div>
      {/if}
    </div>
  </section>

  {#if isLoading}
    <div class="container">
      <div class="courses-grid">
        {#each Array(6) as _, i}
          <div class="skeleton-card" style="animation-delay:{i*80}ms">
            <div class="skeleton-img"></div>
            <div class="skeleton-body">
              <div class="skel-line w-65"></div>
              <div class="skel-line w-90"></div>
              <div class="skel-line w-50"></div>
              <div class="skeleton-footer">
                <div class="skel-circle"></div>
                <div class="skel-btn"></div>
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>

  {:else}
    <div class="container">

      <section class="section" in:fade={{ duration: 400 }}>
        <div class="section-header">
          <div class="section-title-group">
            <div class="section-accent"></div>
            <h2 class="section-title">
              <BookOpen size={26} strokeWidth={2} class="title-icon" />
              استكشف المحاضرات العلمية
            </h2>
          </div>
          {#if filteredCourses.length > 0}
            <span class="results-count">{filteredCourses.length} محاضرة</span>
          {/if}
        </div>

        {#if filteredCourses.length === 0}
          <div class="empty-state" in:fly={{ y: 24, duration: 400 }}>
            <div class="empty-icon">
              <Inbox size={52} strokeWidth={1.2} color="var(--primary)" />
            </div>
            <p class="empty-title">
              {searchTerm || selectedCatId ? 'لا توجد نتائج تطابق بحثك' : 'لا توجد محاضرات متاحة حالياً'}
            </p>
            {#if searchTerm || selectedCatId}
              <button class="btn-reset" onclick={() => { searchTerm = ''; selectedCatId = null; coursePage = 0; }}>
                <SlidersHorizontal size={15} /> عرض كل المحاضرات
              </button>
            {/if}
          </div>

        {:else}
          <div class="courses-grid">
            {#each visibleCourses as c, i (c.id + c.course_title)}
              <div
                class="course-card-clickable"
                onclick={() => openCourse(c)}
                onkeydown={(e) => e.key === 'Enter' && openCourse(c)}
                role="button"
                tabindex="0"
                in:fly={{ y: 36, delay: i * 60, duration: 420, easing: cubicOut }}
              >
                <div class="card-cover">
                  {#if c.display_cover}
                    <img src={`http://127.0.0.1:8000/pics/${c.display_cover}`} alt={c.course_title} onerror={hideBrokenImg} />
                  {/if}
                  <div class="cover-fallback" style={c.display_cover ? 'display:none' : 'display:flex'}>
                    <BookOpen size={52} color="white" strokeWidth={1.2} />
                  </div>
                  <div class="cover-overlay"></div>
                  <span class="sessions-badge">
                    <Layers size={12} strokeWidth={2.5} /> عدد المحاضرات : {c.session_count}
                  </span>
                </div>

                <div class="card-body">
                  <h3 class="card-title">{c.course_title}</h3>
                  <p class="card-desc">{c.description || 'لا يوجد وصف متاح حالياً.'}</p>

                  <div class="card-footer">
                      <button
                        type="button"
                        class="teacher-btn"
                        onclick={(e) => { e.stopPropagation(); if (c.teacher_id) openTeacher(c.teacher_id); }}
                        disabled={!c.teacher_id}
                        aria-label="عرض ملف {c.teacher_name}"
                      >
                        <div class="teacher-avatar">
                          {#if c.teacher_id}
                            <img src={`http://127.0.0.1:8000/users/${c.teacher_id}/profile_image`} alt={c.teacher_name ?? 'معلم'} onerror={hideTeacherImg} />
                            <div class="avatar-fallback" style="display:none"><UserCircle size={28} color="var(--primary)" strokeWidth={1.5} /></div>
                          {:else}
                            <div class="avatar-fallback" style="display:flex"><UserCircle size={28} color="var(--primary)" strokeWidth={1.5} /></div>
                          {/if}
                        </div>
                        <div class="teacher-info">
                          <span class="teacher-label">المحاضر</span>
                          <span class="teacher-name">{c.teacher_name ?? '—'}</span>
                        </div>
                      </button>
                  </div>
                </div>

                <div class="card-footer-action">
                  عرض التفاصيل <ChevronLeft size={16} strokeWidth={2.5} />
                </div>
              </div> {/each}
          </div>

          {#if totalCoursePages > 1}
            <div class="pagination">
              <button class="page-btn page-btn--outline" disabled={coursePage === 0} onclick={() => { coursePage--; scrollToTop(); }}>
                <ChevronRight size={16} /> السابق
              </button>
              <div class="page-dots">
                {#each Array(totalCoursePages) as _, i}
                  <button class="dot {coursePage === i ? 'dot--active' : ''}" onclick={() => { coursePage = i; scrollToTop(); }} aria-label="الصفحة {i + 1}">{i + 1}</button>
                {/each}
              </div>
              <button class="page-btn page-btn--filled" disabled={coursePage + 1 >= totalCoursePages} onclick={() => { coursePage++; scrollToTop(); }}>
                التالي <ChevronLeft size={16} />
              </button>
            </div>
          {/if}
        {/if}
      </section>

      {#if allTeachers.length > 0}
        <section class="section teachers-section" in:fade={{ duration: 400, delay: 200 }}>
          <div class="section-header mb-6">
            <div class="section-title-group">
              <div class="section-accent"></div>
              <div>
                <h2 class="section-title"><GraduationCap size={26} strokeWidth={2} class="title-icon" /> المعلمون في المنصة</h2>
                <p class="section-sub">نخبة من الأساتذة والخبراء المساهمين في زكاة العلم</p>
              </div>
            </div>
            
            <div class="teacher-search-wrap">
              <Search size={16} class="t-search-icon" />
              <input 
                bind:value={teacherSearchTerm} 
                oninput={() => teacherPage = 0} 
                placeholder="ابحث عن معلم..." 
                class="t-search-input"
              />
              {#if teacherSearchTerm}
                <button class="t-search-clear" onclick={() => { teacherSearchTerm = ''; teacherPage = 0; }}><SlidersHorizontal size={14} /></button>
              {/if}
            </div>
          </div>

          {#if filteredTeachers.length === 0}
            <div class="text-center py-10 text-slate-400 font-bold" in:fade>لا يوجد معلم بهذا الاسم</div>
          {:else}
            <div class="teachers-grid">
              {#each visibleTeachers as teacher, i (teacher.id)}
                <button type="button" onclick={() => openTeacher(teacher.id)} class="teacher-card teacher-float-card" in:fly={{ y: 28, delay: i * 70, duration: 380, easing: cubicOut }}>
                  <div class="tcard-avatar">
                    {#if teacher.image && teacher.image !== "data:image/jpeg;base64,null"}
                      <img src={teacher.image} alt={teacher.name} onerror={hideTeacherImg} />
                      <div class="avatar-fallback" style="display:none"><UserCircle size={52} color="var(--primary)" strokeWidth={1.2} /></div>
                    {:else}
                      <div class="avatar-fallback" style="display:flex"><UserCircle size={52} color="var(--primary)" strokeWidth={1.2} /></div>
                    {/if}
                  </div>
                  <h4 class="tcard-name">{teacher.name}</h4>
                  
                  <div class="flex items-center justify-center gap-1.5 mt-1 w-full">
                    <Star size={14} class={teacher.avg_rating > 0 ? "fill-amber-400 text-amber-400" : "text-slate-300"} />
                    <span class="text-xs font-black text-slate-700">{teacher.avg_rating > 0 ? teacher.avg_rating : 'جديد'}</span>
                    <span class="text-[10px] text-slate-400 font-bold">({teacher.ratings_count} تقييم)</span>
                  </div>

                  <p class="tcard-bio">{teacher.bio || 'معلم شغوف بنشر العلم'}</p>
                  <span class="tcard-cta"><Users size={13} strokeWidth={2.5} /> عرض الملف الشخصي</span>
                </button>
              {/each}
            </div>

            {#if totalTeacherPages > 1}
              <div class="teacher-pagination mt-8 flex justify-center items-center gap-3">
                <button class="t-page-btn" disabled={teacherPage === 0} onclick={() => teacherPage--}><ChevronRight size={16} /></button>
                <div class="flex gap-2">
                  {#each Array(totalTeacherPages) as _, i}
                    <button class="t-dot {teacherPage === i ? 'active' : ''}" onclick={() => teacherPage = i} aria-label="انتقل لصفحة المعلمين {i + 1}"></button>
                  {/each}
                </div>
                <button class="t-page-btn" disabled={teacherPage + 1 >= totalTeacherPages} onclick={() => teacherPage++}><ChevronLeft size={16} /></button>
              </div>
            {/if}
          {/if}
        </section>
      {/if}

    </div>
  {/if}
</div>

<style>
  /* ── Tokens ─────────────────────────────────────────────────────────────── */
  :root {
    --primary:    #6b8cce;
    --dark:       #2a3c54;
    --light-bg:   #f4f6fb;
    --card-bg:    #ffffff;
    --border:     #e8edf5;
    --muted:      #8a96a8;
    --radius-xl:  2.5rem;
    --radius-lg:  1.75rem;
    --radius-md:  1rem;
    --shadow-sm:  0 2px 10px rgba(42,60,84,.06);
    --shadow-lg:  0 20px 60px rgba(42,60,84,.13);
    --trans:      all .32s cubic-bezier(.4,0,.2,1);
  }

  /* ── Page ───────────────────────────────────────────────────────────────── */
  .home-page { min-height: 100vh; background: var(--light-bg); direction: rtl; font-family: 'Tajawal', 'Cairo', sans-serif; }
  .container { max-width: 1280px; margin: 0 auto; padding: 3rem 1.5rem 5rem; display: flex; flex-direction: column; gap: 5rem; }

  /* ── Search hero ─────────────────────────────────────────────────────────── */
  .search-section { background: linear-gradient(160deg, var(--dark) 0%, #1e3048 60%, #2d4a6a 100%); padding: 4rem 1.5rem 3.5rem; position: relative; overflow: hidden; }
  .search-section::before { content: ''; position: absolute; inset: 0; background: radial-gradient(circle at 20% 50%, rgba(107,140,206,.18) 0%, transparent 60%), radial-gradient(circle at 80% 20%, rgba(107,140,206,.12) 0%, transparent 50%); pointer-events: none; }
  .search-section::after { content: ''; position: absolute; bottom: -1px; left: 0; right: 0; height: 2.5rem; background: var(--light-bg); clip-path: ellipse(55% 100% at 50% 100%); }
  .search-inner { max-width: 860px; margin: 0 auto; display: flex; flex-direction: column; align-items: center; gap: 2rem; position: relative; z-index: 1; }
  .hero-text { text-align: center; color: white; }
  .hero-text h1 { font-size: clamp(1.8rem, 5vw, 3rem); font-weight: 900; margin: 0 0 .6rem; letter-spacing: -.02em; line-height: 1.2; }
  .accent { color: #a8c0e8; }
  .search-bar-wrap { width: 100%; position: relative; display: flex; align-items: center; }
  .search-icon { position: absolute; right: 1.25rem; color: rgba(255,255,255,.45); display: flex; pointer-events: none; }
  .search-input { width: 100%; background: rgba(255,255,255,.1); border: 1.5px solid rgba(255,255,255,.15); color: white; padding: 1rem 3rem 1rem 3rem; border-radius: var(--radius-xl); font-size: 1rem; font-weight: 600; outline: none; transition: var(--trans); text-align: right; font-family: inherit; backdrop-filter: blur(8px); }
  .search-input::placeholder { color: rgba(255,255,255,.35); }
  .search-input:focus { background: rgba(255,255,255,.16); border-color: rgba(107,140,206,.7); box-shadow: 0 0 0 4px rgba(107,140,206,.15); }
  .search-clear { position: absolute; left: 1.1rem; color: rgba(255,255,255,.5); background: none; border: none; cursor: pointer; font-size: .9rem; padding: .25rem; transition: var(--trans); }
  .search-clear:hover { color: white; }

  /* Category chips */
  .cats-row { display: flex; align-items: center; gap: .75rem; width: 100%; overflow: hidden; }
  .cat-nav { width: 2.4rem; height: 2.4rem; border-radius: .75rem; background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.15); color: white; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: var(--trans); }
  .cat-nav:hover:not(:disabled) { background: rgba(255,255,255,.2); }
  .cat-nav:disabled { opacity: .25; cursor: not-allowed; }
  .cats-chips { display: flex; gap: .5rem; overflow-x: auto; padding: .25rem .1rem; scrollbar-width: none; flex: 1; }
  .cats-chips::-webkit-scrollbar { display: none; }
  .chip { padding: .5rem 1.1rem; border-radius: 99px; border: 1.5px solid rgba(255,255,255,.2); background: rgba(255,255,255,.08); color: rgba(255,255,255,.75); font-size: .8rem; font-weight: 700; white-space: nowrap; cursor: pointer; transition: var(--trans); display: inline-flex; align-items: center; gap: .35rem; font-family: inherit; }
  .chip:hover { background: rgba(255,255,255,.15); color: white; }
  .chip--active { background: white; color: var(--dark); border-color: white; box-shadow: 0 4px 12px rgba(0,0,0,.15); }

  /* ── Sections ────────────────────────────────────────────────────────────── */
  .section { display: flex; flex-direction: column; gap: 2rem; }
  .section-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
  .section-title-group { display: flex; align-items: center; gap: .9rem; }
  .section-accent { width: 6px; height: 2.2rem; background: linear-gradient(to bottom, var(--primary), var(--dark)); border-radius: 99px; flex-shrink: 0; }
  .section-title { font-size: clamp(1.4rem, 3.5vw, 2rem); font-weight: 900; color: var(--dark); margin: 0; letter-spacing: -.02em; display: flex; align-items: center; gap: .5rem; }
  :global(.title-icon) { color: var(--primary); flex-shrink: 0; }
  .section-sub { font-size: .875rem; color: var(--muted); font-weight: 600; margin: .3rem 0 0; }
  .results-count { background: var(--border); color: var(--muted); font-size: .78rem; font-weight: 800; padding: .3em .8em; border-radius: 99px; align-self: center; }

  /* ── Courses grid ───────────────────────────────────────── */
  .courses-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; }
  .course-card-clickable { background: var(--card-bg); border-radius: var(--radius-xl); border: 1px solid var(--border); overflow: hidden; display: flex; flex-direction: column; box-shadow: var(--shadow-sm); transition: var(--trans); text-align: right; cursor: pointer; width: 100%; padding: 0; font-family: inherit; }
  .course-card-clickable:hover { transform: translateY(-6px); box-shadow: var(--shadow-lg); border-color: rgba(107,140,206,.25); }
  .card-cover { height: 210px; position: relative; overflow: hidden; background: var(--light-bg); display: block; width: 100%; flex-shrink: 0; }
  .card-cover img { width: 100%; height: 100%; object-fit: cover; display: block; transition: transform .6s ease; }
  .course-card-clickable:hover .card-cover img { transform: scale(1.07); }
  .cover-fallback { width: 100%; height: 100%; background: linear-gradient(135deg, var(--primary) 0%, var(--dark) 100%); align-items: center; justify-content: center; position: absolute; inset: 0; }
  .cover-overlay { position: absolute; inset: 0; background: linear-gradient(to top, rgba(42,60,84,.6) 0%, transparent 50%); pointer-events: none; }
  .sessions-badge { position: absolute; top: .85rem; right: .85rem; background: rgba(255,255,255,.92); backdrop-filter: blur(8px); color: var(--dark); font-size: .72rem; font-weight: 800; padding: .35em .75em; border-radius: 99px; display: inline-flex; align-items: center; gap: .3rem; box-shadow: 0 2px 10px rgba(0,0,0,.1); }

  .card-body { padding: 1.4rem 1.5rem 1rem; flex: 1; display: flex; flex-direction: column; gap: .6rem; }
  .card-title { font-size: 1.1rem; font-weight: 900; color: var(--dark); margin: 0; display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden; }
  .card-desc { font-size: .83rem; color: var(--muted); font-weight: 500; line-height: 1.6; margin: 0; flex: 1; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .card-footer { display: flex; align-items: center; justify-content: space-between; padding-top: .85rem; margin-top: .25rem; border-top: 1px dashed var(--border); }
  .teacher-btn { display: flex; align-items: center; gap: .7rem; background: none; border: none; cursor: pointer; padding: 0; transition: var(--trans); font-family: inherit; position: relative; z-index: 2; }
  .teacher-btn:hover:not(:disabled) { opacity: .75; }
  .teacher-avatar { width: 2.6rem; height: 2.6rem; border-radius: .75rem; background: var(--light-bg); overflow: hidden; border: 2px solid var(--border); position: relative; flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
  .teacher-avatar img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .avatar-fallback { position: absolute; inset: 0; align-items: center; justify-content: center; background: var(--light-bg); }
  .teacher-info { display: flex; flex-direction: column; text-align: right; gap: .1rem; }
  .teacher-label { font-size: .65rem; color: var(--muted); font-weight: 700; text-transform: uppercase; }
  .teacher-name { font-size: .875rem; font-weight: 800; color: var(--dark); max-width: 140px; display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden; }
  .card-footer-action { display: flex; align-items: center; justify-content: flex-start; gap: .4rem; padding: .85rem 1.5rem 1.1rem; background: rgba(107, 140, 206, 0.03); border-top: 1px solid var(--border); font-size: .85rem; font-weight: 800; color: var(--primary); transition: var(--trans); }
  .course-card-clickable:hover .card-footer-action { background: rgba(107, 140, 206, 0.08); padding-right: 1.1rem; }

  /* ── Empty state ──────────────────────────────────────────────────────────── */
  .empty-state { padding: 5rem 2rem; text-align: center; background: var(--card-bg); border-radius: var(--radius-xl); border: 2px dashed var(--border); display: flex; flex-direction: column; align-items: center; gap: 1rem; }
  .empty-icon { opacity: .5; }
  .empty-title { font-size: 1.1rem; font-weight: 800; color: var(--dark); margin: 0; }
  .btn-reset { margin-top: .5rem; padding: .65rem 1.5rem; background: var(--dark); color: white; border: none; border-radius: var(--radius-md); font-weight: 800; font-size: .875rem; cursor: pointer; transition: var(--trans); display: inline-flex; align-items: center; gap: .45rem; font-family: inherit; }
  .btn-reset:hover { background: var(--primary); transform: scale(1.04); }

  /* ── Pagination ──────────────────────────────────────────────────────────── */
  .pagination { display: flex; align-items: center; justify-content: center; gap: .75rem; padding-top: 1rem; flex-wrap: wrap; }
  .page-btn { padding: .6rem 1.4rem; border-radius: var(--radius-md); font-weight: 800; font-size: .85rem; cursor: pointer; transition: var(--trans); display: inline-flex; align-items: center; gap: .35rem; font-family: inherit; border: none; }
  .page-btn--outline { background: var(--card-bg); color: var(--dark); border: 1.5px solid var(--border); box-shadow: var(--shadow-sm); }
  .page-btn--outline:hover:not(:disabled) { border-color: var(--primary); color: var(--primary); }
  .page-btn--filled { background: var(--dark); color: white; }
  .page-btn--filled:hover:not(:disabled) { background: var(--primary); }
  .page-btn:disabled { opacity: .3; cursor: not-allowed; }
  .page-dots { display: flex; gap: .4rem; }
  .dot { width: 2.2rem; height: 2.2rem; border-radius: .6rem; font-weight: 800; font-size: .8rem; cursor: pointer; transition: var(--trans); border: none; background: var(--card-bg); color: var(--muted); font-family: inherit; }
  .dot:hover { background: var(--border); color: var(--dark); }
  .dot--active { background: var(--dark); color: white; transform: scale(1.1); }

  /* ── Teachers ─────────────────────────────────────────────────────────────── */
  .teachers-section { background: linear-gradient(135deg, #f0f4fb 0%, #e8eef8 100%); border-radius: var(--radius-xl); padding: 2.5rem; border: 1px solid var(--border); }
  
  .teacher-search-wrap { display: flex; align-items: center; background: white; border: 1.5px solid var(--border); border-radius: 1rem; padding: 0.5rem 1rem; width: 100%; max-width: 300px; position: relative; transition: var(--trans); }
  .teacher-search-wrap:focus-within { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(107,140,206,.15); }
  
  .t-search-input { border: none; outline: none; width: 100%; font-family: inherit; font-size: 0.85rem; font-weight: 700; color: var(--dark); background: transparent; }
  .t-search-clear { background: none; border: none; color: var(--muted); cursor: pointer; padding: 0; }
  .t-search-clear:hover { color: var(--primary); }

  .teachers-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 1.25rem; }
  
  /* 👈 الانيميشن الجديد هنا */
  .teacher-float-card { 
    background: var(--card-bg); 
    border-radius: var(--radius-lg); 
    border: 1px solid var(--border); 
    padding: 1.75rem 1.5rem; 
    display: flex; 
    flex-direction: column; 
    align-items: center; 
    text-align: center; 
    cursor: pointer; 
    font-family: inherit; 
    transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.4s ease, border-color 0.4s ease;
    transform-style: preserve-3d;
    perspective: 1000px;
  }
  .teacher-float-card:hover { 
    transform: translateY(-8px) scale(1.02) rotateX(4deg) rotateY(-2deg); 
    box-shadow: 0 25px 50px -12px rgba(107, 140, 206, 0.3); 
    border-color: rgba(107,140,206,.4); 
  }
  
  .tcard-avatar { width: 5.5rem; height: 5.5rem; border-radius: 1.5rem; overflow: hidden; border: 3px solid var(--light-bg); background: var(--light-bg); position: relative; flex-shrink: 0; display: flex; align-items: center; justify-content: center; transition: transform .4s ease; }
  .teacher-float-card:hover .tcard-avatar { transform: translateZ(20px) scale(1.08); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
  .tcard-avatar img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .tcard-name { font-size: 1.1rem; font-weight: 900; color: var(--dark); margin: 0; transition: color .25s; }
  .teacher-float-card:hover .tcard-name { color: var(--primary); transform: translateZ(10px); }
  .tcard-bio { font-size: .78rem; color: var(--muted); font-weight: 500; line-height: 1.55; margin: 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .tcard-cta { margin-top: .6rem; font-size: .75rem; font-weight: 800; color: var(--primary); display: inline-flex; align-items: center; gap: .3rem; opacity: 0; transition: opacity .25s, transform .3s; transform: translateY(10px); }
  .teacher-float-card:hover .tcard-cta { opacity: 1; transform: translateY(0) translateZ(15px); }

  .t-page-btn { background: white; border: 1px solid var(--border); color: var(--dark); width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: var(--trans); }
  .t-page-btn:hover:not(:disabled) { border-color: var(--primary); color: var(--primary); }
  .t-page-btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .t-dot { width: 8px; height: 8px; background: var(--border); border-radius: 50%; cursor: pointer; transition: var(--trans); border: none; padding: 0; }
  .t-dot.active { background: var(--primary); transform: scale(1.5); }

  /* ── Skeleton ──────────────────────────────────────────────────────────────── */
  .skeleton-card { background: var(--card-bg); border-radius: var(--radius-xl); border: 1px solid var(--border); overflow: hidden; animation: pulse 1.6s ease-in-out infinite; }
  .skeleton-img { height: 210px; background: linear-gradient(90deg, #edf0f7 25%, #f4f6fb 50%, #edf0f7 75%); background-size: 200% 100%; animation: shimmer 1.7s infinite; }
  .skeleton-body { padding: 1.4rem 1.5rem 1.5rem; display: flex; flex-direction: column; gap: .65rem; }
  .skel-line { height: .8rem; background: #edf0f7; border-radius: 99px; }
  .w-65 { width: 65%; } .w-90 { width: 90%; } .w-50 { width: 50%; }
  .skeleton-footer { display: flex; justify-content: space-between; align-items: center; margin-top: .4rem; }
  .skel-circle { width: 2.6rem; height: 2.6rem; border-radius: .75rem; background: #edf0f7; }
  .skel-btn { width: 2.8rem; height: 2.8rem; border-radius: var(--radius-md); background: #edf0f7; }

  @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .7; } }

  @media (max-width: 640px) {
    .courses-grid { grid-template-columns: 1fr; }
    .teachers-grid { grid-template-columns: repeat(2, 1fr); }
    .teachers-section { padding: 1.5rem 1.25rem; }
    .container { padding: 2rem 1rem 4rem; gap: 3.5rem; }
    
  }
</style>