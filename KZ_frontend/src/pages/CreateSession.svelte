<script>
  import { onMount } from "svelte";
  import api from "../lib/api"; // التأكد من وجود ملف الـ api اللي يستعمل axios أو fetch
  import { currentPage } from "../lib/stores";
  import { fade, slide, scale } from "svelte/transition";

  // --- حالات الصفحة (Svelte 5) ---
  let currentStep = $state(1);
  let isLoading = $state(false);
  let dbCategories = $state([]);
  
  // بيانات المادة (الكورس)
  let course = $state({
    title: "",
    description: "",
    category_id: null,
    cover_image_url: ""
  });

  // قائمة الأيام (الجلسات)
  let sessionsList = $state([
    { title: "الجلسة الأولى", date_time: "", session_duration: 60, meeting_link: "" }
  ]);

  // مودال الحالة
  let showStatusModal = $state(false);
  let modalType = $state("success");
  let modalMessage = $state("");

  const minDateTime = new Date().toISOString().slice(0, 16);

  onMount(async () => {
    try {
      const res = await api.get('/categories/');
      dbCategories = res.data;
      if (dbCategories.length > 0) course.category_id = dbCategories[0].id;
    } catch (e) { 
      console.error("فشل جلب الأقسام"); 
    }
  });

  // رفع الغلاف (يربط الصورة ببروفايل المستخدم حالياً حسب الباكيند مالتك)
  async function handleCoverUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      isLoading = true;
      // نستخدم الإندبوينت الجديد الخاص بغلاف المحاضرات
      const res = await api.post("/sessions/upload-cover", formData);
      
      // نخزن اسم الملف الراجع من الباكيند
      course.cover_image_url = res.data.cover_url; 
      
      modalType = "success";
      modalMessage = "تم رفع الغلاف بنجاح!";
      showStatusModal = true;
    } catch (err) {
      modalType = "error";
      modalMessage = "فشل رفع الصورة.";
      showStatusModal = true;
    } finally {
      isLoading = false;
    }
  }

  function addSessionDay() {
    sessionsList = [...sessionsList, { 
      title: `الجلسة رقم ${sessionsList.length + 1}`, 
      date_time: "", 
      session_duration: 60, 
      meeting_link: "" 
    }];
  }

  function removeSessionDay(index) {
    if (sessionsList.length > 1) {
      sessionsList = sessionsList.filter((_, i) => i !== index);
    }
  }

  async function handleFinalSubmit() {
    if (!course.title || !course.description || !course.category_id) {
      modalType = "error";
      modalMessage = "يرجى ملء كافة معلومات المادة الأساسية.";
      showStatusModal = true; 
      return;
    }

    isLoading = true;
    try {
      // إرسال كل جلسة كطلب منفصل للباكيند
      for (let s of sessionsList) {
        const finalPayload = {
          title: `${course.title} - ${s.title}`,
          description: course.description,
          session_duration: s.session_duration,
          date_time: s.date_time,
          meeting_link: s.meeting_link,
          cover_image_url: course.cover_image_url, // ربط الصورة المرفوعة بالجلسة
          category_ids: [course.category_id] // إرسال القسم كقائمة 
        };
        await api.post('/sessions/', finalPayload);
      }

      modalType = "success";
      modalMessage = "تم إنشاء الدورة وجدولتها بنجاح!";
      showStatusModal = true;
      setTimeout(() => { 
        showStatusModal = false; 
        currentPage.set('my_lectures'); 
      }, 2000);

    } catch (e) {
      modalType = "error";
      modalMessage = e.response?.data?.detail || "حدث خطأ أثناء الحفظ.";
      showStatusModal = true;
    } finally {
      isLoading = false;
    }
  }
</script>

{#if showStatusModal}
<div in:fade out:fade class="fixed inset-0 z-[5000] flex items-center justify-center p-4 bg-[#2a3c54]/40 backdrop-blur-md">
  <div in:scale={{ duration: 300, start: 0.9 }} class="bg-white rounded-[2.5rem] shadow-2xl p-10 max-w-sm w-full text-center space-y-6">
    <div class="w-20 h-20 rounded-full flex items-center justify-center mx-auto text-4xl font-black {modalType === 'success' ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-500'}">
      {modalType === 'success' ? '✓' : '!'}
    </div>
    <div>
      <h3 class="text-2xl font-black text-[#2a3c54]">{modalType === 'success' ? 'تمت العملية' : 'تنبيه'}</h3>
      <p class="text-sm font-bold text-slate-400 mt-2">{modalMessage}</p>
    </div>
    <button onclick={() => showStatusModal = false} class="w-full py-4 bg-[#2a3c54] text-white rounded-2xl font-black shadow-lg">فهمت</button>
  </div>
</div>
{/if}

<div class="max-w-4xl mx-auto pb-20 text-right" dir="rtl">
  <header class="mb-10">
    <h1 class="text-4xl font-black text-[#2a3c54]">بناء دورة علمية</h1>
    <p class="text-slate-400 font-bold mt-2 italic">نظّم جلساتك التعليمية بخطوات بسيطة.</p>
  </header>

  <div class="bg-white rounded-[3rem] shadow-xl border border-slate-50 p-8 md:p-12">
    <div class="flex items-center gap-4 mb-12">
      <div class="flex-1 h-2 rounded-full {currentStep >= 1 ? 'bg-[#6b8cce]' : 'bg-slate-100'} transition-all"></div>
      <div class="flex-1 h-2 rounded-full {currentStep >= 2 ? 'bg-[#6b8cce]' : 'bg-slate-100'} transition-all"></div>
    </div>

    {#if currentStep === 1}
      <div class="space-y-8" in:fade>
        <div class="flex flex-col items-center gap-4 p-8 bg-slate-50 rounded-[2.5rem] border-2 border-dashed border-slate-200">
          <div class="w-40 h-24 rounded-2xl bg-white shadow-inner overflow-hidden flex items-center justify-center">
  {#if course.cover_image_url}
    <img src="http://localhost:8000/pics/{course.cover_image_url}" class="..." alt="Cover" />
  {:else}
    <span class="text-3xl opacity-20">🖼️</span>
  {/if}
</div>
          <label class="px-6 py-2 bg-[#2a3c54] text-white rounded-xl font-black text-xs cursor-pointer hover:bg-opacity-90 transition-all">
            {isLoading ? 'جاري الرفع...' : 'إضافة غلاف المادة'}
            <input type="file" class="hidden" onchange={handleCoverUpload} accept="image/*" disabled={isLoading} />
          </label>
        </div>

        <div class="grid gap-6">
          <div class="space-y-2">
            <label class="block font-black text-[#2a3c54]/60 text-xs pr-2">اسم المادة الأساسي</label>
            <input bind:value={course.title} class="w-full p-5 bg-slate-50 rounded-2xl border-2 border-slate-100 focus:border-[#6b8cce] outline-none font-bold" placeholder="مثال: دورة تطوير الويب">
          </div>

          <div class="space-y-2">
            <label class="block font-black text-[#2a3c54]/60 text-xs pr-2">وصف الدورة</label>
            <textarea bind:value={course.description} class="w-full p-5 bg-slate-50 rounded-2xl border-2 border-slate-100 focus:border-[#6b8cce] outline-none font-bold h-32 resize-none" placeholder="نبذة مختصرة عن الدورة..."></textarea>
          </div>

          <div class="space-y-2">
            <label class="block font-black text-[#2a3c54]/60 text-xs pr-2">القسم العلمي</label>
            <select bind:value={course.category_id} class="w-full p-5 bg-slate-50 rounded-2xl border-2 border-slate-100 outline-none font-bold appearance-none">
              {#each dbCategories as cat}
                <option value={cat.id}>{cat.category_name}</option>
              {/each}
            </select>
          </div>
        </div>

        <button onclick={() => currentStep = 2} class="w-full py-5 bg-[#2a3c54] text-white rounded-2xl font-black text-lg shadow-lg hover:scale-[1.01] active:scale-95 transition-all">الخطوة التالية: جدولة المحاضرات</button>
      </div>

    {:else}
      <div class="space-y-8" in:fade>
        <div class="flex items-center justify-between border-b pb-6">
          <h2 class="text-2xl font-black text-[#2a3c54]">أيام الجلسات</h2>
          <button onclick={addSessionDay} class="bg-[#2a3c54] text-white px-5 py-2 rounded-xl font-black text-sm hover:bg-[#6b8cce] transition-colors">+ إضافة يوم</button>
        </div>

        <div class="space-y-6 max-h-[50vh] overflow-y-auto pr-2 custom-scrollbar">
          {#each sessionsList as session, i}
            <div class="p-6 bg-slate-50 rounded-[2rem] border border-slate-200 relative" transition:slide>
              <button onclick={() => removeSessionDay(i)} class="absolute top-4 left-4 text-red-400 hover:text-red-600 font-bold">حذف ✕</button>
              <p class="font-black text-sm text-[#6b8cce] mb-4">اليوم {i + 1}</p>
              
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="md:col-span-2">
                  <input bind:value={session.title} class="w-full p-4 rounded-xl border-2 border-white focus:border-[#6b8cce] outline-none font-bold" placeholder="عنوان الجلسة (مثال: تنصيب البيئة)">
                </div>
                <div>
                  <label class="block text-[10px] font-black text-slate-400 mr-2 mb-1">التاريخ والوقت</label>
                  <input type="datetime-local" bind:value={session.date_time} min={minDateTime} class="w-full p-4 rounded-xl border-2 border-white outline-none font-bold">
                </div>
                <div>
                  <label class="block text-[10px] font-black text-slate-400 mr-2 mb-1">المدة (دقيقة)</label>
                  <input type="number" bind:value={session.session_duration} class="w-full p-4 rounded-xl border-2 border-white outline-none font-bold">
                </div>
                <div class="md:col-span-2">
                  <input bind:value={session.meeting_link} dir="ltr" class="w-full p-4 rounded-xl border-2 border-white focus:border-[#6b8cce] outline-none font-bold text-left" placeholder="https://meet.google.com/...">
                </div>
              </div>
            </div>
          {/each}
        </div>

        <div class="grid grid-cols-2 gap-4">
          <button onclick={() => currentStep = 1} class="py-5 bg-slate-100 text-slate-500 rounded-2xl font-black">رجوع</button>
          <button onclick={handleFinalSubmit} disabled={isLoading} class="py-5 bg-[#2a3c54] text-white rounded-2xl font-black shadow-xl disabled:opacity-50">
            {isLoading ? 'جاري الحفظ...' : 'نشر الدورة العلمية ✅'}
          </button>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar { width: 5px; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
</style>