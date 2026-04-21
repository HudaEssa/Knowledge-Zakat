<script>
  import api from "../lib/api";
  import { currentPage, selectedSessionId, user } from "../lib/stores";
  import { onMount } from "svelte";
  import { fade, scale } from "svelte/transition";

  let courseTitle = $selectedSessionId; 
  let courseDetails = $state(null);
  let sessions = $state([]); 
  let isSubmitting = $state(false);

  let showStatusModal = $state(false);
  let modalType = $state("success"); 
  let modalMessage = $state("");

  function getArabicDay(dateStr) {
    if (!dateStr) return "غير محدد";
    const date = new Date(dateStr);
    const days = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"];
    return days[date.getDay()];
  }

  // داخل دالة onMount بملف SessionView.svelte
onMount(async () => {
  try {
    const res = await api.get(`/sessions/`);
    // فلترة الجلسات بناءً على عنوان المادة المختار
    const relatedSessions = res.data.filter(s => s.title.startsWith(courseTitle));
    
    if (relatedSessions.length > 0) {
      const firstSess = relatedSessions[0];
      
      courseDetails = {
        title: courseTitle,
        // جلب الوصف الفعلي من الباكيند
        description: firstSess.description || "لا يوجد وصف متاح لهذه المحاضرة.",
        // ربط الاسم المدموج القادم من الباكيند 
        teacher: firstSess.teacher_name ? `المدرس/ة : ${firstSess.teacher_name}` : "المدرس/ة : قيد التحديث", 
        category: relatedSessions[0].categories?.map(c => c.category_name).join('، ') || "عام"
      };
      
      sessions = relatedSessions.map(s => {
        let dayTitle = s.title.includes(' - ') ? s.title.split(' - ')[1].trim() : s.title;
        return { ...s, day_title: dayTitle, selected: false };
      });
    }
  } catch (e) { 
    console.error("خطأ في جلب البيانات"); 
  }
});

  async function sendEnrollmentRequests() {
    const selectedSessions = sessions.filter(s => s.selected);
    if (selectedSessions.length === 0) {
      modalType = "info";
      modalMessage = "يرجى تحديد يوم واحد على الأقل للانضمام للمحاضرة.";
      showStatusModal = true;
      return;
    }

    isSubmitting = true;
    try {
      const token = localStorage.getItem("token");
      for (let s of selectedSessions) {
        await api.post('/enrollments/', {
          user_id: $user.id,
          session_id: s.id,
          status: 'pending'
        }, { headers: { Authorization: `Bearer ${token}` } });
      }
      modalType = "success";
      modalMessage = "تم إرسال طلباتك للأستاذ بنجاح! بانتظار الموافقة.";
      showStatusModal = true;
    } catch (err) {
      if (err.response && err.response.status === 400) {
        modalType = "info";
        modalMessage = "لقد قمت بإرسال طلب انضمام لهذه الجلسة مسبقاً! ⏳ بانتظار موافقة الأستاذ.";
      } else {
        modalType = "error";
        modalMessage = "حدث خطأ أثناء إرسال الطلبات.";
      }
      showStatusModal = true;
    } finally { isSubmitting = false; }
  }
</script>

{#if showStatusModal}
<div in:fade out:fade class="fixed inset-0 z-[5000] flex items-center justify-center p-4 bg-[#2a3c54]/40 backdrop-blur-md">
  <div in:scale={{ duration: 250, start: 0.85 }} class="bg-white rounded-[2.5rem] shadow-2xl p-10 max-w-sm w-full text-center space-y-6 border border-white">
    <div class="w-20 h-20 rounded-full flex items-center justify-center mx-auto text-4xl font-black
         {modalType === 'success' ? 'bg-green-50 text-green-600' : 'bg-[#eff3fa] text-[#2a3c54]'}">
      {modalType === 'success' ? '✓' : '!'}
    </div>
    <div class="space-y-2">
      <h3 class="text-2xl font-black text-[#2a3c54]">{modalType === 'success' ? 'تم الطلب' : 'تنبيه'}</h3>
      <p class="text-sm font-bold text-slate-400 leading-relaxed italic">{modalMessage}</p>
    </div>
    <button onclick={() => { showStatusModal = false; if (modalType === 'success') currentPage.set('my_learning'); }} 
      class="w-full py-4 bg-[#2a3c54] text-white rounded-2xl font-black text-lg hover:scale-105 transition-all shadow-lg active:scale-95">
      حسناً
    </button>
  </div>
</div>
{/if}

{#if courseDetails}
<div class="space-y-8 pb-20 text-right px-4 md:px-0" dir="rtl" in:fade>
  <button onclick={() => currentPage.set('home')} class="flex items-center gap-2 text-[#2a3c54] font-black opacity-50 hover:opacity-100 transition-all bg-white px-6 py-2 rounded-2xl shadow-sm w-fit mt-4">
    <span class="text-xl">→</span> العودة للمحاضرات
  </button>

  <header class="bg-white/90 backdrop-blur-2xl rounded-[3rem] p-10 md:p-12 shadow-2xl border border-white">
   
   
    <h1 class="text-3xl md:text-4xl font-black text-[#2a3c54] leading-tight">{courseDetails.title}</h1>
    <p class="text-slate-500 font-bold mt-4 leading-relaxed max-w-3xl text-sm md:text-base">{courseDetails.description}</p>
     <span class="bg-[#eff3fa] text-[#6b8cce] px-4 py-1.5 rounded-full font-black text-[px] uppercase tracking-widest mb-4 inline-block shadow-sm">
       التصنيف: {courseDetails.category}
    </span>
    <div class="mt-8 flex items-center gap-4 pt-6 border-t border-slate-100 w-fit">
        <div class="w-12 h-12 rounded-xl bg-slate-50 flex items-center justify-center text-xl shadow-inner">👤</div>
        <div>
            <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest">إشراف الأستاذ</p>
            <p class="font-black text-[#2a3c54]">{courseDetails.teacher}</p>
        </div>
    </div>
  </header>

  <div class="bg-white/90 backdrop-blur-2xl rounded-[3.5rem] shadow-2xl p-8 md:p-14 space-y-8">
    <div class="border-b pb-6 border-slate-50">
        <h2 class="text-xl font-black text-[#2a3c54]">الأيام والجلسات المتاحة:</h2>
        <p class="text-xs font-bold text-slate-400 mt-1">حدد أدناه الجلسات التي ترغب بحضورها ثم أرسل الطلب.</p>
    </div>

    <div class="space-y-4">
      {#each sessions as session}
        <label class="flex items-center justify-between p-6 rounded-3xl border-2 transition-all cursor-pointer 
          {session.selected ? 'border-[#6b8cce] bg-[#eff3fa]' : 'border-slate-50 bg-white hover:border-slate-100'}">
          <div class="flex items-center gap-6">
            <input type="checkbox" bind:checked={session.selected} class="w-6 h-6 rounded-lg accent-[#2a3c54]" />
            <div>
              <p class="font-black text-[#2a3c54] text-lg">{session.day_title}</p>
              <div class="flex flex-wrap gap-3 mt-2">
                  <span class="text-[11px] font-bold text-slate-500 bg-slate-50 px-3 py-1.5 rounded-xl">📅 {getArabicDay(session.date_time)} {session.date_time ? session.date_time.split('T')[0] : ''}</span>
                  <span class="text-[11px] font-bold text-slate-500 bg-slate-50 px-3 py-1.5 rounded-xl">⏰ {session.date_time ? session.date_time.split('T')[1].substring(0,5) : ''}</span>
                  <span class="text-[11px] font-bold text-slate-500 bg-slate-50 px-3 py-1.5 rounded-xl">⏱️ {session.session_duration} دقيقة</span>
              </div>
            </div>
          </div>
        </label>
      {/each}
    </div>

    <button onclick={sendEnrollmentRequests} disabled={isSubmitting} 
      class="w-full py-6 mt-6 bg-[#2a3c54] text-white rounded-[2.2rem] font-black text-lg shadow-xl hover:bg-[#1a2a3a] transition-all disabled:opacity-50 active:scale-95">
      {isSubmitting ? 'جاري إرسال الطلب...' : 'إرسال طلب الانضمام للأيام المحددة'}
    </button>
  </div>
</div>
{:else}
  <div class="flex flex-col items-center justify-center py-40 space-y-4">
      <div class="w-16 h-16 border-4 border-[#2a3c54] border-t-transparent rounded-full animate-spin"></div>
      <p class="text-[#2a3c54] font-black animate-pulse">جاري جلب تفاصيل الجلسة...</p>
  </div>
{/if}