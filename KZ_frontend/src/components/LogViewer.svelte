<script>
  import { onMount } from "svelte";
  import api from "../lib/api";
  import { fade, slide } from "svelte/transition";

  // إعدادات الحالة باستخدام Svelte 5 Runes
  let logs = $state([]);
  let isLoading = $state(true);
  
  // إعدادات الترقيم (Pagination)
  let currentPage = $state(0);
  const itemsPerPage = 8; // عدد السجلات في كل صفحة

  onMount(async () => {
    try {
      const res = await api.get("/admin/logs");
      logs = res.data;
    } catch (error) {
      console.error("فشل في جلب سجلات النشاط:", error);
    } finally {
      isLoading = false;
    }
  });

  // حساب إجمالي الصفحات بشكل تلقائي (Derived State)
  let totalPages = $derived(Math.ceil(logs.length / itemsPerPage));

  // تصفية السجلات التي تظهر في الصفحة الحالية فقط
  let currentLogs = $derived(
    logs.slice(currentPage * itemsPerPage, (currentPage + 1) * itemsPerPage)
  );

  // وظائف التنقل
  function nextPage() {
    if (currentPage < totalPages - 1) currentPage++;
  }

  function prevPage() {
    if (currentPage > 0) currentPage--;
  }

  function goToPage(page) {
    currentPage = page;
  }
</script>

<div class="bg-white rounded-[2.5rem] p-10 shadow-sm border border-slate-50 text-right" dir="rtl">
  <header class="flex justify-between items-center mb-8">
    <h2 class="text-xl font-black text-[#4a6583] border-r-4 border-[#6b8cce] pr-4">رصد النشاطات 📡</h2>
    {#if !isLoading}
      <span class="text-[10px] font-black text-slate-300 uppercase tracking-widest bg-slate-50 px-4 py-2 rounded-full">
        إجمالي السجلات: {logs.length}
      </span>
    {/if}
  </header>

  {#if isLoading}
    <div class="py-20 text-center flex flex-col items-center gap-4">
      <div class="w-10 h-10 border-4 border-[#6b8cce] border-t-transparent rounded-full animate-spin"></div>
      <p class="text-slate-400 font-bold italic">جاري جلب سجلات النظام...</p>
    </div>
  {:else}
    <div class="overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="text-slate-400 border-b font-black">
            <th class="pb-6 text-right">المستخدم</th>
            <th class="pb-6 text-right">النشاط</th>
            <th class="pb-6 text-left">التوقيت</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-50">
          {#each currentLogs as log (log.id || Math.random())}
            <tr in:slide class="hover:bg-slate-50/50 transition-all group">
              <td class="py-6 font-black text-[#6b8cce] group-hover:scale-105 transition-transform origin-right">
                #{log.user_id}
              </td>
              <td class="py-6 font-medium text-slate-600">
                {log.details}
              </td>
              <td class="py-6 text-slate-400 text-[10px] text-left font-mono">
                {new Date(log.timestamp).toLocaleString('ar-IQ')}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    {#if totalPages > 1}
      <div class="mt-10 flex flex-col md:flex-row items-center justify-between gap-6 border-t border-slate-50 pt-8">
        <div class="flex items-center gap-2">
          <button 
            onclick={prevPage} 
            disabled={currentPage === 0}
            class="px-5 py-2.5 bg-white border border-slate-100 rounded-xl font-black text-xs text-[#4a6583] shadow-sm disabled:opacity-20 hover:bg-slate-50 transition-all"
          >
            السابق
          </button>

          <div class="flex gap-1 mx-2">
            {#each Array(totalPages) as _, i}
              {#if i === 0 || i === totalPages - 1 || (i >= currentPage - 1 && i <= currentPage + 1)}
                <button 
                  onclick={() => goToPage(i)}
                  class="w-8 h-8 rounded-lg font-black text-[10px] transition-all {currentPage === i ? 'bg-[#2a3c54] text-white shadow-md' : 'text-slate-300 hover:text-[#4a6583]'}"
                >
                  {i + 1}
                </button>
              {:else if i === currentPage - 2 || i === currentPage + 2}
                <span class="text-slate-200">..</span>
              {/if}
            {/each}
          </div>

          <button 
            onclick={nextPage} 
            disabled={currentPage === totalPages - 1}
            class="px-5 py-2.5 bg-[#2a3c54] rounded-xl font-black text-xs text-white shadow-lg shadow-[#2a3c54]/20 disabled:opacity-20 hover:scale-105 transition-all"
          >
            التالي
          </button>
        </div>

        <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest">
          صفحة {currentPage + 1} من أصل {totalPages}
        </p>
      </div>
    {/if}
  {/if}
</div>