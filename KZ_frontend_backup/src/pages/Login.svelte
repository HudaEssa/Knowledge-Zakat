<!--
  Knowledge Zakat — Login page (FINAL — backend-aligned).

  Backend contract (verified):
   - POST /token    : JSON { email, password }
                      → returns { access_token, token_type }
   - GET  /users/me : returns the authenticated user
-->

<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import api from '../lib/api';
  import { token, user } from '../lib/stores';
  import { navigate } from '../lib/router';
  import { notify } from '../lib/notifications';
  import type { User } from '../lib/types';
  import type { AxiosError } from 'axios';

  import Button from '../components/ui/Button.svelte';
  import Input from '../components/ui/Input.svelte';
  import { Mail, Lock, LogIn, GraduationCap, Sparkles, BookOpen, Users } from 'lucide-svelte';

  let email = $state('');
  let password = $state('');
  let isSubmitting = $state(false);
  let errorMessage = $state('');

  async function handleLogin(e?: Event): Promise<void> {
    e?.preventDefault();
    if (isSubmitting) return;

    if (!email.trim() || !password) {
      errorMessage = 'يرجى إدخال البريد وكلمة المرور';
      return;
    }

    isSubmitting = true;
    errorMessage = '';

    try {
      // Backend's /token expects JSON {email, password} (LoginInput
      // schema). It is NOT the OAuth2 password flow — sending
      // form-urlencoded would return 422 Unprocessable Content.
      const tokenRes = await api.post<{ access_token: string }>('/token', {
        email: email.trim(),
        password: password,
      });
      token.set(tokenRes.data.access_token);

      const meRes = await api.get<User>('/users/me');
      user.set(meRes.data);

      notify.success(`أهلاً بعودتك ${meRes.data.firstname}`);
      setTimeout(() => navigate('home', null, true), 400);
    } catch (err) {
      const ax = err as AxiosError<{ detail?: string }>;
      const detail = ax.response?.data?.detail;
      errorMessage =
        typeof detail === 'string'
          ? detail
          : 'البريد الإلكتروني أو كلمة المرور غير صحيحة';
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
          منصة تعليمية مفتوحة للجميع
        </span>
        <h2 class="text-4xl xl:text-5xl font-bold text-brand leading-tight">
          أنشر علمك،<br />
          واحصد أجراً جارياً
        </h2>
        <p class="text-base xl:text-lg text-ink-secondary leading-relaxed">
          منصة تجمع طلاب العلم بالأساتذة والخبراء في مختلف التخصصات،
          لتبادل المعرفة بأسلوب حديث ومنظّم.
        </p>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div
          class="bg-white/70 backdrop-blur rounded-2xl p-4 border-kz border-brand-200 transition-all duration-kz-normal ease-kz hover:bg-white hover:-translate-y-1"
        >
          <div class="w-10 h-10 rounded-xl bg-brand-soft flex items-center justify-center mb-3">
            <BookOpen size={20} class="text-brand" />
          </div>
          <p class="text-sm font-bold text-brand">دورات متنوعة</p>
          <p class="text-xs text-ink-muted mt-1">في كل التخصصات</p>
        </div>
        <div
          class="bg-white/70 backdrop-blur rounded-2xl p-4 border-kz border-brand-200 transition-all duration-kz-normal ease-kz hover:bg-white hover:-translate-y-1"
        >
          <div class="w-10 h-10 rounded-xl bg-brand-soft flex items-center justify-center mb-3">
            <Users size={20} class="text-brand" />
          </div>
          <p class="text-sm font-bold text-brand">معلمون موثوقون</p>
          <p class="text-xs text-ink-muted mt-1">خبرات حقيقية</p>
        </div>
      </div>
    </div>

  
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
        <header class="mb-8">
          <h2 class="text-2xl md:text-3xl font-bold text-brand">
            مرحباً بعودتك
          </h2>
          <p class="text-sm text-ink-secondary mt-2">
            سجّل دخولك لمتابعة رحلتك العلمية
          </p>
        </header>

        <form onsubmit={handleLogin} class="space-y-5">
          <Input
            id="login-email"
            label="البريد الإلكتروني"
            type="email"
            bind:value={email}
            placeholder="example@email.com"
            icon={Mail}
            autocomplete="email"
            required
            disabled={isSubmitting}
            errorMessage={errorMessage && !email.trim() ? errorMessage : ''}
            oninput={() => (errorMessage = '')}
          />

          <Input
            id="login-password"
            label="كلمة المرور"
            type="password"
            bind:value={password}
            placeholder="••••••••"
            icon={Lock}
            autocomplete="current-password"
            required
            disabled={isSubmitting}
            errorMessage={errorMessage && email.trim() ? errorMessage : ''}
            oninput={() => (errorMessage = '')}
          />

          <Button
            type="submit"
            variant="primary"
            size="lg"
            fullWidth
            loading={isSubmitting}
            icon={LogIn}
            onclick={handleLogin}
          >
            {isSubmitting ? 'جاري تسجيل الدخول...' : 'تسجيل الدخول'}
          </Button>
        </form>

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
          <p class="text-sm text-ink-secondary mb-3">ليس لديك حساب بعد؟</p>
          <Button
            variant="outline"
            size="md"
            fullWidth
            onclick={() => navigate('register')}
          >
            إنشاء حساب جديد
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