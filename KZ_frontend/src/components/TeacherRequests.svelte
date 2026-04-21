<script>
  import api from "../lib/api";
  import { fade, scale } from "svelte/transition";
  import { onMount } from "svelte";

  // إدارة الحالة باستخدام Svelte 5 Runes
  let pendingRequests = $state([]);
  let historyRequests = $state([]);
  let isLoading = $state(true);

  // جلب الطلبات عند فتح الصفحة
  onMount(async () => {
    try {
      const token = localStorage.getItem("token");
      
      // جلب الطلبات الجديدة والسجل بوقت واحد
      const [pendingRes, historyRes] = await Promise.all([
        api.get('/teacher/enrollments/pending', { headers: { Authorization: `Bearer ${token}` } }),
        api.get('/teacher/enrollments/history', { headers: { Authorization: `Bearer ${token}` } })
      ]);
      
      pendingRequests = pendingRes.data.map(req => ({ ...req, processedMessage: null, isProcessing: false }));
      historyRequests = historyRes.data;

    } catch (e) {
      console.error("فشل جلب الطلبات الأكاديمية", e);
    } finally {
      isLoading = false;
    }
  });

  /**
   * دالة تحديث حالة الانضمام
   */
  async function handleAction(req, newStatus) {
    if (req.isProcessing) return;
    
    req.isProcessing = true;
    try {
      const token = localStorage.getItem("token");
      await api.put('/enrollments/status', {
        user_id: req.user_id,
        session_id: req.session_id,
        status: newStatus 
      }, { headers: { Authorization: `Bearer ${token}` } });
      
      // تعيين رسالة النجاح البصرية
      req.processedMessage = newStatus === 'approved' ? '✅ تم قبول الطالب بنجاح' : '❌ تم رفض الطلب';
      
      // بعد ثانية ونص، نشيل الطلب من الجدد ونحطه بالسجل
      setTimeout(() => {
        pendingRequests = pendingRequests.filter(r => r !== req);
        
        // إضافة الطلب إلى قائمة السجل ليظهر بالأسفل
        req.status = newStatus;
        historyRequests = [req, ...historyRequests];
      }, 1500);

    } catch (err) { 
      req.processedMessage = "⚠️ حدث خطأ في الخادم";
      req.isProcessing = false;
      setTimeout(() => req.processedMessage = null, 3000);
    }
  }
</script>

<div class="space-y-12 text-right pb-20" dir="rtl">

  <section>
    <h1 class="text-3xl font-black text-[#2a3c54] border-r-8 border-[#6b8cce] pr-4 mb-8">طلبات الانضمام الجديدة</h1>

    {#if isLoading}
      <div class="py-20 text-center flex flex-col items-center gap-4">
          <div class="w-10 h-10 border-4 border-[#2a3c54] border-t-transparent rounded-full animate-spin"></div>
          <p class="text-[#2a3c54] font-black animate-pulse text-lg">جاري جلب بيانات الطلاب...</p>
      </div>
    {:else if pendingRequests.length === 0}
      <div in:fade class="py-20 text-center text-slate-400 font-black text-xl border-4 border-dashed border-white rounded-[4rem] bg-white/50">
        <div class="text-6xl mb-4">📜</div>
        لا توجد طلبات انضمام جديدة حالياً.
      </div>
    {:else}
      <div class="grid grid-cols-1 gap-6">
        {#each pendingRequests as req (req.user_id + '_' + req.session_id)}
          <div class="group bg-white p-8 rounded-[3.5rem] shadow-sm border border-slate-50 flex flex-col md:flex-row justify-between items-center transition-all hover:shadow-2xl hover:scale-[1.01]" in:scale={{duration: 300}}>
            
            <div class="flex items-center gap-6 text-right w-full">
              <div class="w-16 h-16 bg-[#eff3fa] rounded-[1.5rem] flex items-center justify-center text-2xl font-black text-[#6b8cce] shadow-inner group-hover:bg-[#2a3c54] group-hover:text-white transition-colors">
                {req.student_name.charAt(0)}
              </div>
              <div class="flex-1">
                <p class="font-black text-[#2a3c54] text-xl">{req.student_name}</p>
                <div class="flex flex-wrap gap-x-4 gap-y-1 mt-1">
                  <span class="text-sm font-bold text-slate-400">📖 {req.session_title}</span>
                  <span class="text-sm font-bold text-slate-300 italic">🗓️ {req.date}</span>
                </div>
              </div>
            </div>

            <div class="mt-6 md:mt-0 flex items-center min-w-[280px] justify-end">
              {#if req.processedMessage}
                <div in:scale class="px-8 py-3 rounded-2xl font-black text-sm {req.processedMessage.includes('✅') ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-600'} border border-current transition-all">
                  {req.processedMessage}
                </div>
              {:else}
                <div class="flex gap-4" in:fade>
                  <button 
                    onclick={() => handleAction(req, 'approved')} 
                    disabled={req.isProcessing}
                    class="px-8 py-4 bg-emerald-500 text-white rounded-[1.5rem] font-black text-xs hover:bg-emerald-600 transition-all shadow-lg shadow-emerald-500/30 active:scale-90 disabled:opacity-20"
                  >
                    موافقة ✅
                  </button>
                  <button 
                    onclick={() => handleAction(req, 'rejected')} 
                    disabled={req.isProcessing}
                    class="px-8 py-4 bg-white border-2 border-red-100 text-red-500 rounded-[1.5rem] font-black text-xs hover:bg-red-500 hover:text-white transition-all active:scale-90 disabled:opacity-20"
                  >
                    رفض ✖️
                  </button>
                </div>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </section>

  {#if !isLoading && historyRequests.length > 0}
    <section in:fade class="pt-8 border-t-2 border-dashed border-slate-200">
      <h2 class="text-2xl font-black text-slate-400 mb-6">سجل القرارات السابقة</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 opacity-80 hover:opacity-100 transition-opacity">
        {#each historyRequests as hReq (hReq.user_id + '_history_' + hReq.session_id)}
          <div class="bg-white/60 p-5 rounded-[2rem] border border-slate-100 flex justify-between items-center hover:bg-white transition-colors">
            
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center text-lg font-black text-slate-400 shadow-inner">
                {hReq.student_name.charAt(0)}
              </div>
              <div>
                <p class="font-black text-[#2a3c54] text-sm">{hReq.student_name}</p>
                <p class="text-xs font-bold text-slate-400 mt-0.5">{hReq.session_title}</p>
              </div>
            </div>

            <div>
              {#if hReq.status === 'approved'}
                <span class="px-4 py-2 bg-emerald-50 text-emerald-600 rounded-xl font-black text-[10px] border border-emerald-100">تم القبول ✅</span>
              {:else}
                <span class="px-4 py-2 bg-red-50 text-red-500 rounded-xl font-black text-[10px] border border-red-100">تم الرفض ✖️</span>
              {/if}
            </div>

          </div>
        {/each}
      </div>
    </section>
  {/if}

</div>