# 🚀 دليل هجرة Knowledge Zakat Frontend

## 📦 ما الذي تغيّر؟

استبدلنا بنية الـ routing والـ state القديمة ببنية type-safe جديدة تحل مشكلة الـ refresh وتنظّف الكود.

| القديم | الجديد |
|---|---|
| `currentPage` (string \| object) | `route` ({ name, param }) |
| `selectedTeacherId` store | `route.param` في URL |
| `selectedSessionId` store | `route.param` في URL |
| `localStorage.setItem('token', ...)` يدوياً | تلقائي عند `token.set(...)` |
| `alert()` / `console.error` / inline modals | `notify.success/error/info/warning(...)` |
| `<script>` (JS) | `<script lang="ts">` (TS) |

---

## 📂 خطوات التركيب

### 1. ضعي الملفات الجديدة في مكانها

```
src/
├── App.svelte                  ← استبدلي القديم
├── app.d.ts                    ← 🆕 جديد
├── lib/
│   ├── types.ts                ← 🆕 جديد
│   ├── stores.ts               ← استبدلي القديم
│   ├── router.ts               ← 🆕 جديد
│   ├── api.ts                  ← استبدلي القديم
│   └── notifications.ts        ← 🆕 جديد
└── components/
    └── Notification.svelte     ← 🆕 جديد
```

### 2. ثبّتي الـ TypeScript dependencies

في `package.json` تأكدي من وجود:
```json
{
  "devDependencies": {
    "typescript": "^5.0.0",
    "svelte-check": "^3.0.0",
    "@tsconfig/svelte": "^5.0.0"
  }
}
```

ثم:
```bash
npm install
```

### 3. أضيفي `tsconfig.json` (إذا غير موجود)

```json
{
  "extends": "@tsconfig/svelte/tsconfig.json",
  "compilerOptions": {
    "target": "ESNext",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "resolveJsonModule": true,
    "allowJs": true,
    "checkJs": false,
    "isolatedModules": true,
    "strict": true,
    "moduleResolution": "Bundler"
  },
  "include": ["src/**/*.d.ts", "src/**/*.ts", "src/**/*.svelte"]
}
```

### 4. أنشئي `.env` للفرونتند (اختياري)

```bash
# .env at project root
VITE_API_URL=http://127.0.0.1:8000
```

---

## 🔄 كيف تُهاجرين صفحة موجودة

افتحي أي صفحة قديمة (مثل `Home.svelte`) ونفّذي الاستبدالات التالية:

### استبدال 1: imports

```svelte
<!-- ❌ القديم -->
<script>
  import { currentPage, selectedTeacherId, selectedSessionId } from '../lib/stores';
  import api from '../lib/api';
</script>

<!-- ✅ الجديد -->
<script lang="ts">
  import { navigate } from '../lib/router';
  import { notify } from '../lib/notifications';
  import api from '../lib/api';
  import type { Session, User } from '../lib/types';
</script>
```

### استبدال 2: الانتقال بين الصفحات

```svelte
<!-- ❌ القديم -->
<button onclick={() => {
  selectedTeacherId.set(teacher.id);
  currentPage.set('teacher_view');
}}>عرض المعلم</button>

<!-- ✅ الجديد -->
<button onclick={() => navigate('teacher_view', teacher.id)}>
  عرض المعلم
</button>
```

### استبدال 3: قراءة الـ param في الصفحة المُستهدَفة

```svelte
<!-- ❌ القديم: TeacherView.svelte -->
<script>
  import { selectedTeacherId } from '../lib/stores';
  // الوصول عبر $selectedTeacherId
</script>

<!-- ✅ الجديد -->
<script lang="ts">
  import { route } from '../lib/router';
  
  // الـ param يأتي من URL، يمكنك الوصول له تفاعلياً
  let teacherId = $derived($route.param ? parseInt($route.param) : null);
</script>
```

### استبدال 4: alert / console.error → notify

```svelte
<!-- ❌ القديم -->
catch (e) {
  console.error(e);
  alert('فشل التحميل');
}

<!-- ✅ الجديد -->
catch (e) {
  notify.error('تعذّر تحميل البيانات، يرجى المحاولة لاحقاً');
}
```

### استبدال 5: تسجيل الخروج

```svelte
<!-- ❌ القديم -->
function handleLogout() {
  localStorage.clear();
  token.set(null);
  user.set(null);
  location.reload();
}

<!-- ✅ الجديد -->
import { logout } from '../lib/stores';
import { navigate } from '../lib/router';

function handleLogout() {
  logout();
  navigate('login', null, true);
  notify.info('تم تسجيل الخروج بنجاح');
}
```

### استبدال 6: تسجيل الدخول والتوجيه

```svelte
<!-- ❌ القديم -->
const response = await api.post('/token', { email, password });
token.set(response.data.access_token);
localStorage.setItem('token', response.data.access_token);
const userRes = await api.get('/users/me');
user.set(userRes.data);
localStorage.setItem('user', JSON.stringify(userRes.data));
currentPage.set('home');

<!-- ✅ الجديد (أبسط بكثير) -->
const response = await api.post('/token', { email, password });
token.set(response.data.access_token);  // localStorage يُحدَّث تلقائياً
const userRes = await api.get('/users/me');
user.set(userRes.data);                   // localStorage يُحدَّث تلقائياً
notify.success('مرحباً بعودتك!');
// التوجيه يحدث تلقائياً من App.svelte عبر الـ effect
```

---

## ⚠️ ملاحظات مهمة

### 1. الـ Routing الجديد يعمل فقط داخل `App.svelte`
لا تحتاجين إلى تغيير الـ Layouts (`StudentLayout.svelte`, `TeacherLayout.svelte`) إلا إذا كانت تستخدم `currentPage` للتنقل في القائمة الجانبية.

### 2. الصفحات القديمة ستعمل مؤقتاً
لأن `App.svelte` الجديد يدعم نفس أسماء الصفحات القديمة (`home`, `my_learning`, ...). يمكنك المهاجرة تدريجياً، صفحة بعد صفحة.

### 3. تحقّق من الكود بعد الهجرة
```bash
npx svelte-check
```

---

## 🧪 كيف تختبرين أن مشكلة الـ refresh انحلّت؟

1. سجّلي دخول
2. اذهبي إلى "جلساتي العلمية" (`#/my_learning`)
3. لاحظي الـ URL → يجب أن يكون: `http://localhost:5173/#/my_learning`
4. اضغطي F5 (تحديث) → يجب أن تبقي في نفس الصفحة ✅
5. اضغطي زر Back في المتصفح → يجب أن ترجعي للصفحة السابقة ✅

---

## 📞 استفسارات شائعة

**س: ما الفرق بين `route.set()` و `navigate()`؟**  
ج: لا تستخدمي `route.set()` أبداً — يتجاوز الـ URL ويجعل الـ refresh يكسر الصفحة من جديد. استخدمي `navigate()` فقط.

**س: كيف أمرّر بيانات معقدة بين الصفحات؟**  
ج: مرّري معرّف (ID) في الـ param، ثم اقرئي البيانات الكاملة في الصفحة الهدف عبر `api.get(...)`. البيانات في الـ URL ليست آمنة لمعلومات حساسة.

**س: هل يجب أن أحوّل كل الصفحات لـ TypeScript؟**  
ج: لا فوراً. الملفات الجديدة فقط هي TS. الصفحات القديمة تعمل كـ JS عادي حتى تُحدّثيها واحدة تلو الأخرى.
