# 🔐 Auth Components — معزولة بالكامل

هذا المجلد فيه **كل** ما يخص واجهات الـ Authentication.
لا يوجد أي ملف خارج هذا المجلد يحتوي على JSX/HTML خاص بالـ Auth.

## 📁 البنية النهائية

```
src/
├── pages/
│   └── Auth.svelte                ⭐ مجرد orchestrator (≈90 سطر)
└── components/
    └── auth/                      ← هذا المجلد
        ├── AuthBackground.svelte      البلوبز المتحركة
        ├── AuthMarketingAside.svelte  الـ aside اليساري الترويجي
        ├── AuthModeTabs.svelte        تابز Login | Register فوك
        ├── AuthFlipCard.svelte        wrapper الـ 3D flip
        ├── LoginForm.svelte           فورم تسجيل الدخول
        ├── RegisterForm.svelte        فورم إنشاء حساب (متعدد الخطوات)
        └── GuestExitLink.svelte       زر "تصفح كزائر"
```

## 🎯 مبدأ التصميم

كل مكون مسؤول عن **شيء واحد فقط**:

| المكون | المسؤولية | التبعيات |
|---|---|---|
| `AuthBackground` | عرض البلوبز | ✅ pure (بدون state) |
| `AuthMarketingAside` | الـ marketing copy | ✅ pure (handler واحد بس) |
| `AuthModeTabs` | عرض الـ pill toggle | ✅ controlled (mode + onChange) |
| `AuthFlipCard` | عرض الـ 3D flip animation | ✅ pure (snippets) |
| `LoginForm` | إدارة state + submit الـ login | 🔄 يستعمل token/user stores |
| `RegisterForm` | إدارة state + submit الـ register | 🔄 يستعمل token/user stores |
| `GuestExitLink` | زر "تصفح كزائر" | ✅ pure |
| `Auth.svelte` | تركيب القطع و توجيه الـ navigation | 🔄 router |

## 🔌 API الموحد

كل مكون يأخذ props واضحة عبر `interface Props`:

```ts
// LoginForm.svelte
interface Props {
  onSuccess: (user: User) => void;
  onGuest: () => void;
}

// RegisterForm.svelte
interface Props {
  onSuccess: (user: User) => void;
  onGuest: () => void;
}

// AuthModeTabs.svelte
interface Props {
  mode: 'login' | 'register';
  onChange: (mode: 'login' | 'register') => void;
}

// AuthFlipCard.svelte
interface Props {
  isFlipped: boolean;
  front: Snippet;
  back: Snippet;
  minHeight?: string;
}
```

## ✨ فوائد العزل

### 1. لا تداخل مع بقية الصفحات
الـ `flip-stage`, `flip-card`, `kz-blob-1`, `kz-blob-2` كلها محصورة
داخل `AuthFlipCard` و `AuthBackground` فقط. ما تصير conflicts مع
الـ Home أو SessionDetails أو غيرهم.

### 2. تكدر تختبر كل قطعة لحالها
```svelte
<!-- Storybook example -->
<LoginForm onSuccess={() => {}} onGuest={() => {}} />
```

### 3. تكدر تعيد استخدام الفورمات بمكان آخر
ممكن مستقبلاً تستعمل `LoginForm` داخل modal:
```svelte
<!-- داخل modal على Home -->
<LoginModal>
  <LoginForm onSuccess={closeModal} onGuest={closeModal} />
</LoginModal>
```

### 4. تعديل أي قطعة ما يكسر الباقي
- تريد تغير تصميم التابز؟ → بس عدل `AuthModeTabs.svelte`
- تريد تضيف SSO buttons للـ login؟ → بس عدل `LoginForm.svelte`
- تريد تغير الـ animation timing للـ flip؟ → بس عدل `AuthFlipCard.svelte`

## 🚀 التنصيب

```bash
# 1. أنشئ المجلد
mkdir -p src/components/auth

# 2. انسخ الـ 7 ملفات هذي إلى src/components/auth/
cp AuthBackground.svelte AuthMarketingAside.svelte AuthModeTabs.svelte \
   AuthFlipCard.svelte LoginForm.svelte RegisterForm.svelte \
   GuestExitLink.svelte src/components/auth/

# 3. انسخ Auth.svelte الجديد إلى src/pages/
cp Auth.svelte src/pages/

# 4. احذف الصفحات القديمة
rm src/pages/Login.svelte src/pages/Register.svelte
```

## 📊 المقارنة قبل/بعد

| المقياس | قبل العزل | بعد العزل |
|---|---|---|
| سطور `Auth.svelte` | ~700 | ~90 ✨ |
| ملفات منفصلة | 1 | 7 |
| إمكانية إعادة الاستخدام | ❌ | ✅ |
| سهولة الـ testing | 🟡 صعب | 🟢 سهل |
| تأثير التعديل على باقي الصفحات | ⚠️ احتمال | 🟢 صفر |
