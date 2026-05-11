<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, slide, scale } from 'svelte/transition';
  import api from '../lib/api';
  import { notify } from '../lib/notifications';
  import { Activity, Clock, User as UserIcon, ChevronRight, ChevronLeft } from 'lucide-svelte';

  interface LogRow { id: number; user_id: number; details: string | null; timestamp: string; }

  // ---- State --------------------------------------------------------------
  let logs = $state<LogRow[]>([]);
  let isLoading = $state(true);
  
  // متغيرات الترقيم (Pagination)
  let currentPage = $state(0);
  const itemsPerPage = 6; // عدد السجلات في كل صفحة

  // ---- Derived State ------------------------------------------------------
  // حساب السجلات المعروضة حالياً بناءً على الصفحة
  let totalPages = $derived(Math.max(1, Math.ceil(logs.length / itemsPerPage)));
  let currentLogs = $derived(
    logs.slice(currentPage * itemsPerPage, (currentPage + 1) * itemsPerPage)
  );

  onMount(async () => {
    try {
      const res = await api.get<LogRow[]>('/admin/logs');
      logs = res.data ?? [];
    } catch { notify.error('تعذّر جلب سجلات النشاط'); }
    finally { isLoading = false; }
  });

  function formatTimestamp(iso: string) {
    try {
      return new Date(iso).toLocaleString('ar-IQ', {
        hour: '2-digit', minute: '2-digit', year: 'numeric', month: 'numeric', day: 'numeric'
      });
    } catch { return iso; }
  }

  function goToPage(page: number) {
    currentPage = page;
  }
</script>

<div class="space-y-6 text-right" dir="rtl">
  <header class="flex justify-between items-center mb-6">
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 rounded-xl bg-brand-soft flex items-center justify-center text-brand">
        <Activity size={20} />
      </div>
      <h2 class="text-xl font-black text-brand">رصد النشاطات</h2>
    </div>
    <span class="bg-brand-soft text-brand px-4 py-2 rounded-full font-black text-[10px] uppercase tracking-widest">
      إجمالي السجلات: {logs.length}
    </span>
  </header>

  {#if isLoading}
    <div class="space-y-4 animate-pulse">
      {#each Array(5) as _} <div class="h-16 bg-white rounded-2xl"></div> {/each}
    </div>
  {:else if logs.length === 0}
    <div class="py-20 text-center border-4 border-dashed border-brand-100 rounded-[2.5rem] text-slate-400 font-bold">
      لا توجد سجلات حالياً
    </div>
  {:else}
    <div class="flex flex-col gap-3">
      {#each currentLogs as log (log.id)}
        <div in:slide class="bg-white p-5 rounded-2xl shadow-sm border border-brand-50 flex justify-between items-center group hover:border-brand transition-all">
          <div class="flex items-center gap-4">
            <div class="w-10 h-10 bg-slate-50 rounded-xl flex items-center justify-center text-slate-400 group-hover:text-brand transition-colors">
              <UserIcon size={18} />
            </div>
            <div class="flex flex-col">
              <span class="text-[10px] font-black text-slate-300 uppercase tracking-widest">المعرف #{log.user_id}</span>
              <p class="font-bold text-slate-600 text-sm">{log.details ?? '—'}</p>
            </div>
          </div>
          
          <div class="flex items-center gap-2 text-slate-400 bg-slate-50 px-4 py-2 rounded-xl border border-slate-100">
            <Clock size={14} />
            <span class="text-sm font-black font-mono tracking-tighter">
              {formatTimestamp(log.timestamp)}
            </span>
          </div>
        </div>
      {/each}
    </div>

    {#if totalPages > 1}
      <div class="mt-8 flex justify-between items-center bg-white/50 backdrop-blur-md p-3 rounded-2xl border border-brand-100 max-w-md mx-auto" in:fade>
        <button 
          onclick={() => goToPage(Math.min(totalPages - 1, currentPage + 1))} 
          disabled={currentPage === totalPages - 1}
          class="p-2 bg-white rounded-xl shadow-sm text-brand disabled:opacity-20 transition-all hover:scale-110"
        >
          <ChevronRight size={20} />
        </button>

        <div class="flex items-center gap-3">
          <span class="text-xs font-black text-slate-400">صفحة {currentPage + 1} من {totalPages}</span>
        </div>

        <button 
          onclick={() => goToPage(Math.max(0, currentPage - 1))} 
          disabled={currentPage === 0}
          class="p-2 bg-white rounded-xl shadow-sm text-brand disabled:opacity-20 transition-all hover:scale-110"
        >
          <ChevronLeft size={20} />
        </button>
      </div>
    {/if}
  {/if}
</div>