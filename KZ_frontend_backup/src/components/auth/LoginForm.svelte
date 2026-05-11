<!--
  Knowledge Zakat — Login Form.

  Self-contained login form: own state, own submit handler, own
  error display. Emits `onSuccess` after the token is stored and
  the user is fetched so the parent can navigate away.

  Backend contract (unchanged):
   - POST /token    : JSON { email, password } → { access_token }
   - GET  /users/me : returns the authenticated user
-->

<script lang="ts">
  import api from '../../lib/api';
  import { token, user } from '../../lib/stores';
  import { notify } from '../../lib/notifications';
  import type { User } from '../../lib/types';
  import type { AxiosError } from 'axios';

  import Button from '../ui/Button.svelte';
  import Input from '../ui/Input.svelte';
  import GuestExitLink from './GuestExitLink.svelte';
  import { Mail, Lock, LogIn } from 'lucide-svelte';

  interface Props {
    /** Called after a successful login (token + user already saved). */
    onSuccess: (user: User) => void;
    /** Called when the visitor clicks "browse as guest". */
    onGuest: () => void;
  }

  let { onSuccess, onGuest }: Props = $props();

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
      // 1. تجهيز البيانات
      const params = new URLSearchParams();
      params.append('username', email.trim());
      params.append('password', password);

      // 2. جلب التوكن
      const tokenRes = await api.post<{ access_token: string }>('/token', params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      const currentToken = tokenRes.data.access_token;
      token.set(currentToken);

      // 3. 👈 السر الجديد والنظيف: نجبر الـ Axios يثبت التوكن فوراً بالهيدر العام
      api.defaults.headers.common['Authorization'] = `Bearer ${currentToken}`;

      // 4. 👈 هسة نطلب بيانات اليوزر طبيعي (التايب سكربت راح يسكت وماكو 401 بعد!)
      const meRes = await api.get<User>('/users/me');
      
      user.set(meRes.data);

      notify.success(`أهلاً بعودتك ${meRes.data.firstname}`);
      onSuccess(meRes.data);
      
    } catch (err) {
      const ax = err as AxiosError<{ detail?: string }>;
      
      if (ax.response?.status === 429) {
        errorMessage = 'تجاوزت الحد المسموح من المحاولات، يرجى الانتظار دقيقة.';
      } else {
        const detail = ax.response?.data?.detail;
        errorMessage = typeof detail === 'string' ? detail : 'البريد الإلكتروني أو كلمة المرور غير صحيحة';
      }
    } finally {
      isSubmitting = false;
    }
  }
</script>

<div
  class="bg-white rounded-modal p-7 md:p-9 shadow-kz-xl border-kz border-brand-200"
>
  <header class="mb-7">
    <h2 class="text-2xl md:text-3xl font-bold text-brand">مرحباً بعودتك</h2>
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

  <GuestExitLink onClick={onGuest} />
</div>
