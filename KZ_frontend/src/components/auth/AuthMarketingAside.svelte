<!--
  Knowledge Zakat — Auth Marketing Aside.

  The decorative left column on desktop. Hidden on mobile (<lg) so
  the form takes the full width on phones.

  Emits one event:
   - `guest`: fired when the visitor clicks "تصفح كزائر بدون تسجيل".
              Parent decides what to navigate to (we keep this dumb).
-->

<script lang="ts">
  import { fly } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import {
    GraduationCap,
    Sparkles,
    BookOpen,
    Users,
    Eye,
    ArrowLeft,
  } from 'lucide-svelte';

  interface Props {
    /** Called when the user clicks the "browse as guest" link. */
    onGuest: () => void;
  }

  let { onGuest }: Props = $props();
</script>

<aside
  class="hidden lg:flex flex-1 flex-col justify-between p-12 xl:p-16 relative z-10"
  in:fly={{ x: 60, duration: 600, easing: quintOut }}
>
  <!-- Brand mark -->
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

  <!-- Marketing copy -->
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

    <!-- Feature cards -->
    <div class="grid grid-cols-2 gap-4">
      <div
        class="bg-white/70 backdrop-blur rounded-2xl p-4 border-kz border-brand-200 transition-all duration-kz-normal ease-kz hover:bg-white hover:-translate-y-1"
      >
        <div
          class="w-10 h-10 rounded-xl bg-brand-soft flex items-center justify-center mb-3"
        >
          <BookOpen size={20} class="text-brand" />
        </div>
        <p class="text-sm font-bold text-brand">دورات متنوعة</p>
        <p class="text-xs text-ink-muted mt-1">في كل التخصصات</p>
      </div>
      <div
        class="bg-white/70 backdrop-blur rounded-2xl p-4 border-kz border-brand-200 transition-all duration-kz-normal ease-kz hover:bg-white hover:-translate-y-1"
      >
        <div
          class="w-10 h-10 rounded-xl bg-brand-soft flex items-center justify-center mb-3"
        >
          <Users size={20} class="text-brand" />
        </div>
        <p class="text-sm font-bold text-brand">معلمون موثوقون</p>
        <p class="text-xs text-ink-muted mt-1">خبرات حقيقية</p>
      </div>
    </div>

    <!-- Guest entry -->
    <button
      type="button"
      onclick={onGuest}
      class="group inline-flex items-center gap-2 text-sm font-bold text-brand hover:text-brand-dark transition-colors"
    >
      <Eye size={16} />
      <span>تصفح كزائر بدون تسجيل</span>
      <ArrowLeft
        size={14}
        class="opacity-60 group-hover:-translate-x-1 transition-transform"
      />
    </button>
  </div>

  <p class="text-xs text-ink-muted">
    © {new Date().getFullYear()} زكاة العلم
  </p>
</aside>
