<script lang="ts">
  import { fly, fade } from 'svelte/transition';
  import { backOut, cubicOut } from 'svelte/easing';
  import { notifications, dismiss } from '../lib/notifications';
  import { 
    CheckCircle2, 
    XCircle, 
    AlertTriangle, 
    Info, 
    X 
  } from 'lucide-svelte';

  // تعريف الستايلات لكل نوع من أنواع التنبيهات
  const CONFIG = {
    success: {
      bg: 'bg-white/90',
      border: 'border-emerald-500/20',
      accent: 'bg-emerald-500',
      iconColor: 'text-emerald-500',
      textColor: 'text-slate-700',
      Icon: CheckCircle2
    },
    error: {
      bg: 'bg-white/90',
      border: 'border-red-500/20',
      accent: 'bg-red-500',
      iconColor: 'text-red-500',
      textColor: 'text-slate-700',
      Icon: XCircle
    },
    warning: {
      bg: 'bg-white/90',
      border: 'border-amber-500/20',
      accent: 'bg-amber-500',
      iconColor: 'text-amber-500',
      textColor: 'text-slate-700',
      Icon: AlertTriangle
    },
    info: {
      bg: 'bg-white/90',
      border: 'border-sky-500/20',
      accent: 'bg-sky-500',
      iconColor: 'text-sky-500',
      textColor: 'text-slate-700',
      Icon: Info
    }
  };
</script>

<div
  class="fixed top-6 left-6 z-[9999] flex flex-col gap-4 pointer-events-none w-full max-w-[380px]"
  aria-live="polite"
>
  {#each $notifications as n (n.id)}
    {@const cfg = CONFIG[n.kind] || CONFIG.info}
    {@const Icon = cfg.Icon} 
    
    <div
      dir="rtl"
      role={n.kind === 'error' ? 'alert' : 'status'}
      class="pointer-events-auto relative overflow-hidden rounded-[1.5rem] border {cfg.border} {cfg.bg} shadow-2xl backdrop-blur-md flex items-start gap-4 p-5 transition-all hover:scale-[1.02]"
      in:fly={{ x: -50, duration: 500, easing: backOut }}
      out:fade={{ duration: 200, easing: cubicOut }}
    >
      <div class="absolute right-0 top-0 bottom-0 w-1.5 {cfg.accent}"></div>

      <div class="shrink-0 mt-0.5 {cfg.iconColor}">
        <Icon size={22} strokeWidth={2.5} />
      </div>

      <div class="flex-1">
        <p class="text-xs font-black leading-relaxed {cfg.textColor}">
          {n.message}
        </p>
      </div>

      <button
        type="button"
        onclick={() => dismiss(n.id)}
        class="shrink-0 p-1 rounded-full text-slate-300 hover:text-slate-500 hover:bg-slate-100 transition-all group"
        aria-label="إغلاق"
      >
        <X size={16} strokeWidth={3} class="group-hover:rotate-90 transition-transform duration-300" />
      </button>

      <div 
        class="absolute bottom-0 left-0 h-1 {cfg.accent} opacity-20 w-full origin-left progress-anim"
      ></div>
    </div>
  {/each}
</div>

<style>
  /* تحريك شريط الوقت ليختفي تدريجياً خلال 5 ثوانٍ */
  .progress-anim {
    animation: shrink 5s linear forwards;
  }

  @keyframes shrink {
    from { transform: scaleX(1); }
    to { transform: scaleX(0); }
  }

  /* تطبيق الخط الرئيسي للمنصة */
  div {
    font-family: 'Tajawal', sans-serif;
  }
</style>