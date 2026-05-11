<!--
  Knowledge Zakat — Register Form.

  Self-contained two-step registration form. Step 1 collects the
  essentials (name, email, password, role); step 2 collects optional
  profile info plus the teacher CV upload if "معلم" was selected.

  Emits `onSuccess` after the user is created, auto-logged in, and
  (optionally) a teacher request has been submitted. Parent decides
  where to navigate next.

  Backend contract (unchanged):
   - POST /users/             : create user → UserResponse (NOT a token)
   - POST /token              : auto-login → { access_token }
   - POST /users/upload-cv    : upload CV file (teacher applications)
   - POST /users/request-teacher : submit teacher promotion request
-->

<script lang="ts">
  import { fade, slide } from 'svelte/transition';
  import api from '../../lib/api';
  import { token, user } from '../../lib/stores';
  import { notify } from '../../lib/notifications';
  import type { User } from '../../lib/types';
  import type { AxiosError } from 'axios';

  import Button from '../ui/Button.svelte';
  import Input from '../ui/Input.svelte';
  import GuestExitLink from './GuestExitLink.svelte';
  import {
    User as UserIcon,
    Mail,
    Lock,
    Phone,
    Calendar,
    UserPlus,
    UserCheck,
    GraduationCap,
    ArrowLeft,
    ArrowRight,
    Upload,
    CheckCircle2,
  } from 'lucide-svelte';

  interface Props {
    onSuccess: (user: User) => void;
    onGuest: () => void;
  }

  let { onSuccess, onGuest }: Props = $props();

  // ────────────────────────────────────────────────────────────
  // State
  // ────────────────────────────────────────────────────────────
  type RoleChoice = 'student' | 'teacher';
  type ValidationState = 'idle' | 'success' | 'error';

  let currentStep = $state<1 | 2>(1);

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

  let passwordState = $derived<ValidationState>(
    password === ''
      ? 'idle'
      : isPasswordStrong(password)
        ? 'success'
        : 'error',
  );

  let confirmState = $derived<ValidationState>(
    confirmPassword === ''
      ? 'idle'
      : confirmPassword === password
        ? 'success'
        : 'error',
  );

  // ────────────────────────────────────────────────────────────
  // Step navigation
  // ────────────────────────────────────────────────────────────
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
      step1Error =
        'كلمة المرور يجب أن تحتوي 8 أحرف على الأقل + حرف كبير + صغير + رقم';
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

    if (
      !['image/jpeg', 'image/png', 'image/webp', 'application/pdf'].includes(
        file.type,
      )
    ) {
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

  // ────────────────────────────────────────────────────────────
  // Submit
  // ────────────────────────────────────────────────────────────
  async function handleRegister(): Promise<void> {
    if (isSubmitting) return;
    isSubmitting = true;

    try {
      // 1. Create the account.
      await api.post('/users/', {
        firstname: firstname.trim(),
        lastname: lastname.trim(),
        email: email.trim(),
        password,
        bio: bio.trim() || null,
        birthday_date: birthday || null,
      });

      // 2. Auto-login to get a token + fetch the user.
      const tokenRes = await api.post<{ access_token: string }>('/token', {
        email: email.trim(),
        password: password,
      });
      token.set(tokenRes.data.access_token);

      const meRes = await api.get<User>('/users/me');
      user.set(meRes.data);

      // 3. Optional teacher promotion request.
      if (role === 'teacher') {
        try {
          let finalCvLink: string | null = null;
          if (cvFile) {
            const fd = new FormData();
            fd.append('file', cvFile);
            const uploadRes = await api.post<{ cv_link: string }>(
              '/users/upload-cv',
              fd,
              { headers: { 'Content-Type': 'multipart/form-data' } },
            );
            finalCvLink = uploadRes.data.cv_link;
          }
          await api.post('/users/request-teacher', {
            phone: phone.trim(),
            cv_link: finalCvLink,
          });
          notify.info('تم استلام طلبك كمعلم وهو قيد المراجعة');
        } catch {
          notify.error('تم إنشاء الحساب لكن فشل إرسال طلب المعلم');
        }
      }

      notify.success(`أهلاً بك في زكاة العلم، ${meRes.data.firstname}!`);
      onSuccess(meRes.data);
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
  class="bg-white rounded-modal p-7 md:p-9 shadow-kz-xl border-kz border-brand-200"
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

  <!-- Step progress -->
  <div class="flex items-center gap-2 mb-6">
    <div class="flex-1 h-1.5 rounded-full bg-brand-100 overflow-hidden">
      <div
        class="h-full bg-brand rounded-full transition-all duration-kz-normal ease-kz"
        style="width: {currentStep === 1 ? '50%' : '100%'};"
      ></div>
    </div>
    <span dir="ltr" class="text-xs font-semibold text-ink-muted">
      {currentStep} / 2
    </span>
  </div>

  {#if currentStep === 1}
    <!-- ──────────────────────────────────────────────────────── -->
    <!-- STEP 1: essentials                                      -->
    <!-- ──────────────────────────────────────────────────────── -->
    <div in:fade={{ duration: 220 }} class="space-y-4">
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
          placeholder="او اسم الوالد"
          required
          disabled={isSubmitting}
        />
      </div>

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
        errorMessage={confirmState === 'error'
          ? 'كلمتا المرور غير متطابقتين'
          : ''}
      />

      <!-- Role selector -->
      <div class="space-y-2">
        <p class="text-xs font-semibold text-ink-secondary px-1">
          نوع الحساب
        </p>
        <div class="grid grid-cols-2 gap-3">
          <button
            type="button"
            onclick={() => (role = 'student')}
            class="kz-card is-interactive p-3 text-right transition-all duration-kz-normal ease-kz {role ===
            'student'
              ? 'border-brand bg-brand-soft'
              : ''}"
          >
            <div class="flex items-center gap-3">
              <div
                class="w-9 h-9 rounded-xl flex items-center justify-center {role ===
                'student'
                  ? 'bg-brand text-white'
                  : 'bg-brand-soft text-brand'}"
              >
                <UserCheck size={18} />
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
            class="kz-card is-interactive p-3 text-right transition-all duration-kz-normal ease-kz {role ===
            'teacher'
              ? 'border-brand bg-brand-soft'
              : ''}"
          >
            <div class="flex items-center gap-3">
              <div
                class="w-9 h-9 rounded-xl flex items-center justify-center {role ===
                'teacher'
                  ? 'bg-brand text-white'
                  : 'bg-brand-soft text-brand'}"
              >
                <GraduationCap size={18} />
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
    <!-- ──────────────────────────────────────────────────────── -->
    <!-- STEP 2: optional profile + (if teacher) CV upload       -->
    <!-- ──────────────────────────────────────────────────────── -->
    <div in:fade={{ duration: 220 }} class="space-y-4">
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
        helperText="اختياري"
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
          class="kz-focusable w-full px-4 py-3 bg-surface-input border-kz border-brand-200 rounded-button text-sm text-ink-primary placeholder:text-ink-muted h-24 resize-none disabled:opacity-60"
        ></textarea>
      </div>

      {#if role === 'teacher'}
        <div class="space-y-2" in:slide={{ duration: 220 }}>
          <p class="text-xs font-semibold text-ink-secondary px-1">
            السيرة الذاتية / الشهادة
            <span class="text-ink-muted">(اختياري)</span>
          </p>
          <label
            class="flex items-center justify-center gap-3 w-full p-3 bg-surface-input border-kz border-dashed border-brand-200 rounded-button cursor-pointer hover:border-brand hover:bg-brand-50 transition-all duration-kz-normal ease-kz"
          >
            {#if cvFile}
              <CheckCircle2 size={18} class="text-kz-success" />
              <span class="text-sm font-semibold text-brand line-clamp-1">
                {cvFile.name}
              </span>
            {:else}
              <Upload size={18} class="text-brand" />
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

      <div class="grid grid-cols-2 gap-3 pt-1">
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

  <GuestExitLink onClick={onGuest} />
</div>