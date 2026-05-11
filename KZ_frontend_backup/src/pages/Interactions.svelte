<script>
  import { onMount } from "svelte";
  import api from "../lib/api";
  import { user } from "../lib/stores";

  let interactions = $state([]);
  let isLoading = $state(true);

  onMount(async () => {
    try {
      // جلب التقييمات من جدول Ratings
      const res = await api.get('/ratings/'); 
      // فلترة التقييمات لتشمل فقط ما يخص جلسات هذا المعلم (يحتاج تعديل Endpoint بالباكيند)
      interactions = res.data; 
    } finally { isLoading = false; }
  });
</script>

<div class="max-w-5xl mx-auto space-y-10">
  <h2 class="text-3xl font-black text-[#2a3c54]">آراء طلاب العلم</h2>

  <div class="grid gap-6">
    {#each interactions as item}
      <div class="bg-white p-8 rounded-[2.5rem] shadow-sm border border-slate-50 flex flex-col gap-4">
        <div class="flex justify-between items-start">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 bg-[#eff3fa] rounded-2xl flex items-center justify-center font-black text-[#6b8cce]">
              {item.user_id}
            </div>
            <div>
              <h4 class="font-black text-[#2a3c54]">طالب العلم رقم: {item.user_id}</h4>
              <p class="text-[10px] text-slate-400 font-bold uppercase">على جلسة: {item.session_id}</p>
            </div>
          </div>
          <div class="bg-emerald-50 text-emerald-600 px-4 py-1.5 rounded-xl font-black text-sm">
            {item.rate} / 5
          </div>
        </div>
        
        <div class="bg-slate-50 p-6 rounded-2xl italic text-slate-600 font-bold border-r-4 border-[#6b8cce]">
          "{item.comment || 'لا يوجد تعليق مكتوب.'}"
        </div>
      </div>
    {:else}
      <div class="py-40 text-center text-slate-300 font-black text-xl italic">لا توجد تفاعلات أو تقييمات حتى الآن.</div>
    {/each}
  </div>
</div>