<script>
  import api from "../lib/api";
  import { fade, scale } from "svelte/transition";
  import { onMount } from 'svelte';
  
  let teacherRequests = $state([]);
  let isFetching = $state(true);
  let selectedUser = $state(null);

  async function loadTeacherRequests() {
    try {
      const res = await api.get('/admin/teacher-requests');
      teacherRequests = res.data;
    } catch (e) { 
      console.error("فشل جلب طلبات التوظيف"); 
    } finally { 
      isFetching = false; 
    }
  }

  onMount(loadTeacherRequests);

  async function approveTeacher(userId) {
    try {
      await api.post(`/admin/users/${userId}/promote-to-teacher`);
      teacherRequests = teacherRequests.filter(u => u.id !== userId);
      selectedUser = null;
      alert("تم قبول المعلم بنجاح! ✅");
    } catch (e) { 
      alert("فشل في ترقية المستخدم.."); 
    }
  }
  async function rejectTeacher(userId) {
    if (!confirm("هل أنت متأكد من رفض هذا الطلب؟ سيبقى المستخدم كطالب في المنصة.")) return;
    
    try {
      await api.post(`/admin/users/${userId}/reject-teacher-request`);
      // إخفاء الطلب من الواجهة بعد الرفض
      teacherRequests = teacherRequests.filter(u => u.id !== userId);
      selectedUser = null; // إغلاق النافذة إذا كانت مفتوحة
      alert("تم رفض الطلب بنجاح ❌");
    } catch (e) { 
      alert("فشل في رفض الطلب.."); 
    }
  }
</script>

<div class="space-y-6 text-right">
  <h2 class="text-2xl font-black text-[#2a3c54]">طلبات الانضمام كمعلم 🎓</h2>
  
  {#if isFetching}
    <div class="py-20 text-center text-slate-400 font-bold animate-pulse italic">جاري تحميل الطلبات...</div>
  {:else if teacherRequests.length === 0}
    <div in:fade class="p-12 border-2 border-dashed border-slate-100 rounded-[2rem] text-center text-slate-400 font-bold">
      لا توجد طلبات توظيف جديدة حالياً.
    </div>
  {:else}
    <div class="grid gap-4">
      {#each teacherRequests as user (user.id)}
        <div class="bg-white p-6 rounded-[2rem] shadow-sm border border-slate-50 flex justify-between items-center hover:shadow-md transition-all" in:fade>
          <div class="flex gap-4 items-center">
            {#if user.profile_image}
               <img src={user.profile_image} alt="User" class="w-12 h-12 rounded-xl object-cover shadow-sm" />
            {:else}
               <div class="w-12 h-12 bg-[#eff3fa] rounded-xl flex items-center justify-center font-black text-[#6b8cce]">{user.firstname.charAt(0)}</div>
            {/if}
             <div>
                <p class="font-black text-[#2a3c54]">{user.firstname} {user.lastname}</p>
                <p class="text-xs text-slate-400 font-bold">{user.email}</p>
             </div>
          </div>
          <div class="flex gap-2">
            <button onclick={() => selectedUser = user} class="bg-[#eff3fa] text-[#6b8cce] px-4 py-2 rounded-xl font-black text-xs hover:bg-[#e2e8f0] transition-all">التفاصيل 📄</button>
            <button onclick={() => approveTeacher(user.id)} class="bg-emerald-500 text-white px-6 py-2 rounded-xl font-black text-xs hover:scale-105 transition-all">قبول ✅</button>
            <button onclick={() => rejectTeacher(user.id)} class="bg-red-50 text-red-500 px-6 py-2 rounded-xl font-black text-xs hover:bg-red-100 transition-all">رفض ❌</button>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

{#if selectedUser}
  <div in:fade out:fade class="fixed inset-0 z-[200] flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4" dir="rtl">
    <div in:scale class="bg-white rounded-[2.5rem] p-8 shadow-2xl max-w-md w-full border-t-8 border-[#6b8cce] max-h-[90vh] overflow-y-auto">
      
      <div class="flex justify-between items-start mb-6">
        <h3 class="text-xl font-black text-[#2a3c54]">معلومات طلب الانضمام</h3>
        <button onclick={() => selectedUser = null} class="text-slate-400 hover:text-red-500 text-2xl font-bold leading-none">&times;</button>
      </div>

      <div class="flex flex-col items-center mb-6">
        {#if selectedUser.profile_image}
          <img src={selectedUser.profile_image} alt="Profile" class="w-24 h-24 rounded-2xl object-cover shadow-md mb-4" />
        {:else}
          <div class="w-24 h-24 bg-[#eff3fa] rounded-2xl flex items-center justify-center font-black text-4xl text-[#6b8cce] mb-4">
            {selectedUser.firstname.charAt(0)}
          </div>
        {/if}
        <h4 class="font-black text-xl text-[#2a3c54]">{selectedUser.firstname} {selectedUser.lastname}</h4>
        <span class="text-sm font-bold text-slate-500">{selectedUser.email}</span>
      </div>

      <div class="space-y-4 bg-slate-50 p-6 rounded-2xl border border-slate-100 text-right">
        <div>
          <span class="block text-xs font-bold text-slate-400 mb-1">رقم الهاتف:</span>
          <p class="text-sm font-semibold text-[#2a3c54]" dir="ltr">{selectedUser.phone}</p>
        </div>
        <div>
          <span class="block text-xs font-bold text-slate-400 mb-1">تاريخ الميلاد:</span>
          <p class="text-sm font-semibold text-[#2a3c54]">{selectedUser.birthday_date}</p>
        </div>
        <div>
          <span class="block text-xs font-bold text-slate-400 mb-1">النبذة التعريفية:</span>
          <p class="text-sm font-semibold text-[#2a3c54]">{selectedUser.bio}</p>
        </div>
       <div>
          <span class="block text-xs font-bold text-slate-400 mb-1">الشهادة / الهوية:</span>
          {#if selectedUser.cv_link && selectedUser.cv_link.includes('/static/')}
            <a 
              href={`http://localhost:8000${selectedUser.cv_link}`} 
              target="_blank" 
              class="inline-flex items-center gap-2 text-sm font-bold text-white bg-[#6b8cce] px-5 py-2.5 rounded-xl hover:bg-[#5a7abb] shadow-md transition-all"
            >
              عرض المرفق 🖼️
            </a>
          {:else}
            <p class="text-sm font-semibold text-slate-400">لا يوجد مرفق صالح</p>
          {/if}
        </div>
        <div class="flex gap-3 mt-8">
        <button onclick={() => selectedUser = null} class="flex-1 bg-slate-100 text-slate-600 py-3 rounded-xl font-bold hover:bg-slate-200 transition-colors">إغلاق</button>
        <button onclick={() => rejectTeacher(selectedUser.id)} class="flex-1 bg-red-50 text-red-500 py-3 rounded-xl font-black hover:bg-red-100 transition-colors">رفض ❌</button>
        <button onclick={() => approveTeacher(selectedUser.id)} class="flex-[2] bg-emerald-500 text-white py-3 rounded-xl font-black shadow-lg shadow-emerald-500/30 hover:scale-105 transition-transform">قبول كمعلم ✅</button>
      </div>
      </div>

     
    </div>
  </div>
{/if}