<!--
  Knowledge Zakat — Register page (FINAL — backend-aligned).

  Backend contract (verified):
   - POST /users/  : JSON {firstname, lastname, email, password,
                          bio?, birthday_date?}
                     → returns UserResponse (NOT a token)
   - POST /token   : JSON {email, password} for auto-login afterwards
                     → returns { access_token }
   - GET  /users/me: authenticated user data

  Notes about the new backend:
   - No /register endpoint — use POST /users/ instead
   - No phone field on UserCreate — collected but not sent
   - No role field on UserCreate — every new user is created as a
     student; teacher promotion happens via the admin panel later
-->

<script lang="ts">
  import { fade, fly, slide } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import api from '../lib/api';
  import { token, user } from '../lib/stores';
  import { navigate } from '../lib/router';
  import { notify } from '../lib/notifications';
  import type { User } from '../lib/types';
  import type { AxiosError } from 'axios';

  import Button from '../components/ui/Button.svelte';
  import Input from '../components/ui/Input.svelte';
  import {
    GraduationCap,
    User as UserIcon,
    Mail,
    Lock,
    Phone,
    Calendar,
    Sparkles,
    BookOpen,
    Users,
    UserPlus,
    UserCheck,
    ArrowLeft,
    ArrowRight,
    Upload,
    CheckCircle2,
  } from 'lucide-svelte';

  let currentStep = $state<1 | 2>(1);

  type RoleChoice = 'student' | 'teacher';

  let firstname = $state('');
  let lastname = $state('');
  let email = $state('');
  let password = $state('');
  let confirmPassword = $state('');
  let role = $state<RoleChoice>('student');

  let birthday = $state('');
  let phone = $state('');
  let bio = $state('');
  let cvFile = $state<File | null>(null);

  let isSubmitting = $state(false);
  let step1Error = $state('');

  function isPasswordStrong(pwd: string): boolean {
    return /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/.test(pwd);
  }

  type ValidationState = 'idle' | 'success' | 'error';

  let passwordState = $derived<ValidationState>(
    password === '' ? 'idle' : isPasswordStrong(password) ? 'success' : 'error',
  );

  let confirmState = $derived<ValidationState>(
    confirmPassword === ''
      ? 'idle'
      : confirmPassword === password
        ? 'success'
        : 'error',
  );

  function goToStep2(): void {
    step1Error = '';

    if (!firstname.trim() || !lastname.trim()) {
      step1Error = 'يرجى إدخال الاسم الأول والأخير';
      return;
    }
    if (!email.trim() || !email.includes('@')) {
      step1Error = 'يرجى إدخال بريد إلكتروني صحيح';
      return;
    }
    if (!isPasswordStrong(password)) {
      step1Error = 'كلمة المرور يجب أن تحتوي 8 أحرف على الأقل + حرف كبير + حرف صغير + رقم';
      return;
    }
    if (password !== confirmPassword) {
      step1Error = 'كلمتا المرور غير متطابقتين';
      return;
    }

    currentStep = 2;
  }

  function handleCvSelect(e: Event): void {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    if (!['image/jpeg', 'image/png', 'image/webp', 'application/pdf'].includes(file.type)) {
      notify.error('نوع الملف غير مدعوم — استخدم JPG/PNG/PDF');
      input.value = '';
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      notify.error('حجم الملف كبير جداً — الحد الأقصى 5MB');
      input.value = '';
      return;
    }

    cvFile = file;
    notify.success('تم اختيار الملف');
  }

  async function handleRegister(): Promise<void> {
    if (isSubmitting) return;
    isSubmitting = true;

    try {
      // Step A: Create the user account.
      // Backend POST /users/ accepts only:
      //   firstname, lastname, email, password, bio?, birthday_date?
      // It returns a UserResponse, NOT a token.
      await api.post('/users/', {
        firstname: firstname.trim(),
        lastname: lastname.trim(),
        email: email.trim(),
        password,
        bio: bio.trim() || null,
        birthday_date: birthday || null,
      });

      // Step B: Auto-login so the user lands on Home directly.
      // /token expects JSON {email, password} (LoginInput schema).
      const tokenRes = await api.post<{ access_token: string }>('/token', {
        email: email.trim(),
        password: password,
      });
      token.set(tokenRes.data.access_token);

      const meRes = await api.get<User>('/users/me');
      user.set(meRes.data);

      // Step C: Optional teacher application.
      // The /upload-cv/ and /request-teacher/ endpoints may not exist
      // yet on the new backend; we tolerate failure so the student
      // account is always created successfully.
      // Step C: طلب الانضمام كمعلم
// Step C: طلب الانضمام كمعلم
// Step C: طلب الانضمام كمعلم
if (role === 'teacher') {
  try {
    let finalCvLink = null; // عرفناه هنا بالبداية حتى الكل يشوفه

    // أ- رفع الملف إذا موجود
    if (cvFile) {
      const fd = new FormData();
      fd.append('file', cvFile);
      
      const uploadRes = await api.post<{ cv_link: string }>('/users/upload-cv', fd, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      // نخزن الرابط بالمتغير اللي عرفناه بره
      finalCvLink = uploadRes.data.cv_link;
    }

    // ب- إرسال الطلب الرسمي (هنا نستخدم finalCvLink)
    await api.post('/users/request-teacher', {
      phone: phone.trim(),
      cv_link: finalCvLink // هسة البرنامج راح يتعرف عليه بدون مشاكل
    });

    notify.info('تم استلام طلبك وهو قيد المراجعة');
  } catch (err) {
    notify.error('تم إنشاء الحساب لكن فشل إرسال طلب المعلم');
  }
}

      notify.success(`أهلاً بك في زكاة العلم، ${meRes.data.firstname}!`);
      setTimeout(() => navigate('home', null, true), 500);
    } catch (err) {
      const ax = err as AxiosError<{ detail?: string }>;
      const detail = ax.response?.data?.detail;
      notify.error(
        typeof detail === 'string'
          ? detail
          : 'تعذّر إنشاء الحساب — قد يكون البريد مستخدماً مسبقاً',
      );
    } finally {
      isSubmitting = false;
    }
  }
</script>

<div
  class="min-h-screen w-full flex items-stretch overflow-hidden bg-brand-100 relative"
  dir="rtl"
>
  <div
    class="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-brand-200/40 blur-3xl kz-blob-1 pointer-events-none"
  ></div>
  <div
    class="absolute -bottom-32 -right-32 w-[28rem] h-[28rem] rounded-full bg-brand-300/30 blur-3xl kz-blob-2 pointer-events-none"
  ></div>
  <div
    class="absolute top-1/2 left-1/3 w-72 h-72 rounded-full bg-brand-400/15 blur-3xl kz-blob-1 pointer-events-none"
    style="animation-delay: -7s;"
  ></div>

  <aside
    class="hidden lg:flex flex-1 flex-col justify-between p-12 xl:p-16 relative z-10"
    in:fly={{ x: 60, duration: 600, easing: quintOut }}
  >
    <div class="flex items-center gap-3">
      <div
        class="w-12 h-12 rounded-2xl bg-brand flex items-center justify-center text-white shadow-kz-brand"
      >
        <GraduationCap size={26} />
      </div>
      <div>
        <h1 class="text-xl font-bold text-brand">زكاة العلم</h1>
        <p class="text-xs font-medium text-ink-secondary">Knowledge Zakat</p>
      </div>
    </div>

    <div class="space-y-8 max-w-lg">
      <div class="space-y-4">
        <span
          class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/60 backdrop-blur border-kz border-brand-200 text-xs font-semibold text-brand"
        >
          <Sparkles size={14} />
          ابدأ رحلتك العلمية الآن
        </span>
        <h2 class="text-4xl xl:text-5xl font-bold text-brand leading-tight">
          انضم إلى<br />
          مجتمع طلاب العلم
        </h2>
        <p class="text-base xl:text-lg text-ink-secondary leading-relaxed">
          سجّل حسابك مجاناً واستمتع بالوصول لمكتبة واسعة من الدورات
          العلمية بإشراف نخبة من المعلمين.
        </p>
      </div>

      <div class="space-y-3">
        {#each [{ icon: BookOpen, label: 'دورات في جميع التخصصات' }, { icon: Users, label: 'مجتمع نشط من طلاب العلم' }, { icon: CheckCircle2, label: 'شهادات حضور موثّقة' }] as item, i (i)}
          {@const ItemIcon = item.icon}
          <div
            class="flex items-center gap-3 bg-white/60 backdrop-blur rounded-xl p-3 border-kz border-brand-200"
          >
            <div
              class="w-9 h-9 rounded-lg bg-brand-soft flex items-center justify-center"
            >
              <ItemIcon size={18} class="text-brand" />
            </div>
            <p class="text-sm font-semibold text-brand">{item.label}</p>
          </div>
        {/each}
      </div>
    </div>

    <p class="text-xs text-ink-muted">
      © {new Date().getFullYear()} زكاة العلم — جميع الحقوق محفوظة
    </p>
  </aside>

  <main
    class="flex-1 flex items-center justify-center p-6 md:p-12 relative z-10"
  >
    <div
      class="w-full max-w-md"
      in:fly={{ y: 30, duration: 500, easing: quintOut }}
    >
      <div class="lg:hidden flex items-center justify-center gap-3 mb-8">
        <div
          class="w-12 h-12 rounded-2xl bg-brand flex items-center justify-center text-white shadow-kz-brand"
        >
          <GraduationCap size={24} />
        </div>
        <h1 class="text-xl font-bold text-brand">زكاة العلم</h1>
      </div>

      <div
        class="bg-white rounded-modal p-8 md:p-10 shadow-kz-xl border-kz border-brand-200"
      >
        <header class="mb-6">
          <h2 class="text-2xl md:text-3xl font-bold text-brand">
            {currentStep === 1 ? 'إنشاء حساب جديد' : 'إكمال البيانات'}
          </h2>
          <p class="text-sm text-ink-secondary mt-2">
            {currentStep === 1
              ? 'املأ بياناتك الأساسية للبدء'
              : 'بضع تفاصيل أخرى وستكون جاهزاً'}
          </p>
        </header>

        <div class="flex items-center gap-2 mb-8">
          <div class="flex-1 h-1.5 rounded-full bg-brand-100 overflow-hidden">
            <div
              class="h-full bg-brand rounded-full transition-all duration-kz-normal ease-kz"
              style="width: {currentStep === 1 ? '50%' : '100%'};"
            ></div>
          </div>
          <span class="text-xs font-semibold text-ink-muted">
            {currentStep} / 2
          </span>
        </div>

        {#if currentStep === 1}
          <div in:fade={{ duration: 220 }} class="space-y-5">
            <div class="grid grid-cols-2 gap-3">
              <Input
                id="reg-firstname"
                label="الاسم الأول"
                bind:value={firstname}
                placeholder="الاسم الاول"
                icon={UserIcon}
                required
                disabled={isSubmitting}
              />
              <Input
                id="reg-lastname"
                label="الاسم الأخير"
                bind:value={lastname}
                placeholder="الاسم الاخير او اسم الوالد"
                required
                disabled={isSubmitting}
              />
            </div>
            <span dir="ltr" class="text-xs font-semibold text-ink-muted">
             {currentStep} / 2
            </span>
            <Input
              id="reg-email"
              label="البريد الإلكتروني"
              type="email"
              bind:value={email}
              placeholder="example@email.com"
              icon={Mail}
              autocomplete="email"
              required
              disabled={isSubmitting}
            />

            <Input
              id="reg-password"
              label="كلمة المرور"
              type="password"
              bind:value={password}
              placeholder="8+ أحرف، حرف كبير، صغير، رقم"
              icon={Lock}
              autocomplete="new-password"
              required
              disabled={isSubmitting}
              validation={passwordState}
              helperText={password === '' ? 'مثال: Password123' : undefined}
            />

            <Input
              id="reg-confirm"
              label="تأكيد كلمة المرور"
              type="password"
              bind:value={confirmPassword}
              placeholder="أعد كتابة كلمة المرور"
              icon={Lock}
              autocomplete="new-password"
              required
              disabled={isSubmitting}
              validation={confirmState}
              errorMessage={confirmState === 'error' ? 'كلمتا المرور غير متطابقتين' : ''}
            />

            <div class="space-y-2">
              <p class="text-xs font-semibold text-ink-secondary px-1">
                نوع الحساب
              </p>
              <div class="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onclick={() => (role = 'student')}
                  class="kz-card is-interactive p-4 text-right transition-all duration-kz-normal ease-kz {role ===
                  'student'
                    ? 'border-brand bg-brand-soft'
                    : ''}"
                >
                  <div class="flex items-center gap-3">
                    <div
                      class="w-10 h-10 rounded-xl flex items-center justify-center {role ===
                      'student'
                        ? 'bg-brand text-white'
                        : 'bg-brand-soft text-brand'}"
                    >
                      <UserCheck size={20} />
                    </div>
                    <div>
                      <p class="text-sm font-bold text-brand">طالب</p>
                      <p class="text-[10px] text-ink-muted">أتعلّم وأنمو</p>
                    </div>
                  </div>
                </button>
                <button
                  type="button"
                  onclick={() => (role = 'teacher')}
                  class="kz-card is-interactive p-4 text-right transition-all duration-kz-normal ease-kz {role ===
                  'teacher'
                    ? 'border-brand bg-brand-soft'
                    : ''}"
                >
                  <div class="flex items-center gap-3">
                    <div
                      class="w-10 h-10 rounded-xl flex items-center justify-center {role ===
                      'teacher'
                        ? 'bg-brand text-white'
                        : 'bg-brand-soft text-brand'}"
                    >
                      <GraduationCap size={20} />
                    </div>
                    <div>
                      <p class="text-sm font-bold text-brand">معلم</p>
                      <p class="text-[10px] text-ink-muted">أنشر العلم</p>
                    </div>
                  </div>
                </button>
              </div>
            </div>

            {#if step1Error}
              <div
                in:slide={{ duration: 220 }}
                class="bg-kz-error-soft text-kz-error-dark text-xs font-semibold p-3 rounded-button border-kz border-red-200"
              >
                {step1Error}
              </div>
            {/if}

            <Button
              variant="primary"
              size="lg"
              fullWidth
              iconRight={ArrowLeft}
              onclick={goToStep2}
              disabled={isSubmitting}
            >
              المتابعة
            </Button>
          </div>
        {:else}
          <div in:fade={{ duration: 220 }} class="space-y-5">
            <Input
              id="reg-birthday"
              label="تاريخ الميلاد"
              type="date"
              bind:value={birthday}
              icon={Calendar}
              disabled={isSubmitting}
            />

            <Input
              id="reg-phone"
              label="رقم الهاتف"
              type="tel"
              bind:value={phone}
              placeholder="07XXXXXXXXX"
              icon={Phone}
              disabled={isSubmitting}
              helperText="اختياري — لن يُحفظ في البيانات حالياً"
            />

            <div class="space-y-2">
              <label
                for="reg-bio"
                class="text-xs font-semibold text-ink-secondary px-1 block"
              >
                نبذة مختصرة
                {#if role === 'teacher'}
                  <span class="text-kz-error">*</span>
                {/if}
              </label>
              <textarea
                id="reg-bio"
                bind:value={bio}
                placeholder={role === 'teacher'
                  ? 'تخصصاتك وخبراتك التعليمية...'
                  : 'طموحاتك العلمية... (اختياري)'}
                disabled={isSubmitting}
                class="kz-focusable w-full px-4 py-3.5 bg-surface-input border-kz border-brand-200 rounded-button text-sm text-ink-primary placeholder:text-ink-muted h-28 resize-none disabled:opacity-60"
              ></textarea>
            </div>

            {#if role === 'teacher'}
              <div class="space-y-2" in:slide={{ duration: 220 }}>
                <p class="text-xs font-semibold text-ink-secondary px-1">
                  السيرة الذاتية / الشهادة
                  <span class="text-ink-muted">(اختياري)</span>
                </p>
                <label
                  class="flex items-center justify-center gap-3 w-full p-4 bg-surface-input border-kz border-dashed border-brand-200 rounded-button cursor-pointer hover:border-brand hover:bg-brand-50 transition-all duration-kz-normal ease-kz"
                >
                  {#if cvFile}
                    <CheckCircle2 size={20} class="text-kz-success" />
                    <span class="text-sm font-semibold text-brand line-clamp-1">
                      {cvFile.name}
                    </span>
                  {:else}
                    <Upload size={20} class="text-brand" />
                    <span class="text-sm font-medium text-ink-secondary">
                      اضغط لرفع ملف (PDF / صورة)
                    </span>
                  {/if}
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp,application/pdf"
                    onchange={handleCvSelect}
                    class="hidden"
                    disabled={isSubmitting}
                  />
                </label>
              </div>
            {/if}

            <div class="grid grid-cols-2 gap-3 pt-2">
              <Button
                variant="ghost"
                size="lg"
                fullWidth
                icon={ArrowRight}
                onclick={() => (currentStep = 1)}
                disabled={isSubmitting}
              >
                رجوع
              </Button>
              <Button
                variant="primary"
                size="lg"
                fullWidth
                loading={isSubmitting}
                icon={UserPlus}
                onclick={handleRegister}
              >
                {isSubmitting ? 'جاري الإنشاء...' : 'إنشاء الحساب'}
              </Button>
            </div>
          </div>
        {/if}

        <div class="relative my-8">
          <div class="absolute inset-0 flex items-center">
            <div class="w-full border-t border-brand-200"></div>
          </div>
          <div class="relative flex justify-center">
            <span class="bg-white px-4 text-xs font-medium text-ink-muted">
              أو
            </span>
          </div>
        </div>

        <div class="text-center">
          <p class="text-sm text-ink-secondary mb-3">لديك حساب بالفعل؟</p>
          <Button
            variant="outline"
            size="md"
            fullWidth
            onclick={() => navigate('login')}
            disabled={isSubmitting}
          >
            تسجيل الدخول
          </Button>
        </div>
      </div>
    </div>
  </main>
</div>

<style>
  :global(.kz-blob-1),
  :global(.kz-blob-2) {
    will-change: transform;
  }
</style>