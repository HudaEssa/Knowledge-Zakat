<script lang="ts">
  import { fade, fly, slide, scale } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import { 
    UserCircle, Edit3, X, Save, KeyRound, 
    ImagePlus, Loader2, Mail, Info, ShieldAlert,
    Eye, EyeOff
  } from 'lucide-svelte';
  import api from '../lib/api';
  import { user } from '../lib/stores';
  import { notify } from '../lib/notifications';
  import type { User } from '../lib/types';
  import type { AxiosError } from 'axios';

  // ---- Form state ---------------------------------------------------------
  let isEditing = $state(false);
  let isSaving = $state(false);
  let isUploadingImage = $state(false);
  let showPasswordSection = $state(false); 

  let showOld = $state(false);
  let showNew = $state(false);
  let serverOldPwdError = $state(false);

  let formData = $state({
    firstname: $user?.firstname ?? '',
    lastname: $user?.lastname ?? '',
    bio: $user?.bio ?? '',
    old_password: '',
    new_password: '',
    confirm_password: '',
  });

  $effect(() => {
    if (!isEditing && $user) {
      formData.firstname = $user.firstname;
      formData.lastname = $user.lastname;
      formData.bio = $user.bio ?? '';
    }
  });

  // ---- Validators ---------------------------------------------------------
  type Validity = 'idle' | 'success' | 'error';

  function validateNewPwd(pwd: string): Validity {
    if (pwd === '') return 'idle';
    const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
    return regex.test(pwd) ? 'success' : 'error';
  }

  let oldPwdClass = $derived(serverOldPwdError ? 'input-error' : '');

  let newPwdClass = $derived.by(() => {
    const v = validateNewPwd(formData.new_password);
    if (v === 'idle') return '';
    if (v === 'success') return 'input-success';
    return 'input-error';
  });

  let confirmClass = $derived.by(() => {
    if (formData.confirm_password === '') return '';
    return formData.confirm_password === formData.new_password
      ? 'input-success'
      : 'input-error';
  });

  // ---- Image upload -------------------------------------------------------
  async function handleImage(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      notify.error('نوع الصورة غير مدعوم، استخدم JPG أو PNG أو WEBP');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      notify.error('حجم الصورة كبير جداً، الحد الأقصى 5 ميجابايت');
      return;
    }

    isUploadingImage = true;
    try {
      const formDataObj = new FormData();
      formDataObj.append('file', file);

      const res = await api.post<User>('/me/upload-image', formDataObj, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      user.set(res.data);
      notify.success('تم تحديث صورة الملف الشخصي');
    } catch {
      notify.error('تعذّر رفع الصورة، يرجى المحاولة لاحقاً');
    } finally {
      isUploadingImage = false;
      input.value = '';
    }
  }

  // ---- Cancel edit --------------------------------------------------------
  function toggleEditing(): void {
    isEditing = !isEditing;
    showPasswordSection = false; 
    formData.old_password = '';
    formData.new_password = '';
    formData.confirm_password = '';
    serverOldPwdError = false;
  }

  // ---- Save ---------------------------------------------------------------
  async function saveAll(): Promise<void> {
    if (isSaving) return;
    serverOldPwdError = false;

    if (showPasswordSection) {
      if (validateNewPwd(formData.new_password) === 'error') {
        notify.error('كلمة المرور يجب أن تكون 8 أحرف وتشمل حرفاً كبيراً وصغيراً ورقماً');
        return;
      }
      if (formData.new_password !== formData.confirm_password) {
        notify.error('كلمتا المرور الجديدتان غير متطابقتين');
        return;
      }
      if (!formData.old_password) {
        notify.error('يرجى إدخال كلمة المرور الحالية لتغييرها');
        return;
      }
    }

    if (!$user) return;
    isSaving = true;

    try {
      const payload: Record<string, unknown> = {
        firstname: formData.firstname,
        lastname: formData.lastname,
        bio: formData.bio,
      };
      
      if (showPasswordSection && formData.new_password !== '') {
        payload.old_password = formData.old_password;
        payload.new_password = formData.new_password;
      }

      const res = await api.put<User>(`/users/${$user.id}`, payload);
      user.set(res.data);
      isEditing = false;
      showPasswordSection = false;
      formData.old_password = '';
      formData.new_password = '';
      formData.confirm_password = '';
      notify.success('تم حفظ التعديلات بنجاح');
    } catch (err) {
      const ax = err as AxiosError<{ detail?: string }>;
      const detail = ax.response?.data?.detail;

      if (ax.response?.status === 403 || ax.response?.status === 400) {
        serverOldPwdError = true;
      }

      notify.error(typeof detail === 'string' ? detail : 'تعذّر حفظ التعديلات، يرجى المحاولة لاحقاً');
    } finally {
      isSaving = false;
    }
  }
</script>

<div class="sv-page" dir="rtl">
  
  <div class="profile-container">
    
    <header class="header-card" in:fly={{ y: 30, duration: 450, easing: cubicOut }}>
      <div class="header-cover">
        <div class="cover-overlay-pattern"></div>
      </div>

      <div class="header-content">
        <div class="avatar-section">
          <div class="avatar-wrapper">
            {#if $user?.profile_image}
              <img src={$user.profile_image} alt="Profile" class="avatar-img" />
            {:else}
              <div class="avatar-placeholder">
                {$user?.firstname?.charAt(0).toUpperCase() ?? '?'}
              </div>
            {/if}

            {#if isEditing}
              <label class="avatar-upload-overlay" in:fade={{ duration: 150 }}>
                {#if isUploadingImage}
                  <Loader2 class="spin" size={32} color="white" />
                {:else}
                  <ImagePlus size={32} color="white" strokeWidth={2} />
                  <span class="upload-text">تغيير الصورة</span>
                {/if}
                <input
                  type="file"
                  class="hidden"
                  onchange={handleImage}
                  accept="image/jpeg,image/png,image/webp"
                  disabled={isUploadingImage}
                />
              </label>
            {/if}
          </div>
        </div>

        <div class="user-details">
          <h1 class="user-name">{$user?.firstname ?? ''} {$user?.lastname ?? ''}</h1>
          {#if $user?.email}
            <p class="user-email" dir="ltr"><Mail size={14} /> {$user.email}</p>
          {/if}
        </div>

        {#if !isEditing}
          <div class="action-section" in:fade>
            <button class="btn-primary" onclick={toggleEditing}>
              <Edit3 size={16} strokeWidth={2.5} /> تعديل البيانات
            </button>
          </div>
        {/if}
      </div>
    </header>

    <div class="body-card" in:fly={{ y: 40, delay: 100, duration: 450, easing: cubicOut }}>
      
      {#if isEditing}
        <div class="edit-form" in:fade={{ duration: 300 }}>
          <div class="section-title-group mb-6">
            <div class="section-accent"></div>
            <h2 class="section-title">المعلومات الشخصية</h2>
          </div>

          <div class="form-grid">
            <div class="input-group">
              <label for="firstname">الاسم الأول</label>
              <input id="firstname" bind:value={formData.firstname} disabled={isSaving} class="sv-input" />
            </div>

            <div class="input-group">
              <label for="lastname">الاسم الأخير</label>
              <input id="lastname" bind:value={formData.lastname} disabled={isSaving} class="sv-input" />
            </div>

            <div class="input-group full-width">
              <label for="bio">نبذة عن طموحاتك العلمية</label>
              <textarea id="bio" bind:value={formData.bio} disabled={isSaving} class="sv-textarea" placeholder="تحدث عن نفسك وما تطمح لتعلمه..."></textarea>
            </div>
          </div>

          <div class="password-section mt-8 pt-6 border-t">
            <div class="flex justify-between items-center mb-4">
              <div class="section-title-group">
                <div class="section-accent bg-amber-500"></div>
                <h2 class="section-title text-lg">الأمان وحماية الحساب</h2>
              </div>
              <button 
                type="button" 
                class="btn-toggle-pwd" 
                onclick={() => showPasswordSection = !showPasswordSection}
              >
                <KeyRound size={16} /> 
                {showPasswordSection ? 'إلغاء تغيير كلمة المرور' : 'تغيير كلمة المرور'}
              </button>
            </div>

            {#if showPasswordSection}
              <div class="form-grid password-grid bg-slate-50 p-6 rounded-2xl border border-slate-100" in:slide={{ duration: 300, easing: cubicOut }}>
                <div class="input-group full-width relative">
                  <label for="prof-oldpw">كلمة المرور الحالية</label>
                  <input
                    id="prof-oldpw"
                    type={showOld ? 'text' : 'password'}
                    bind:value={formData.old_password}
                    disabled={isSaving}
                    class="sv-input {oldPwdClass} pr-12"
                    placeholder="أدخل كلمة المرور الحالية لتأكيد التغيير"
                  />
                  <button type="button" class="pwd-eye" onclick={() => (showOld = !showOld)} tabindex="-1">
                    {#if showOld}<EyeOff size={18} />{:else}<Eye size={18} />{/if}
                  </button>
                  {#if serverOldPwdError}
                    <span class="error-msg" in:fade><ShieldAlert size={12} /> كلمة المرور الحالية غير صحيحة</span>
                  {/if}
                </div>

                <div class="input-group relative">
                  <label for="prof-newpw">كلمة المرور الجديدة</label>
                  <input
                    id="prof-newpw"
                    type={showNew ? 'text' : 'password'}
                    bind:value={formData.new_password}
                    disabled={isSaving}
                    class="sv-input {newPwdClass} pr-12"
                    placeholder="8 أحرف، حرف كبير، صغير، رقم"
                  />
                  <button type="button" class="pwd-eye" onclick={() => (showNew = !showNew)} tabindex="-1">
                    {#if showNew}<EyeOff size={18} />{:else}<Eye size={18} />{/if}
                  </button>
                </div>

                <div class="input-group relative">
                  <label for="prof-confirm">تأكيد كلمة المرور الجديدة</label>
                  <input
                    id="prof-confirm"
                    type="password"
                    bind:value={formData.confirm_password}
                    disabled={isSaving}
                    class="sv-input {confirmClass}"
                    placeholder="أعد كتابة كلمة المرور الجديدة"
                  />
                </div>
              </div>
            {/if}
          </div>

          <div class="action-footer mt-8 pt-6 border-t flex gap-4">
            <button type="button" class="btn-save flex-1" onclick={saveAll} disabled={isSaving}>
              {#if isSaving}
                <Loader2 class="spin" size={20} /> جاري الحفظ...
              {:else}
                <Save size={18} /> حفظ التعديلات
              {/if}
            </button>
            <button type="button" class="btn-cancel" onclick={toggleEditing} disabled={isSaving}>
              إلغاء
            </button>
          </div>
        </div>

      {:else}
        <div class="read-mode" in:fade={{ duration: 300 }}>
          <div class="section-title-group mb-6">
            <div class="section-accent"></div>
            <h2 class="section-title">نبذة تعريفية</h2>
          </div>
          <div class="bio-box">
            <p class="bio-text">
              {$user?.bio || 'لا توجد نبذة شخصية بعد، ابدأ بكتابة طموحاتك العلمية لتشاركها مع المعلمين والزملاء.'}
            </p>
          </div>
        </div>
      {/if}

    </div>
  </div>
</div>

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
    --radius-xl: 2.5rem;
    --radius-lg: 1.5rem;
    --radius-md: .875rem;
    --shadow-sm: 0 2px 10px rgba(42,60,84,.06);
    --shadow-lg: 0 20px 56px rgba(42,60,84,.12);
    --trans:     all .3s cubic-bezier(.4,0,.2,1);
  }

  /* ── Layout ── */
  .sv-page { direction: rtl; min-height: 100vh; padding: 2rem 1.25rem 5rem; font-family: 'Tajawal', 'Cairo', sans-serif; }
  .profile-container { max-width: 860px; margin: 0 auto; display: flex; flex-direction: column; gap: 1.5rem; }

  /* ── Header Card ── */
  .header-card { background: var(--card-bg); border-radius: var(--radius-xl); border: 1px solid var(--border); overflow: hidden; box-shadow: var(--shadow-lg); position: relative; }
  .header-cover { height: 180px; background: linear-gradient(135deg, var(--dark) 0%, #1e3048 60%, var(--primary) 100%); position: relative; overflow: hidden; }
  .cover-overlay-pattern { position: absolute; inset: 0; background: radial-gradient(circle at 80% 20%, rgba(255,255,255,0.1) 0%, transparent 50%); }

  /* 👈 تم إزالة margin-top السالب من هنا لضمان بقاء الاسم في المنطقة البيضاء */
  .header-content { display: flex; align-items: flex-end; justify-content: space-between; padding: 0 2.5rem 2rem; gap: 1.5rem; flex-wrap: wrap; }
  
  /* 👈 الرفع السالب تم تطبيقه فقط على الصورة */
  .avatar-section { flex-shrink: 0; position: relative; z-index: 10; margin-top: -5rem; }
  
  /* 👈 تكبير حجم الصورة إلى 160px */
  .avatar-wrapper { width: 160px; height: 160px; border-radius: 2.5rem; background: var(--card-bg); padding: 6px; box-shadow: 0 8px 24px rgba(42,60,84,0.15); position: relative; overflow: hidden; }
  .avatar-img { width: 100%; height: 100%; object-fit: cover; border-radius: 2.1rem; }
  .avatar-placeholder { width: 100%; height: 100%; background: var(--light-bg); border-radius: 2.1rem; display: flex; align-items: center; justify-content: center; font-size: 4rem; font-weight: 900; color: var(--primary); }
  
  .avatar-upload-overlay { position: absolute; inset: 6px; background: rgba(42,60,84,0.7); border-radius: 2.1rem; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.5rem; cursor: pointer; opacity: 0; transition: var(--trans); backdrop-filter: blur(2px); }
  .avatar-wrapper:hover .avatar-upload-overlay { opacity: 1; }
  .upload-text { color: white; font-size: 0.85rem; font-weight: 800; }

  /* 👈 دفع النص قليلاً للأسفل ليناسب حجم الصورة الجديد */
  .user-details { flex: 1; padding-bottom: 0.5rem; padding-top: 1rem; }
  .user-name { font-size: 1.8rem; font-weight: 900; color: var(--dark); margin: 0 0 0.4rem; letter-spacing: -0.02em; }
  .user-email { display: inline-flex; align-items: center; gap: 0.4rem; font-size: 0.9rem; font-weight: 700; color: var(--muted); background: var(--light-bg); padding: 0.3rem 0.8rem; border-radius: 99px; }

  .action-section { padding-bottom: 0.5rem; }
  .btn-primary { display: inline-flex; align-items: center; gap: 0.5rem; background: var(--dark); color: white; padding: 0.8rem 1.5rem; border-radius: var(--radius-md); font-size: 0.9rem; font-weight: 800; border: none; cursor: pointer; transition: var(--trans); box-shadow: var(--shadow-sm); font-family: inherit; }
  .btn-primary:hover { background: var(--primary); transform: translateY(-2px); box-shadow: 0 8px 20px rgba(107,140,206,0.3); }

  /* ── Body Card ── */
  .body-card { background: var(--card-bg); border-radius: var(--radius-xl); border: 1px solid var(--border); padding: 2.5rem; box-shadow: var(--shadow-sm); }
  
  .section-title-group { display: flex; align-items: center; gap: 0.75rem; }
  .section-accent { width: 5px; height: 1.5rem; background: var(--primary); border-radius: 99px; }
  .section-title { font-size: 1.25rem; font-weight: 900; color: var(--dark); margin: 0; }

  /* Read Mode */
  .bio-box { background: var(--light-bg); border: 1px solid var(--border); padding: 2rem; border-radius: var(--radius-lg); position: relative; }
  .bio-box::before { content: '“'; position: absolute; top: 0.5rem; right: 1.5rem; font-size: 4rem; color: rgba(107,140,206,0.15); font-family: serif; line-height: 1; pointer-events: none; }
  .bio-text { font-size: 1rem; font-weight: 600; color: var(--dark); line-height: 1.8; margin: 0; position: relative; z-index: 1; }

  /* Edit Form */
  .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
  .input-group { display: flex; flex-direction: column; gap: 0.5rem; }
  .full-width { grid-column: 1 / -1; }
  .input-group label { font-size: 0.85rem; font-weight: 800; color: var(--dark); padding-right: 0.25rem; }
  
  .sv-input, .sv-textarea { width: 100%; padding: 0.9rem 1.25rem; background: var(--light-bg); border: 1.5px solid var(--border); border-radius: var(--radius-md); font-size: 0.95rem; font-weight: 700; color: var(--dark); outline: none; transition: var(--trans); font-family: inherit; }
  .sv-textarea { min-height: 120px; resize: vertical; }
  .sv-input:focus, .sv-textarea:focus { background: white; border-color: var(--primary); box-shadow: 0 0 0 4px rgba(107, 140, 206, 0.15); }
  .sv-input:disabled, .sv-textarea:disabled { opacity: 0.6; cursor: not-allowed; }

  /* Password Section */
  .border-t { border-top-color: var(--border); }
  .btn-toggle-pwd { display: inline-flex; align-items: center; gap: 0.4rem; background: rgba(107,140,206,0.1); color: var(--primary); border: none; padding: 0.5rem 1rem; border-radius: 99px; font-size: 0.8rem; font-weight: 800; cursor: pointer; transition: var(--trans); font-family: inherit; }
  .btn-toggle-pwd:hover { background: rgba(107,140,206,0.2); }
  .password-grid { grid-template-columns: 1fr 1fr; }
  
  .pwd-eye { position: absolute; left: 1rem; top: 2.3rem; color: var(--muted); background: none; border: none; cursor: pointer; transition: var(--trans); padding: 0.2rem; }
  .pwd-eye:hover { color: var(--primary); }
  
  .input-error { border-color: var(--danger) !important; background: #fef2f2 !important; }
  .input-error:focus { box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.15) !important; }
  .input-success { border-color: var(--success) !important; background: #f0fdf4 !important; }
  .input-success:focus { box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.15) !important; }
  .error-msg { font-size: 0.75rem; font-weight: 800; color: var(--danger); display: flex; align-items: center; gap: 0.3rem; margin-top: 0.3rem; }

  /* Action Buttons */
  .btn-save { background: var(--dark); color: white; padding: 1rem; border-radius: var(--radius-lg); font-size: 1rem; font-weight: 900; border: none; cursor: pointer; transition: var(--trans); display: flex; align-items: center; justify-content: center; gap: 0.5rem; font-family: inherit; box-shadow: 0 4px 15px rgba(42,60,84,0.2); }
  .btn-save:hover:not(:disabled) { background: var(--primary); transform: translateY(-2px); box-shadow: 0 8px 25px rgba(107,140,206,0.3); }
  .btn-cancel { background: var(--light-bg); color: var(--muted); padding: 1rem 2rem; border-radius: var(--radius-lg); font-size: 0.95rem; font-weight: 800; border: 1px solid var(--border); cursor: pointer; transition: var(--trans); font-family: inherit; }
  .btn-cancel:hover:not(:disabled) { background: #e2e8f0; color: var(--dark); }
  
  .spin { animation: spin 1s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Responsive ── */
  @media (max-width: 768px) {
    .header-content { flex-direction: column; align-items: center; text-align: center; padding: 0 1.5rem 1.5rem; }
    .avatar-section { margin-top: -5rem; }
    .user-details { padding-top: 0; }
    .action-section { width: 100%; }
    .btn-primary { width: 100%; justify-content: center; }
    .body-card { padding: 1.5rem; }
    .form-grid, .password-grid { grid-template-columns: 1fr; }
    .action-footer { flex-direction: column; }
    .btn-cancel { width: 100%; }
  }
</style>