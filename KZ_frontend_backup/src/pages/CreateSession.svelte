<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, slide, fly, scale } from 'svelte/transition';
  import { cubicOut, backOut } from 'svelte/easing';
  import { 
    BookOpen, Calendar, Clock, Link, Plus, Trash2, 
    ChevronLeft, ChevronRight, ImagePlus, CheckCircle2,
    Loader2, LayoutGrid, Info, Sparkles, ChevronDown, Check,
    Users, Infinity, UserPlus 
  } from 'lucide-svelte';
  import api from '../lib/api';
  import { navigate } from '../lib/router';
  import { notify } from '../lib/notifications';
  import type { Category } from '../lib/types';
  import type { AxiosError } from 'axios';

  // ---- Local types --------------------------------------------------------
  interface CourseMeta {
    title: string;
    description: string;
    category_id: number | null;
    cover_image_url: string;
    student_limit: number | null;
    limit_mode: 'unlimited' | 'capped';
  }

  interface SessionDayInput {
    title: string;
    date_time: string;
    session_duration: number;
    duration_mode: 'preset' | 'custom';
    isDropdownOpen: boolean;
    meeting_link: string;
  }

  // ---- State --------------------------------------------------------------
  let currentStep = $state<1 | 2>(1);
  let isLoading = $state(false);
  let isUploadingCover = $state(false);
  let dbCategories = $state<Category[]>([]);

  // حالة القائمة المنسدلة للقسم
  let isCatDropdownOpen = $state(false);

  let course = $state<CourseMeta>({
    title: '',
    description: '',
    category_id: null,
    cover_image_url: '',
    student_limit: null,
    limit_mode: 'unlimited',
  });

  let sessionsList = $state<SessionDayInput[]>([
    { 
      title: 'المحاضرة الأولى', 
      date_time: '', 
      session_duration: 60, 
      duration_mode: 'preset',
      isDropdownOpen: false,
      meeting_link: '' 
    },
  ]);

  const minDateTime = new Date().toISOString().slice(0, 16);

  let selectedCatName = $derived(
    dbCategories.find(c => c.id === course.category_id)?.category_name ?? 'اختر التصنيف العلمي'
  );

  // ---- Load Categories ----------------------------------------------------
  onMount(async () => {
    try {
      const res = await api.get<Category[]>('/sessions/categories');
      dbCategories = res.data ?? [];
      if (dbCategories.length > 0) course.category_id = dbCategories[0].id;
    } catch {
      notify.error('تعذّر تحميل قائمة الأقسام العلمية');
    }
  });

  // ---- Cover upload -------------------------------------------------------
  async function handleCoverUpload(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      notify.error('استخدم صور JPG أو PNG أو WEBP فقط');
      return;
    }
    
    isUploadingCover = true;
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await api.post<{ cover_url: string }>(
        '/sessions/upload-cover',
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } },
      );
      course.cover_image_url = res.data.cover_url;
      notify.success('تم رفع غلاف الدورة');
    } catch {
      notify.error('فشل الرفع، جرب مرة ثانية');
    } finally {
      isUploadingCover = false;
      input.value = '';
    }
  }

  // ---- Step 2 Logic -------------------------------------------------------
  function addSessionDay(): void {
    sessionsList = [
      ...sessionsList,
      {
        title: `المحاضرة رقم ${sessionsList.length + 1}`,
        date_time: '',
        session_duration: 60,
        duration_mode: 'preset',
        isDropdownOpen: false,
        meeting_link: '',
      },
    ];
  }

  function removeSessionDay(index: number): void {
    if (sessionsList.length > 1) {
      sessionsList = sessionsList.filter((_, i) => i !== index);
    }
  }

  function goToStep2(): void {
    if (!course.title.trim() || !course.description.trim()) {
      notify.warning('أكمل معلومات الدورة أولاً');
      return;
    }
    currentStep = 2;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // ---- Submit -------------------------------------------------------------
  async function handleFinalSubmit(): Promise<void> {
    if (isLoading) return;
    
    if (sessionsList.some((s) => !s.date_time || !s.title.trim() || !s.meeting_link.trim())) {
      notify.error('يرجى تعبئة جميع الحقول الإجبارية لكل المحاضرات (التاريخ، العنوان، رابط الاجتماع)');
      return;
    }

    isLoading = true;
    try {
      const results = await Promise.allSettled(
        sessionsList.map((s) =>
          api.post('/sessions/', {
            title: `${course.title} - ${s.title}`,
            description: course.description,
            session_duration: s.session_duration,
            date_time: s.date_time,
            meeting_link: s.meeting_link,
            cover_image_url: course.cover_image_url || null,
            category_ids: [course.category_id],
            student_limit: course.student_limit,
          }),
        ),
      );

      if (results.every(r => r.status === 'fulfilled')) {
        notify.success('تم النشر');
        setTimeout(() => navigate('my_lectures'), 1000);
      } else {
        notify.warning('تم نشر بعض المحاضرات, يرجى مراجعة القائمة');
      }
    } catch {
      notify.error('حدث خطأ غير متوقع أثناء النشر');
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="create-page" dir="rtl">
  
  <header class="page-header" in:fly={{ y: -20, duration: 600 }}>
    <div class="header-icon">
      <Sparkles size={32} class="text-amber-400" />
    </div>
    <div class="header-text">
      <h1>انشاء محاضرة جديدة</h1>
      <p>حوّل خبرتك إلى علم ينتفع به الآخرون</p>
    </div>
    <button class="btn-back-ghost" onclick={() => navigate('my_lectures')}>
      العودة للمحاضرات <ChevronLeft size={18} />
    </button>
  </header>

  <main class="wizard-card" in:fly={{ y: 30, duration: 800, easing: backOut }}>
    
    <div class="stepper">
      <div class="step-item {currentStep >= 1 ? 'active' : ''}">
        <div class="step-num">{currentStep > 1 ? '✓' : '1'}</div>
        <span>معلومات الدورة</span>
      </div>
      <div class="step-line">
        <div class="line-fill" style="width: {currentStep === 2 ? '100%' : '0%'}"></div>
      </div>
      <div class="step-item {currentStep === 2 ? 'active' : ''}">
        <div class="step-num">2</div>
        <span>جدولة المحاضرات</span>
      </div>
    </div>

    {#if currentStep === 1}
      <section class="step-content" in:fade={{ duration: 300 }}>
        
        <div class="form-layout">
          <div class="upload-zone {course.cover_image_url ? 'has-image' : ''}">
            {#if isUploadingCover}
              <div class="upload-loader" in:fade>
                <Loader2 class="spin" size={40} />
                <p>جاري معالجة الصورة...</p>
              </div>
            {:else if course.cover_image_url}
              <img 
                src={`http://127.0.0.1:8000/pics/${course.cover_image_url}`} 
                alt="preview" 
                class="cover-preview"
                in:scale={{ start: 0.9, duration: 400 }}
              />
              <label class="change-cover">
                <ImagePlus size={20} /> تغيير الغلاف
                <input type="file" class="hidden" onchange={handleCoverUpload} accept="image/*" />
              </label>
            {:else}
              <label class="upload-placeholder">
                <div class="icon-box">
                  <ImagePlus size={48} strokeWidth={1.5} />
                </div>
                <h3>ارفع غلاف الدورة</h3>
                <p>يفضل أبعاد 16:9 للحصول على أفضل مظهر</p>
                <input type="file" class="hidden" onchange={handleCoverUpload} accept="image/*" />
              </label>
            {/if}
          </div>

          <div class="fields-grid">
            <div class="input-group">
              <label for="title">العنوان</label>
              <div class="input-wrapper">
                <BookOpen class="input-icon" size={18} />
                <input id="title" bind:value={course.title} placeholder="مثلاً: أسس الخوارزميات المتقدمة" />
              </div>
            </div>

            <div class="input-group relative" style="z-index: 50;">
              <label>التصنيف</label>
              <div class="relative w-full">
                <LayoutGrid class="input-icon" size={18} />
                <button
                  type="button"
                  class="custom-select-trigger {isCatDropdownOpen ? 'active' : ''}"
                  onclick={() => isCatDropdownOpen = !isCatDropdownOpen}
                >
                  <span class="select-text">{selectedCatName}</span>
                  <div class="icon-chevron {isCatDropdownOpen ? 'rotate-180' : ''}">
                    <ChevronDown size={18} />
                  </div>
                </button>

                {#if isCatDropdownOpen}
                  <div class="fixed-backdrop" onclick={() => isCatDropdownOpen = false} role="presentation"></div>
                  <ul class="custom-select-menu" transition:slide={{ duration: 250, easing: cubicOut }}>
                    {#if dbCategories.length === 0}
                      <li class="p-3 text-center text-sm text-slate-400 font-bold">لا توجد أقسام متاحة</li>
                    {:else}
                      {#each dbCategories as cat (cat.id)}
                        <li>
                          <button
                            type="button"
                            class="custom-select-item {course.category_id === cat.id ? 'selected' : ''}"
                            onclick={() => { course.category_id = cat.id; isCatDropdownOpen = false; }}
                          >
                            <span class="truncate">{cat.category_name}</span>
                            {#if course.category_id === cat.id}<Check size={16} strokeWidth={3} class="check-icon" />{/if}
                          </button>
                        </li>
                      {/each}
                    {/if} 
                  </ul>
                {/if}
              </div>
            </div>

            <div class="input-group full-width">
              <label>السعة الاستيعابية (عدد الطلاب)</label>
              <div class="capacity-toggle-group">
                <button 
                  type="button" 
                  class="toggle-btn {course.limit_mode === 'unlimited' ? 'active' : ''}"
                  onclick={() => { course.limit_mode = 'unlimited'; course.student_limit = null; }}
                >
                  <Infinity size={16} /> غير محدود
                </button>
                <button 
                  type="button" 
                  class="toggle-btn {course.limit_mode === 'capped' ? 'active' : ''}"
                  onclick={() => { course.limit_mode = 'capped'; course.student_limit = 20; }}
                >
                  <Users size={16} /> عدد محدد
                </button>
              </div>

              {#if course.limit_mode === 'capped'}
                <div class="limit-input-wrapper" transition:slide={{ duration: 300 }}>
                  <div class="input-wrapper">
                    <UserPlus class="input-icon" size={18} />
                    <input 
                      type="number" 
                      bind:value={course.student_limit} 
                      min="1" 
                      placeholder="أدخل أقصى عدد للطلاب"
                      class="minimal-input"
                    />
                  </div>
                  <p class="limit-hint">سيتم إغلاق التسجيل تلقائياً عند اكتمال العدد.</p>
                </div>
              {/if}
            </div>

            <div class="input-group full-width">
              <label for="desc">وصف تفصيلي</label>
              <textarea id="desc" bind:value={course.description} placeholder="ما الذي سيتعلمه الطالب في هذه الدورة؟"></textarea>
            </div>
          </div>
        </div>

        <div class="footer-actions">
          <button class="btn-primary-large" onclick={goToStep2}>
            متابعة  <ChevronLeft size={20} />
          </button>
        </div>
      </section>

    {:else}
      <section class="step-content" in:fade={{ duration: 300 }}>
        
        <div class="step-header-flex">
          <div class="text">
            <h2>أيام ومواعيد المحاضرات</h2>
            <p>يمكنك إضافة محاضرة واحدة أو أكثر</p>
          </div>
          <button class="btn-add-day" onclick={addSessionDay}>
            <Plus size={18} /> إضافة محاضرة إضافية
          </button>
        </div>

        <div class="sessions-scroll custom-scrollbar">
          {#each sessionsList as session, i (i)}
            <div class="session-item-card" style="z-index: {50 - i}; position: relative;" transition:slide={{ duration: 300, easing: cubicOut }}>
              <div class="item-header">
                <div class="day-badge">المحاضرة {i + 1}</div>
                {#if sessionsList.length > 1}
                  <button class="btn-remove" onclick={() => removeSessionDay(i)} title="حذف">
                    <Trash2 size={16} />
                  </button>
                {/if}
              </div>

              <div class="item-grid">
                <div class="input-group col-span-2">
                  <input bind:value={session.title} placeholder="عنوان المحاضرة (مثلاً: المقدمة والبيئة البرمجية)" class="minimal-input" />
                </div>
                
                <div class="input-group">
                  <label>التاريخ والوقت</label>
                  <input type="datetime-local" bind:value={session.date_time} min={minDateTime} class="minimal-input" />
                </div>

                <div class="input-group relative" style="z-index: {40 - i};">
                  <label>مدة المحاضرة</label>
                  <div class="relative w-full">
                    <Clock class="input-icon" size={18} />
                    <button
                      type="button"
                      class="custom-select-trigger {session.isDropdownOpen ? 'active' : ''}"
                      onclick={() => session.isDropdownOpen = !session.isDropdownOpen}
                    >
                      <span class="select-text">
                        {#if session.duration_mode === 'custom'}
                          أكثر (إدخال مخصص)
                        {:else if session.session_duration === 60}
                          ساعة واحدة (60 دقيقة)
                        {:else if session.session_duration === 120}
                          ساعتان (120 دقيقة)
                        {:else if session.session_duration === 180}
                          ثلاث ساعات (180 دقيقة)
                        {:else}
                          ساعة واحدة (60 دقيقة)
                        {/if}
                      </span>
                      <div class="icon-chevron {session.isDropdownOpen ? 'rotate-180' : ''}">
                        <ChevronDown size={18} />
                      </div>
                    </button>

                    {#if session.isDropdownOpen}
                      <div class="fixed-backdrop" onclick={() => session.isDropdownOpen = false} role="presentation"></div>
                      <ul class="custom-select-menu" transition:slide={{ duration: 250, easing: cubicOut }}>
                        <li>
                          <button type="button" class="custom-select-item" onclick={() => { session.session_duration = 60; session.duration_mode = 'preset'; session.isDropdownOpen = false; }}>
                            <span>ساعة واحدة (60 دقيقة)</span>
                            {#if session.duration_mode === 'preset' && session.session_duration === 60}<Check size={16} class="check-icon" />{/if}
                          </button>
                        </li>
                        <li>
                          <button type="button" class="custom-select-item" onclick={() => { session.session_duration = 120; session.duration_mode = 'preset'; session.isDropdownOpen = false; }}>
                            <span>ساعتان (120 دقيقة)</span>
                            {#if session.duration_mode === 'preset' && session.session_duration === 120}<Check size={16} class="check-icon" />{/if}
                          </button>
                        </li>
                        <li>
                          <button type="button" class="custom-select-item" onclick={() => { session.session_duration = 180; session.duration_mode = 'preset'; session.isDropdownOpen = false; }}>
                            <span>ثلاث ساعات (180 دقيقة)</span>
                            {#if session.duration_mode === 'preset' && session.session_duration === 180}<Check size={16} class="check-icon" />{/if}
                          </button>
                        </li>
                        <li>
                          <button type="button" class="custom-select-item" onclick={() => { session.duration_mode = 'custom'; session.isDropdownOpen = false; }}>
                            <span>أكثر (إدخال مخصص)</span>
                            {#if session.duration_mode === 'custom'}<Check size={16} class="check-icon" />{/if}
                          </button>
                        </li>
                      </ul>
                    {/if}
                  </div>
                </div>

                {#if session.duration_mode === 'custom'}
                  <div class="input-group col-span-2" transition:slide={{ duration: 300, easing: cubicOut }}>
                    <label>أدخل المدة بالدقائق</label>
                    <div class="flex gap-4 items-center">
                      <input type="number" bind:value={session.session_duration} min="15" class="minimal-input w-32 shrink-0 text-center" />
                      <div class="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 flex items-center gap-3 shadow-inner">
                        <Info size={18} class="text-[#6b8cce]" />
                        <span class="text-sm font-bold text-slate-500">الوقت التقريبي:</span>
                        <span class="text-sm font-black text-slate-700">
                          {Math.floor((session.session_duration || 0) / 60)} ساعة و {(session.session_duration || 0) % 60} دقيقة
                        </span>
                      </div>
                    </div>
                  </div>
                {/if}

                <div class="input-group col-span-2">
                  <label>رابط الاجتماع (إجباري)</label>
                  <div class="input-wrapper">
                    <Link class="input-icon" size={16} />
                    <input bind:value={session.meeting_link} dir="ltr" placeholder="https://zoom.us/j/..." class="minimal-input" />
                  </div>
                </div>
              </div>
            </div>
          {/each}
        </div>

        <div class="footer-actions spread">
          <button class="btn-secondary" onclick={() => currentStep = 1}>
            <ChevronRight size={18} /> السابق
          </button>
          <button class="btn-publish" onclick={handleFinalSubmit} disabled={isLoading}>
            {#if isLoading}
              <Loader2 class="spin" size={20} /> جاري النشر...
            {:else}
              <CheckCircle2 size={20} />نشر
            {/if}
          </button>
        </div>
      </section>
    {/if}
  </main>
</div>

<style>
  :root {
    --primary: #6b8cce;
    --dark: #2a3c54;
    --bg-soft: #f8fafc;
    --card-shadow: 0 20px 50px rgba(42, 60, 84, 0.1);
    --trans: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .create-page { max-width: 900px; margin: 0 auto; padding: 2rem 1.5rem 5rem; font-family: 'Tajawal', 'Cairo', sans-serif; }

  /* ── Header ── */
  .page-header { display: flex; align-items: center; gap: 1.5rem; margin-bottom: 3rem; }
  .header-icon { width: 64px; height: 64px; background: white; border-radius: 1.5rem; display: flex; align-items: center; justify-content: center; box-shadow: var(--card-shadow); border: 1px solid #eef2f6; }
  .header-text h1 { font-size: 2rem; font-weight: 900; color: var(--dark); margin: 0; }
  .header-text p { color: #94a3b8; font-weight: 500; margin-top: 0.2rem; }
  .btn-back-ghost { margin-right: auto; background: none; border: none; color: #94a3b8; font-weight: 700; display: flex; align-items: center; gap: 0.5rem; cursor: pointer; transition: var(--trans); font-family: inherit; }
  .btn-back-ghost:hover { color: var(--primary); }

  /* ── Wizard Card ── */
  .wizard-card { background: white; border-radius: 3rem; padding: 3rem; box-shadow: var(--card-shadow); border: 1px solid #f1f5f9; }

  /* ── Stepper ── */
  .stepper { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4rem; padding: 0 2rem; }
  .step-item { display: flex; flex-direction: column; align-items: center; gap: 0.8rem; position: relative; z-index: 2; }
  .step-num { width: 44px; height: 44px; border-radius: 50%; background: #f1f5f9; color: #94a3b8; display: flex; align-items: center; justify-content: center; font-weight: 900; transition: var(--trans); border: 4px solid white; outline: 1px solid #e2e8f0; }
  .step-item.active .step-num { background: var(--primary); color: white; outline-color: var(--primary); transform: scale(1.1); box-shadow: 0 0 20px rgba(107, 140, 206, 0.4); }
  .step-item span { font-size: 0.9rem; font-weight: 800; color: #94a3b8; transition: var(--trans); }
  .step-item.active span { color: var(--dark); }
  .step-line { flex: 1; height: 4px; background: #f1f5f9; margin: 0 1rem; margin-top: -1.8rem; border-radius: 2px; overflow: hidden; }
  .line-fill { height: 100%; background: var(--primary); transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1); }

  /* ── Capacity Toggle Styles ── */
  .capacity-toggle-group { display: flex; gap: 1rem; background: var(--bg-soft); padding: 0.5rem; border-radius: 1.2rem; border: 1.5px solid #eef2f6; }
  .toggle-btn { flex: 1; padding: 0.8rem; border-radius: 0.8rem; border: none; background: transparent; color: #94a3b8; font-weight: 800; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 0.5rem; transition: var(--trans); font-family: inherit; }
  .toggle-btn.active { background: white; color: var(--primary); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
  .limit-input-wrapper { margin-top: 1rem; padding: 1rem; background: #f0f7ff; border-radius: 1.5rem; border: 1px dashed var(--primary); }
  .limit-hint { font-size: 0.8rem; color: var(--primary); font-weight: 700; margin-top: 0.5rem; padding-right: 0.5rem; }

  /* ── Upload Zone ── */
  .upload-zone { width: 100%; height: 260px; background: var(--bg-soft); border: 2px dashed #cbd5e1; border-radius: 2.5rem; margin-bottom: 2.5rem; position: relative; overflow: hidden; transition: var(--trans); }
  .upload-zone:hover { border-color: var(--primary); background: #f0f7ff; }
  .upload-placeholder { width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; cursor: pointer; }
  .icon-box { width: 80px; height: 80px; background: white; border-radius: 2rem; display: flex; align-items: center; justify-content: center; color: var(--primary); margin-bottom: 1rem; box-shadow: 0 10px 20px rgba(0,0,0,0.05); }
  .upload-placeholder h3 { font-size: 1.2rem; font-weight: 900; color: var(--dark); margin: 0; }
  .upload-placeholder p { color: #94a3b8; font-size: 0.85rem; margin-top: 0.4rem; }
  .cover-preview { width: 100%; height: 100%; object-fit: cover; }
  .change-cover { position: absolute; bottom: 1.5rem; left: 1.5rem; background: rgba(0,0,0,0.6); backdrop-filter: blur(5px); color: white; padding: 0.6rem 1.2rem; border-radius: 1rem; font-size: 0.8rem; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 0.5rem; transition: var(--trans); }
  .change-cover:hover { background: var(--primary); }

  /* ── Form Fields ── */
  .fields-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
  .full-width { grid-column: 1 / -1; }
  .input-group { display: flex; flex-direction: column; gap: 0.6rem; }
  .input-group label { font-size: 0.9rem; font-weight: 800; color: var(--dark); padding-right: 0.5rem; }
  .input-wrapper { position: relative; display: flex; align-items: center; width: 100%; }
  .input-icon { position: absolute; right: 1.2rem; color: #94a3b8; pointer-events: none; z-index: 2; }
  
  input, textarea { width: 100%; padding: 1rem 1.2rem; padding-right: 3rem; background: var(--bg-soft); border: 1.5px solid #eef2f6; border-radius: 1.2rem; font-size: 0.95rem; font-weight: 700; color: var(--dark); outline: none; transition: var(--trans); font-family: inherit; }
  textarea { padding-right: 1.2rem; height: 140px; resize: none; }
  input:focus, textarea:focus { border-color: var(--primary); background: white; box-shadow: 0 0 0 4px rgba(107, 140, 206, 0.1); }

  /* ── Custom Select (Dropdown) ── */
  .custom-select-trigger { width: 100%; padding: 1rem 1.2rem 1rem 3rem; background: var(--bg-soft); border: 1.5px solid #eef2f6; border-radius: 1.2rem; font-size: 0.95rem; font-weight: 700; color: var(--dark); cursor: pointer; display: flex; align-items: center; justify-content: space-between; transition: var(--trans); text-align: right; font-family: inherit; }
  .custom-select-trigger .select-text { padding-right: 2rem; }
  .custom-select-trigger:hover { border-color: #cbd5e1; }
  .custom-select-trigger.active { border-color: var(--primary); background: white; box-shadow: 0 0 0 4px rgba(107, 140, 206, 0.1); }
  
  .icon-chevron { position: absolute; left: 1.2rem; color: #94a3b8; transition: transform 0.3s ease; }
  .rotate-180 { transform: rotate(180deg); color: var(--primary); }

  .fixed-backdrop { position: fixed; inset: 0; z-index: 10; cursor: default; }

  .custom-select-menu { position: absolute; top: calc(100% + 0.5rem); left: 0; right: 0; background: white; border-radius: 1.2rem; border: 1px solid #eef2f6; box-shadow: 0 15px 40px rgba(42, 60, 84, 0.12); z-index: 50; max-height: 240px; overflow-y: auto; padding: 0.5rem; list-style: none; margin: 0; }
  .custom-select-menu::-webkit-scrollbar { width: 4px; }
  .custom-select-menu::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
  
  .custom-select-item { width: 100%; text-align: right; padding: 0.8rem 1rem; border-radius: 0.8rem; font-size: 0.9rem; font-weight: 700; color: var(--dark); cursor: pointer; background: transparent; border: none; transition: var(--trans); display: flex; align-items: center; justify-content: space-between; font-family: inherit; }
  .custom-select-item:hover { background: #f0f4f8; color: var(--primary); transform: translateX(-4px); }
  .custom-select-item.selected { background: rgba(107, 140, 206, 0.08); color: var(--primary); }
  .check-icon { flex-shrink: 0; }

  /* ── Step 2 Specifics ── */
  .step-header-flex { display: flex; align-items: center; justify-content: space-between; margin-bottom: 2rem; }
  .step-header-flex h2 { font-size: 1.5rem; font-weight: 900; color: var(--dark); margin: 0; }
  .step-header-flex p { color: #94a3b8; font-size: 0.9rem; margin-top: 0.2rem; }
  .btn-add-day { background: #f1f5f9; color: var(--dark); border: none; padding: 0.7rem 1.2rem; border-radius: 1rem; font-weight: 800; display: flex; align-items: center; gap: 0.5rem; cursor: pointer; transition: var(--trans); font-family: inherit; }
  .btn-add-day:hover { background: var(--dark); color: white; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(42,60,84,0.1); }

  .sessions-scroll { padding: 0.5rem; padding-left: 1rem; margin-bottom: 2rem; }
  .session-item-card { background: white; border: 1.5px solid #eef2f6; border-radius: 2rem; padding: 2rem; margin-bottom: 1.5rem; position: relative; box-shadow: 0 4px 15px rgba(0,0,0,0.02); }
  .item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
  .day-badge { background: rgba(107,140,206,0.1); color: var(--primary); padding: 0.4rem 1rem; border-radius: 0.8rem; font-size: 0.8rem; font-weight: 900; }
  .btn-remove { background: #fff1f2; color: #f43f5e; border: none; width: 32px; height: 32px; border-radius: 0.7rem; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: var(--trans); }
  .btn-remove:hover { background: #f43f5e; color: white; transform: rotate(90deg); }
  .item-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
  .col-span-2 { grid-column: span 2; }
  .minimal-input { background: var(--bg-soft); padding-right: 1.2rem; border-color: #eef2f6; }

  /* ── Actions ── */
  .footer-actions { display: flex; gap: 1rem; margin-top: 3rem; }
  .spread { justify-content: space-between; }
  .btn-primary-large { flex: 1; padding: 1.2rem; background: var(--dark); color: white; border: none; border-radius: 1.5rem; font-size: 1.1rem; font-weight: 900; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 0.8rem; transition: var(--trans); box-shadow: 0 10px 20px rgba(42, 60, 84, 0.2); font-family: inherit; }
  .btn-primary-large:hover { background: var(--primary); transform: translateY(-3px); box-shadow: 0 15px 30px rgba(107, 140, 206, 0.25); }
  .btn-secondary { padding: 1.2rem 2.5rem; background: #f1f5f9; color: #64748b; border: none; border-radius: 1.5rem; font-weight: 800; cursor: pointer; transition: var(--trans); display: flex; align-items: center; gap: 0.5rem; font-family: inherit; }
  .btn-secondary:hover { background: #e2e8f0; color: var(--dark); }
  .btn-publish { padding: 1.2rem 3rem; background: #10b981; color: white; border: none; border-radius: 1.5rem; font-size: 1.1rem; font-weight: 900; cursor: pointer; display: flex; align-items: center; gap: 0.8rem; transition: var(--trans); box-shadow: 0 10px 20px rgba(16, 185, 129, 0.2); font-family: inherit; }
  .btn-publish:hover:not(:disabled) { background: #059669; transform: translateY(-3px); box-shadow: 0 15px 30px rgba(16, 185, 129, 0.3); }

  .spin { animation: spin 1s linear infinite; }
  @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

  /* ── Scrollbar ── */
  .custom-scrollbar::-webkit-scrollbar { width: 6px; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
  .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }

  @media (max-width: 768px) {
    .wizard-card { padding: 1.5rem; border-radius: 2rem; }
    .fields-grid, .item-grid { grid-template-columns: 1fr; }
    .col-span-2 { grid-column: span 1; }
    .stepper { padding: 0; }
    .stepper span { display: none; }
  }
</style>