<script lang="ts">
  // Svelte 5 Props - لضمان المزامنة التلقائية بدون إيرورات
  let { stats, isLoading = false } = $props<{
    stats: { students: number; teachers: number; sessions: number; requests: number; };
    isLoading?: boolean;
  }>();

  import { scale, fly } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import { 
    Users, 
    UserStar, 
    Presentation, 
    ClipboardCheck 
  } from 'lucide-svelte';

  // مصفوفة البيانات لترتيب الكود (DRY) مثل ستايل المحترفين
  const statCards = $derived([
    { id: 'students', label: 'الطلاب', value: stats.students, icon: Users, color: 'brand', delay: 0 },
    { id: 'teachers', label: 'المعلمون', value: stats.teachers, icon: UserStar, color: 'brand', delay: 100 },
    { id: 'sessions', label: 'الجلسات', value: stats.sessions, icon: Presentation, color: 'brand', delay: 200 },
    { id: 'requests', label: 'الطلبات', value: stats.requests, icon: ClipboardCheck, color: 'orange', delay: 300 }
  ]);
</script>

<div class="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-10 text-right" dir="rtl">
  {#each statCards as card}
    <div 
      in:fly={{ y: 20, duration: 600, delay: card.delay, easing: cubicOut }}
      class="relative overflow-hidden group {card.color === 'brand' ? 'bg-white/70' : 'bg-white/70'} 
             backdrop-blur-md p-6 rounded-[2.5rem] border border-slate-100 shadow-sm 
             hover:shadow-xl hover:-translate-y-1 transition-all duration-300"
    >
      <div class="flex flex-col items-center lg:items-start gap-4">
        
        <div class="relative">
          <div class="absolute inset-0 scale-150 blur-2xl opacity-20 {card.color === 'brand' ? 'bg-brand' : 'bg-orange-400'}"></div>
          
          <div class="relative w-14 h-14 rounded-2xl flex items-center justify-center transition-transform group-hover:scale-110
               {card.color === 'brand' ? 'bg-brand-soft/30 text-brand' : 'bg-orange-50 text-orange-500'}">
            <card.icon size={28} strokeWidth={2.5} />
          </div>
        </div>

        <div class="mt-2 text-center lg:text-right">
          <p class="text-[11px] font-black {card.color === 'brand' ? 'text-slate-400' : 'text-orange-400'} uppercase tracking-[0.1em] mb-1">
            {card.label}
          </p>
          <div class="text-3xl font-black text-[#2a3c54] font-mono tracking-tighter">
            {#if isLoading}
              <span class="inline-block animate-pulse">...</span>
            {:else}
              <div in:scale={{ duration: 400, start: 0.8 }}>{card.value}</div>
            {/if}
          </div>
        </div>
      </div>

      <div class="absolute -bottom-4 -left-4 w-24 h-24 rounded-full blur-3xl opacity-10 
           {card.color === 'brand' ? 'bg-brand' : 'bg-orange-400'}"></div>
    </div>
  {/each}
</div>

<style>
  /* إضافة خط مخصص للأرقام إذا متوفر، أو الاعتماد على مونو */
  :global(.font-mono) {
    font-variant-numeric: tabular-nums;
  }
</style>