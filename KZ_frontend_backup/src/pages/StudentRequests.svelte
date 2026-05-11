<script>
  import api from "../lib/api";
  import { fade } from "svelte/transition";

  let requests = $state([]);

  async function updateStatus(userId, sessionId, newStatus) {
    try {
      await api.put('/enrollments/status', {
        user_id: userId,
        session_id: sessionId,
        status: newStatus
      });
      requests = requests.filter(r => !(r.user_id === userId && r.session_id === sessionId));
    } catch (err) { console.error("فشل التحديث"); }
  }
</script>

<div class="space-y-8 text-right" dir="rtl" in:fade>
  <h1 class="text-3xl font-black text-[#2a3c54]">طلبات الانضمام للجلسات</h1>

  <div class="grid grid-cols-1 gap-4">
    {#each requests as req}
      <div class="bg-white p-8 rounded-[3rem] shadow-xl border border-white flex justify-between items-center">
        <div class="flex items-center gap-6">
          <div class="w-16 h-16 bg-[#eff3fa] rounded-2xl flex items-center justify-center text-xl font-black text-[#6b8cce]">
            {req.student_name.charAt(0)}
          </div>
          <div>
            <p class="font-black text-[#2a3c54]">{req.student_name}</p>
            <p class="text-sm font-bold text-slate-400">يريد الانضمام لجلسة: {req.session_title}</p>
            <p class="text-[10px] font-black text-[#6b8cce] uppercase">{req.session_date}</p>
          </div>
        </div>

        <div class="flex gap-4">
          <button onclick={() => updateStatus(req.user_id, req.session_id, 'approved')} class="px-8 py-3 bg-emerald-500 text-white rounded-2xl font-black text-sm hover:bg-emerald-600 transition-all">قبول</button>
          <button onclick={() => updateStatus(req.user_id, req.session_id, 'rejected')} class="px-8 py-3 bg-red-500 text-white rounded-2xl font-black text-sm hover:bg-red-600 transition-all">رفض</button>
        </div>
      </div>
    {/each}
  </div>
</div>