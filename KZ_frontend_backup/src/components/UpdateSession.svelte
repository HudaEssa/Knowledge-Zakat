<script lang="ts">
  import { onMount } from 'svelte';
  import { fade } from 'svelte/transition';
  import api from '../lib/api';
  import { route, navigate } from '../lib/router';
  import { notify } from '../lib/notifications';
  import { 
    Save, ArrowRight, Image as ImageIcon, Link, Clock, 
    Calendar, Type, AlignRight, Tag, Loader2, UploadCloud
  } from 'lucide-svelte';

  let isLoading = $state(true);
  let isSaving = $state(false);
  let isUploadingCover = $state(false); // حالة رفع الصورة
  let dbCategories = $state<any[]>([]);

  let sessionData = $state({
    title: '',
    description: '',
    category_id: null as number | null,
    cover_image_url: '',
    date_time: '',
    session_duration: 60,
    meeting_link: '',
  });

  let sessionId = $derived($route.param ? Number($route.param) : null);

  onMount(async () => {
    if (!sessionId) return navigate('my_lectures');

    try {
      const [catRes, sessRes] = await Promise.all([
        api.get<any[]>('/sessions/categories'), 
        api.get<any>(`/sessions/${sessionId}`),
      ]);
      
      dbCategories = catRes.data;
      const current = sessRes.data;

      sessionData = {
        title: current.title,
        description: current.description || '',
        category_id: current.category_id,
        cover_image_url: current.cover_image_url || '',
        date_time: current.date_time ? new Date(current.date_time).toISOString().slice(0, 16) : '',
        session_duration: current.session_duration,
        meeting_link: current.meeting_link || '',
      };
    } catch {
      notify.error('تعذّر تحميل البيانات');
    } finally {
      isLoading = false;
    }
  });

  // ---- وظيفة رفع الغلاف الجديد ----
  async function handleCoverUpload(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    // فحص الحجم والنوع (5 ميجابايت كحد أقصى)
    if (file.size > 5 * 1024 * 1024) {
      notify.error('حجم الصورة كبير جداً (الأقصى 5 ميجابايت)');
      return;
    }

    isUploadingCover = true;
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const res = await api.post<{ cover_url: string }>(
        '/sessions/upload-cover',
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      
      sessionData.cover_image_url = res.data.cover_url;
      notify.success('تم تحديث الغلاف بنجاح');
    } catch {
      notify.error('فشل رفع الصورة، حاول مرة أخرى');
    } finally {
      isUploadingCover = false;
      input.value = ''; // تصغير المدخل
    }
  }

  async function handleUpdate() {
    if (isSaving || !sessionId) return;
    isSaving = true;

    try {
      // نجهز الـ payload بشكل صريح لضمان عدم حدوث تضارب في البيانات
      const payload = {
        title: sessionData.title,
        description: sessionData.description,
        session_duration: Number(sessionData.session_duration),
        // 👈 نرسل التاريخ كـ String مباشرة من الحقل بدون تحويله لـ Date object
        // هذا يمنع السيرفر من إنقاص 3 ساعات (توقيت بغداد)
        date_time: sessionData.date_time, 
        meeting_link: sessionData.meeting_link,
        category_ids: [Number(sessionData.category_id)]
      };

      await api.put(`/sessions/${sessionId}`, payload);

      notify.success('تم حفظ جميع التعديلات بنجاح ✨');
      
      // تأخير بسيط للانتقال حتى يشوف المستخدم رسالة النجاح
      setTimeout(() => navigate('my_lectures'), 800);
      
    } catch (err) {
      notify.error('تعذّر حفظ التعديلات، يرجى التأكد من ملء الحقول المطلوبة');
      console.error("Update Error:", err);
    } finally {
      isSaving = false;
    }
  }
</script>

<div class="min-h-screen bg-slate-100/50 py-10 px-4 text-right" dir="rtl">
  <div class="max-w-4xl mx-auto">
    <header class="mb-10 flex justify-between items-center px-2">
      <div>
        <h1 class="text-3xl md:text-4xl font-black text-[#2a3c54]">تعديل المحاضرة</h1>
        <p class="text-slate-400 font-bold italic text-sm md:text-base">تغيير كافة التفاصيل، الصور، والروابط</p>
      </div>
      <button onclick={() => navigate('my_lectures')} class="flex items-center gap-2 text-slate-500 font-black hover:text-[#2a3c54] transition-all group">
         <ArrowRight size={20} class="group-hover:-translate-x-1 transition-transform" /> العودة
      </button>
    </header>

    {#if isLoading}
      <div class="bg-white rounded-[3rem] p-24 text-center shadow-xl flex flex-col items-center gap-4">
        <Loader2 size={50} class="animate-spin text-[#6b8cce]" />
        <p class="font-black text-slate-300">جاري جلب بياناتك من السيرفر...</p>
      </div>
    {:else}
      <div class="bg-white rounded-[3rem] shadow-kz-xl p-6 md:p-14 space-y-10 border border-white" in:fade>
        
        <div class="flex flex-col items-center gap-6 p-8 bg-slate-50 rounded-[2.5rem] border-2 border-dashed border-slate-200">
          <div class="relative group">
            <div class="w-64 md:w-80 h-36 md:h-44 rounded-3xl bg-white shadow-inner overflow-hidden flex items-center justify-center border border-slate-100">
              {#if sessionData.cover_image_url}
                <img 
                  src={`http://127.0.0.1:8000/pics/${sessionData.cover_image_url}`} 
                  class="w-full h-full object-cover" 
                  alt="Session Cover" 
                />
              {:else}
                <div class="flex flex-col items-center text-slate-300 gap-2">
                   <ImageIcon size={48} strokeWidth={1} />
                   <span class="text-xs font-bold">لا يوجد غلاف</span>
                </div>
              {/if}
            </div>
            
            {#if isUploadingCover}
              <div class="absolute inset-0 bg-white/60 backdrop-blur-sm flex items-center justify-center rounded-3xl">
                <Loader2 size={32} class="animate-spin text-[#2a3c54]" />
              </div>
            {/if}
          </div>

          <label class="px-8 py-3 bg-[#2a3c54] text-white rounded-2xl font-black text-sm cursor-pointer hover:bg-[#1a2a3a] transition-all flex items-center gap-2 shadow-lg active:scale-95">
             <UploadCloud size={18} />
             {sessionData.cover_image_url ? 'تغيير صورة الغلاف' : 'إضافة غلاف للمحاضرة'}
             <input type="file" class="hidden" onchange={handleCoverUpload} accept="image/*" disabled={isUploadingCover} />
          </label>
        </div>

        <div class="grid gap-8">
          <div class="space-y-3">
            <label class="flex items-center gap-2 font-black text-slate-400 text-xs pr-2"><Type size={16} /> عنوان المحاضرة</label>
            <input bind:value={sessionData.title} class="w-full p-5 bg-slate-50 rounded-2xl border-2 border-slate-100 focus:border-[#6b8cce] outline-none font-black shadow-inner transition-all" />
          </div>

          <div class="space-y-3">
            <label class="flex items-center gap-2 font-black text-slate-400 text-xs pr-2"><AlignRight size={16} /> الوصف</label>
            <textarea bind:value={sessionData.description} class="w-full p-5 bg-slate-50 rounded-2xl border-2 border-slate-100 focus:border-[#6b8cce] outline-none font-bold h-40 shadow-inner resize-none transition-all"></textarea>
          </div>

          <div class="grid md:grid-cols-2 gap-8">
            <div class="space-y-3">
              <label class="flex items-center gap-2 font-black text-slate-400 text-xs pr-2"><Calendar size={16} /> التاريخ والوقت</label>
              <input type="datetime-local" bind:value={sessionData.date_time} class="w-full p-5 bg-slate-50 rounded-2xl border-2 border-slate-100 focus:border-[#6b8cce] outline-none font-black shadow-inner transition-all" />
            </div>
            <div class="space-y-3">
              <label class="flex items-center gap-2 font-black text-slate-400 text-xs pr-2"><Clock size={16} /> مدة الجلسة (دقيقة)</label>
              <input type="number" bind:value={sessionData.session_duration} class="w-full p-5 bg-slate-50 rounded-2xl border-2 border-slate-100 focus:border-[#6b8cce] outline-none font-black shadow-inner transition-all" />
            </div>
          </div>

          <div class="space-y-3">
            <label class="flex items-center gap-2 font-black text-slate-400 text-xs pr-2"><Link size={16} /> رابط الاجتماع المباشر (اختياري)</label>
            <input bind:value={sessionData.meeting_link} dir="ltr" placeholder="https://meet.google.com/..." class="w-full p-5 bg-slate-50 rounded-2xl border-2 border-slate-100 focus:border-[#6b8cce] outline-none font-black text-left shadow-inner transition-all" />
          </div>
        </div>

        <button 
          onclick={handleUpdate} 
          disabled={isSaving || isUploadingCover} 
          class="w-full py-6 bg-[#2a3c54] text-white rounded-[2.5rem] font-black text-xl shadow-2xl hover:bg-[#1a2a3a] transition-all flex items-center justify-center gap-3 active:scale-[0.98] disabled:opacity-50"
        >
          {#if isSaving}
            <Loader2 size={24} class="animate-spin" /> جاري حفظ التعديلات...
          {:else}
           تعديل<Save size={24} />
          {/if}
        </button>
      </div>
    {/if}
  </div>
</div>

<style>
  /* تنسيق خاص للظلال */
  :global(.shadow-kz-xl) {
    box-shadow: 0 25px 50px -12px rgba(42, 60, 84, 0.1);
  }
</style>