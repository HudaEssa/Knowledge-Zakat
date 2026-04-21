<script>
  import { onMount } from "svelte";
  import api from "../lib/api";
  import { currentPage } from "../lib/stores";
  import { fade, slide, scale } from "svelte/transition";

  let myLectures = $state([]);
  let approvedStudents = $state([]); // لتخزين بيانات الطلاب لكل الجلسات
  let isLoading = $state(true);
  
  // مودال الحذف والحالة
  let showConfirmModal = $state(false);
  let showStatusModal = $state(false);
  let selectedSession = $state(null);
  let modalMessage = $state("");
  let modalType = $state("info");

  // مودال عرض الطلاب المشتركين
  let showStudentsModal = $state(false);
  let selectedSessionStudents = $state([]);
  let selectedSessionTitle = $state("");

  onMount(loadData);

  async function loadData() {
    try {
      // جلب المحاضرات والطلاب المقبولين بنفس الوقت
      const [lecturesRes, studentsRes] = await Promise.all([
        api.get("/me/sessions/"),
        api.get("/teacher/enrollments/approved")
      ]);
      myLectures = lecturesRes.data;
      approvedStudents = studentsRes.data;
    } catch (e) {
      displayStatus("فشل في تحميل البيانات", "error");
    } finally {
      isLoading = false;
    }
  }

  // دالة لفلترة وفتح قائمة الطلاب لجلسة معينة
  function openStudentsList(sessionId, title) {
    selectedSessionStudents = approvedStudents
      .filter(s => s.session_id === sessionId)
      .map(s => s.student);
    selectedSessionTitle = title;
    showStudentsModal = true;
  }

  function openDeleteConfirmation(session) {
    if (session.enrollments_count > 0) {
      displayStatus("لا يمكن حذف محاضرة بها طلاب مشتركين", "error");
      return;
    }
    selectedSession = session;
    showConfirmModal = true;
  }

  async function proceedWithDeletion() {
    showConfirmModal = false;
    try {
      await api.delete(`/sessions/${selectedSession.id}`);
      myLectures = myLectures.filter(l => l.id !== selectedSession.id);
      displayStatus("تم الحذف بنجاح", "success");
    } catch (e) {
      displayStatus("فشل الحذف", "error");
    }
  }

  function displayStatus(message, type) {
    modalMessage = message; modalType = type; showStatusModal = true;
    if (type === "success") setTimeout(() => showStatusModal = false, 2000);
  }

  function navigateToUpdate(lecture) {
    currentPage.set({ name: 'update_session', data: { sessionId: lecture.id } });
  }

  function navigateToDetails(lectureId) {
    currentPage.set({ name: 'session_details', data: { sessionId: lectureId } });
  }
</script>

{#if showStudentsModal}
<div in:fade out:fade class="fixed inset-0 z-[8000] flex items-center justify-center p-4 bg-[#2a3c54]/60 backdrop-blur-sm" dir="rtl">
  <div in:scale class="bg-white rounded-[2.5rem] p-8 max-w-md w-full shadow-2xl flex flex-col max-h-[80vh]">
    <div class="flex justify-between items-center mb-6 border-b pb-4">
        <h3 class="text-xl font-black text-[#2a3c54]">الطلاب في: {selectedSessionTitle}</h3>
        <button onclick={() => showStudentsModal = false} class="text-slate-400 hover:text-red-500 text-2xl">&times;</button>
    </div>
    
    <div class="overflow-y-auto space-y-4 pr-2 custom-scrollbar">
      {#if selectedSessionStudents.length === 0}
        <p class="text-center py-10 text-slate-400 font-bold">لا يوجد طلاب مقبولين في هذه الجلسة بعد.</p>
      {:else}
        {#each selectedSessionStudents as student}
          <div class="flex items-center gap-4 bg-slate-50 p-4 rounded-2xl border border-slate-100">
            <div class="w-12 h-12 rounded-xl bg-[#6b8cce] text-white flex items-center justify-center font-black overflow-hidden shadow-sm">
                {#if student.image}
                    <img src={`data:image/jpeg;base64,${student.image}`} alt="profile" class="w-full h-full object-cover" />
                {:else}
                    {student.name.charAt(0)}
                {/if}
            </div>
            <div>
              <h4 class="font-black text-[#2a3c54] text-sm">{student.name}</h4>
              <p class="text-[10px] text-slate-500 line-clamp-1">{student.email}</p>
            </div>
          </div>
        {/each}
      {/if}
    </div>
    <button onclick={() => showStudentsModal = false} class="mt-6 w-full py-3 bg-[#2a3c54] text-white rounded-xl font-black">إغلاق</button>
  </div>
</div>
{/if}

{#if showConfirmModal}
<div in:fade class="fixed inset-0 z-[6000] flex items-center justify-center p-4 bg-[#2a3c54]/40 backdrop-blur-sm">
  <div in:scale class="bg-white rounded-[2.5rem] p-10 max-w-md w-full text-center shadow-2xl">
    <div class="w-20 h-20 bg-red-50 text-red-500 rounded-full flex items-center justify-center mx-auto text-3xl mb-6">🗑️</div>
    <h3 class="text-2xl font-black text-[#2a3c54] mb-2">تأكيد الحذف</h3>
    <p class="text-slate-500 font-bold mb-8">هل أنت متأكد من حذف "{selectedSession?.title}"؟</p>
    <div class="flex gap-4">
      <button onclick={proceedWithDeletion} class="flex-1 py-4 bg-red-500 text-white rounded-2xl font-black shadow-lg">حذف</button>
      <button onclick={() => showConfirmModal = false} class="flex-1 py-4 bg-slate-100 text-slate-500 rounded-2xl font-black">إلغاء</button>
    </div>
  </div>
</div>
{/if}

<div class="max-w-6xl mx-auto pb-20 text-right" dir="rtl">
  <header class="mb-12">
    <h1 class="text-4xl font-black text-[#2a3c54]">إدارة محاضراتي العلمية</h1>
    <p class="text-slate-400 font-bold mt-2 italic text-lg">تحكم في محتواك الأكاديمي وتابع طلابك من مكان واحد.</p>
  </header>

  {#if isLoading}
    <div class="text-center py-20 font-black text-[#6b8cce] animate-pulse text-xl">جاري جلب بياناتك...</div>
  {:else if myLectures.length === 0}
    <div class="bg-white rounded-[3rem] p-20 text-center border-2 border-dashed border-slate-200">
      <div class="text-6xl mb-6">📚</div>
      <h2 class="text-2xl font-black text-slate-400 mb-6">لم تقم بنشر أي محاضرة حتى الآن</h2>
      <button onclick={() => currentPage.set('create_session')} class="px-10 py-4 bg-[#2a3c54] text-white rounded-2xl font-black shadow-xl hover:scale-105 transition-all">ابدأ الآن</button>
    </div>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
      {#each myLectures as lecture (lecture.id)}
        <div in:fade class="bg-white rounded-[3rem] shadow-md hover:shadow-2xl transition-all border border-slate-100 overflow-hidden group flex flex-col">
          
          <div class="h-52 bg-slate-100 relative overflow-hidden">
            <img src="http://localhost:8000/pics/{lecture.cover}" alt="cover" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" />
            <button 
                onclick={() => openStudentsList(lecture.id, lecture.title)}
                class="absolute top-4 right-4 bg-white/95 backdrop-blur px-5 py-2 rounded-2xl text-xs font-black text-[#2a3c54] shadow-sm hover:bg-[#6b8cce] hover:text-white transition-all cursor-pointer">
                👤 {lecture.enrollments_count} طالب مشترك
            </button>
          </div>

          <div class="p-8 flex-1 flex flex-col">
            <h3 class="text-xl font-black text-[#2a3c54] mb-3 line-clamp-1">{lecture.title}</h3>
            <p class="text-slate-400 text-sm font-bold leading-relaxed mb-6 line-clamp-2 italic flex-1">{lecture.description}</p>
            
            <div class="space-y-3">
              <button 
                onclick={() => navigateToDetails(lecture.id)}
                class="w-full py-4 bg-[#6b8cce] text-white rounded-[1.25rem] font-black text-sm hover:bg-[#4a6583] transition-all shadow-md flex justify-center items-center gap-2">
                 عرض التفاصيل 
              </button>
              
              <div class="flex gap-2">
                <button 
                  onclick={() => navigateToUpdate(lecture)}
                  class="flex-1 py-3.5 bg-[#eff3fa] text-[#2a3c54] rounded-[1.25rem] font-black text-xs hover:bg-[#2a3c54] hover:text-white transition-all shadow-inner">
                  تعديل
                </button>
                <button 
                  onclick={() => openDeleteConfirmation(lecture)}
                  class="px-5 py-3.5 bg-red-50 text-red-500 rounded-[1.25rem] font-black text-xs hover:bg-red-500 hover:text-white transition-all">
                  حذف
                </button>
              </div>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar { width: 5px; }
  .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
</style>