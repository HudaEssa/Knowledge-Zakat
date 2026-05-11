<script>
  import { currentPage, user } from "../lib/stores";
  import { fade, fly } from "svelte/transition";
  import api from "../lib/api";

  let { lectureId } = $props(); 
  let lecture = $state({ title: "Programming", instructor: "أستاذ البرمجيات" });
  let sessions = $state([]); // يتم جلبها من الداتابيز

  // جلب الجلسات المتاحة لهذه المحاضرة
  async function fetchSessions() {
    const res = await api.get(`/lectures/${lectureId}/sessions`);
    sessions = res.data.map(s => ({ ...s, selected: false }));
  }

  async function sendRequests() {
    const selectedIds = sessions.filter(s => s.selected).map(s => s.id);
    if (selectedIds.length === 0) return alert("يرجى اختيار يوم واحد على الأقل");

    try {
      await api.post('/enrollments/request', { session_ids: selectedIds });
      alert("تم إرسال طلباتك بنجاح.. بانتظار موافقة الأستاذ");
      currentPage.set('home');
    } catch (err) {
      console.error("فشل الإرسال");
    }
  }
</script>

<div class="min-h-screen w-full bg-gradient-to-b from-slate-100 to-[#2a3c54] -m-10 p-10" dir="rtl">
  <button onclick={() => currentPage.set('home')} class="mb-8 flex items-center gap-2 text-[#2a3c54] font-black hover:gap-4 transition-all">
    <span class="text-2xl">→</span> العودة للمحاضرات
  </button>

  <div class="max-w-[1400px] mx-auto space-y-8">
    <header class="bg-white/90 backdrop-blur-xl rounded-[3rem] p-12 shadow-2xl border border-white">
      <h1 class="text-4xl font-black text-[#2a3c54]">{lecture.title}</h1>
      <p class="text-slate-400 font-bold mt-2 italic">مع الأستاذ المنسق لهذه المادة</p>
    </header>

    <div class="bg-white rounded-[4rem] shadow-2xl p-12 space-y-8">
      <h2 class="text-xl font-black text-[#2a3c54] border-b pb-4">اختر الأيام والمواضيع التي تود حضورها:</h2>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        {#each sessions as session}
          <label class="group relative flex items-center justify-between p-8 rounded-[2.5rem] border-2 transition-all cursor-pointer 
            {session.selected ? 'border-[#6b8cce] bg-[#eff3fa]' : 'border-slate-50 hover:border-slate-200'}">
            
            <div class="flex items-center gap-6">
              <input type="checkbox" bind:checked={session.selected} class="w-8 h-8 rounded-xl accent-[#2a3c54]" />
              <div class="space-y-1">
                <span class="text-[10px] font-black text-[#6b8cce] uppercase tracking-widest">{session.date}</span>
                <p class="text-xl font-black text-[#2a3c54]">{session.title}</p>
                <p class="text-sm font-bold text-slate-400">الساعة: {session.time}</p>
              </div>
            </div>
          </label>
        {/each}
      </div>

      <button onclick={sendRequests} class="w-full py-6 bg-[#2a3c54] text-white rounded-[2.5rem] font-black text-xl shadow-xl hover:scale-[1.02] transition-all">
        إرسال طلب الانضمام للأيام المحددة
      </button>
    </div>
  </div>
</div>