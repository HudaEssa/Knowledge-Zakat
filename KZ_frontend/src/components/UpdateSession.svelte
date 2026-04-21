<script>
  import { onMount } from "svelte";
  import api from "../lib/api";
  import { currentPage } from "../lib/stores";
  import { fade, scale } from "svelte/transition";

  // استلام معرف الجلسة من المتجر
  let { sessionId } = $currentPage.data; 

  let isLoading = $state(true);
  let isSaving = $state(false);
  let dbCategories = $state([]);
  
  // بيانات الجلسة (تستخدم Svelte 5 Runes)
  let sessionData = $state({
    title: "",
    description: "",
    category_id: null,
    cover_image_url: "",
    date_time: "",
    session_duration: 60,
    meeting_link: ""
  });

  // حالات واجهة المستخدم
  let showStatusModal = $state(false);
  let modalMessage = $state("");
  let modalType = $state("success");

  const minDateTime = new Date().toISOString().slice(0, 16);

  onMount(async () => {
    try {
      // 1. جلب قائمة الأقسام العلمية
      const catRes = await api.get('/categories/');
      dbCategories = catRes.data;

      // 2. جلب بيانات الجلسة الحالية
      const res = await api.get('/sessions/');
      const currentSession = res.data.find(s => s.id === sessionId);
      
      if (currentSession) {
        sessionData = {
          title: currentSession.title,
          description: currentSession.description,
          // استخراج أول معرف قسم من القائمة
          category_id: currentSession.categories?.[0]?.id || null,
          cover_image_url: currentSession.cover_image_url || "",
          // تنسيق التاريخ ليتناسب مع حقل datetime-local
          date_time: currentSession.date_time ? new Date(currentSession.date_time).toISOString().slice(0, 16) : "",
          session_duration: currentSession.session_duration,
          meeting_link: currentSession.meeting_link
        };
      }
    } catch (e) {
      displayMessage("فشل في استرداد بيانات المحاضرة من الخادم", "error");
    } finally {
      isLoading = false;
    }
  });

  // معالجة رفع غلاف جديد للمحاضرة
  async function handleCoverUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);

    try {
      isSaving = true;
      const res = await api.post("/sessions/upload-cover", formData);
      // نخزن اسم الملف الفريد الراجع من الباكيند
      sessionData.cover_image_url = res.data.cover_url;
      displayMessage("تم رفع الغلاف الجديد بنجاح", "success");
    } catch (err) {
      displayMessage("فشل في رفع الصورة، يرجى التحقق من حجم الملف", "error");
    } finally {
      isSaving = false;
    }
  }

  // إرسال التحديثات النهائية للباكيند
  async function handleUpdate() {
    if (!sessionData.category_id) {
      displayMessage("يرجى اختيار القسم العلمي للمحاضرة", "error");
      return;
    }

    isSaving = true;
    try {
      // بناء هيكل البيانات المطلوب (Payload) بدقة
      const payload = {
        title: sessionData.title,
        description: sessionData.description,
        session_duration: Number(sessionData.session_duration),
        date_time: sessionData.date_time,
        meeting_link: sessionData.meeting_link,
        category_ids: [Number(sessionData.category_id)], // إرسال مصفوفة أرقام
        cover_image_url: sessionData.cover_image_url
      };

      await api.put(`/sessions/${sessionId}`, payload);
      displayMessage("تم تحديث بيانات المحاضرة بنجاح", "success");
      
      // العودة لصفحة الإدارة بعد نجاح التعديل
      setTimeout(() => currentPage.set({ name: 'my_lectures', data: {} }), 2000);
    } catch (e) {
      // استخراج رسالة الخطأ بدقة لتجنب عرض [object Object]
      const errorMsg = e.response?.data?.detail || "حدث خطأ غير متوقع أثناء الحفظ";
      displayMessage(errorMsg, "error");
    } finally {
      isSaving = false;
    }
  }

  function displayMessage(msg, type) {
    modalMessage = msg;
    modalType = type;
    showStatusModal = true;
    if (type === "success") {
      setTimeout(() => { showStatusModal = false; }, 2500);
    }
  }
</script>

{#if showStatusModal}
<div in:fade out:fade class="fixed inset-0 z-[8000] flex items-center justify-center p-4 bg-[#2a3c54]/40 backdrop-blur-md">
  <div in:scale class="bg-white rounded-[2.5rem] shadow-2xl p-10 max-w-sm w-full text-center space-y-6 border border-white">
    <div class="w-20 h-20 rounded-full flex items-center justify-center mx-auto text-4xl {modalType === 'success' ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-500'}">
      {modalType === 'success' ? '✓' : '!'}
    </div>
    <div class="space-y-2">
      <h3 class="text-2xl font-black text-[#2a3c54]">{modalType === 'success' ? 'تمت العملية' : 'تنبيه'}</h3>
      <p class="text-sm font-bold text-slate-400 leading-relaxed italic">{modalMessage}</p>
    </div>
    <button onclick={() => showStatusModal = false} class="w-full py-4 bg-[#2a3c54] text-white rounded-2xl font-black shadow-lg hover:bg-opacity-90 transition-all">فهمت</button>
  </div>
</div>
{/if}

<div class="max-w-4xl mx-auto pb-20 text-right" dir="rtl">
  <header class="mb-12 flex justify-between items-end">
    <div>
      <h1 class="text-4xl font-black text-[#2a3c54]">تحديث المحاضرة</h1>
      <p class="text-slate-400 font-bold mt-2 italic">أنت الآن تقوم بتعديل بيانات الدورة العلمية.</p>
    </div>
    <button onclick={() => currentPage.set({ name: 'my_lectures', data: {} })} class="text-slate-400 font-black hover:text-[#2a3c54] transition-all underline decoration-dotted">العودة للإدارة</button>
  </header>

  {#if isLoading}
    <div class="bg-white rounded-[3rem] p-20 text-center shadow-xl border border-slate-50">
       <div class="w-12 h-12 border-4 border-[#6b8cce] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
       <p class="font-black text-[#2a3c54]">جاري تحضير البيانات الأكاديمية...</p>
    </div>
  {:else}
    <div class="bg-white rounded-[3.5rem] shadow-xl border border-slate-50 p-10 md:p-16 space-y-12">
      
      <div class="flex flex-col items-center gap-6 p-8 bg-slate-50 rounded-[2.5rem] border-2 border-dashed border-slate-200">
        <div class="w-64 h-36 rounded-2xl bg-white shadow-inner overflow-hidden flex items-center justify-center border border-slate-100">
          {#if sessionData.cover_image_url}
            <img 
              src={sessionData.cover_image_url.startsWith('data:') 
                   ? sessionData.cover_image_url 
                   : `http://localhost:8000/pics/${sessionData.cover_image_url}`} 
              class="w-full h-full object-cover" 
              alt="Cover Preview" 
            />
          {:else}
            <span class="text-4xl opacity-20">🖼️</span>
          {/if}
        </div>
        <label class="px-8 py-3 bg-white text-[#2a3c54] rounded-xl font-black text-xs shadow-sm cursor-pointer hover:bg-[#2a3c54] hover:text-white transition-all border border-slate-100">
          تغيير غلاف المحاضرة
          <input type="file" class="hidden" onchange={handleCoverUpload} accept="image/*" />
        </label>
      </div>

      <div class="grid grid-cols-1 gap-10">
        <div class="space-y-3">
          <label class="block font-black text-[#2a3c54]/60 text-xs uppercase tracking-widest pr-2">عنوان المادة العلمية</label>
          <input bind:value={sessionData.title} class="w-full p-6 bg-slate-50 rounded-[2rem] border-2 border-slate-100 focus:border-[#6b8cce] font-black text-lg outline-none transition-all shadow-sm">
        </div>
        
        <div class="space-y-3">
          <label class="block font-black text-[#2a3c54]/60 text-xs uppercase tracking-widest pr-2">الوصف التفصيلي للمحاضرة</label>
          <textarea bind:value={sessionData.description} class="w-full p-6 bg-slate-50 rounded-[2.5rem] border-2 border-slate-100 focus:border-[#6b8cce] font-bold text-lg h-48 outline-none resize-none transition-all shadow-sm"></textarea>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div class="space-y-3">
            <label class="block font-black text-[#2a3c54]/60 text-xs pr-2">تاريخ ووقت الانعقاد</label>
            <input type="datetime-local" bind:value={sessionData.date_time} min={minDateTime} class="w-full p-6 bg-slate-50 rounded-[2rem] border-2 border-slate-100 font-black text-lg outline-none shadow-sm">
          </div>
          <div class="space-y-3">
            <label class="block font-black text-[#2a3c54]/60 text-xs pr-2">المدة (بالدقائق)</label>
            <input type="number" bind:value={sessionData.session_duration} class="w-full p-6 bg-slate-50 rounded-[2rem] border-2 border-slate-100 font-black text-lg outline-none shadow-sm">
          </div>
        </div>

        <div class="space-y-3">
          <label class="block font-black text-[#2a3c54]/60 text-xs uppercase tracking-widest pr-2">رابط القاعة الافتراضية</label>
          <input bind:value={sessionData.meeting_link} dir="ltr" class="w-full p-6 bg-slate-50 rounded-[2rem] border-2 border-slate-100 font-black text-lg outline-none text-left shadow-sm placeholder:text-slate-300" placeholder="https://meet.google.com/...">
        </div>

        <div class="space-y-3">
          <label class="block font-black text-[#2a3c54]/60 text-xs uppercase pr-2">التصنيف أو القسم العلمي</label>
          <select bind:value={sessionData.category_id} class="w-full p-6 bg-slate-50 rounded-[2rem] border-2 border-slate-100 font-black text-lg outline-none cursor-pointer shadow-sm appearance-none">
            <option value={null} disabled>اختر قسماً...</option>
            {#each dbCategories as cat}
              <option value={cat.id}>{cat.category_name}</option>
            {/each}
          </select>
        </div>
      </div>

      <div class="pt-6">
        <button 
          onclick={handleUpdate} 
          disabled={isSaving}
          class="w-full py-7 bg-[#2a3c54] text-white rounded-[2.5rem] font-black text-xl shadow-2xl hover:scale-[1.02] disabled:opacity-50 transition-all shadow-[#2a3c54]/30">
          {#if isSaving}
            جاري حفظ التغييرات...
          {:else}
            اعتماد التحديثات ونشرها ✅
          {/if}
        </button>
      </div>
    </div>
  {/if}
</div>

<style>
  /* تحسينات بصرية إضافية */
  input:focus, textarea:focus, select:focus {
    box-shadow: 0 10px 15px -3px rgba(107, 140, 206, 0.1);
  }
</style>