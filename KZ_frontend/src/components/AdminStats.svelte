<script>
  import { onMount } from "svelte";
  import api from "../lib/api";
  import { scale } from "svelte/transition";

  // 👈 ضفنا avgRating للإحصائيات
  let stats = $state({ students: 0, teachers: 0, sessions: 0, requests: 0, avgRating: 0 });
  let isLoading = $state(true);

  onMount(async () => {
    try {
      const [uRes, sRes, rRes] = await Promise.all([
        api.get("/users/"),
        api.get("/sessions/"),
        api.get("/admin/teacher-requests")
      ]);
      
      const teachers = uRes.data.filter(u => u.roles.some(r => r.id === 2 || r.role_name === 'teacher')).length;
      const students = uRes.data.filter(u => u.roles.some(r => r.id === 1 || r.role_name === 'student')).length;

      // 👈 حساب متوسط التقييم لكل الجلسات المنشورة
      const allSessions = sRes.data;
      const totalRating = allSessions.reduce((acc, s) => acc + (s.avg_rating || 0), 0);
      const average = allSessions.length > 0 ? (totalRating / allSessions.length).toFixed(1) : 0;

      stats = {
        students: students,
        teachers: teachers,
        sessions: allSessions.length,
        requests: rRes.data.length,
        avgRating: average
      };
    } catch (error) {
      console.error("خطأ في جلب الإحصائيات:", error);
    } finally {
      isLoading = false;
    }
  });
</script>

<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-10 text-right" dir="rtl">
  
  <div in:scale={{delay: 100}} class="bg-gradient-to-br from-[#2a3c54] to-[#4a6583] p-6 rounded-[2rem] text-white shadow-lg relative overflow-hidden group">
    <div class="text-xs font-bold opacity-70 mb-1">إجمالي الطلاب</div>
    <div class="text-3xl font-black">{isLoading ? '...' : stats.students}</div>
    <div class="absolute -right-2 -bottom-2 text-white/10 text-6xl">👥</div>
  </div>

  <div in:scale={{delay: 200}} class="bg-white p-6 rounded-[2rem] border border-slate-100 shadow-sm group">
    <div class="text-xs font-bold text-slate-400 mb-1">المعلمون</div>
    <div class="text-3xl font-black text-[#2a3c54]">{isLoading ? '...' : stats.teachers}</div>
  </div>

  <div in:scale={{delay: 300}} class="bg-white p-6 rounded-[2rem] border border-slate-100 shadow-sm group">
    <div class="text-xs font-bold text-slate-400 mb-1">الجلسات</div>
    <div class="text-3xl font-black text-[#2a3c54]">{isLoading ? '...' : stats.sessions}</div>
  </div>

  <div in:scale={{delay: 400}} class="bg-white p-6 rounded-[2rem] border border-slate-100 shadow-sm group">
    <div class="text-xs font-bold text-orange-400 mb-1">طلبات التقديم</div>
    <div class="text-3xl font-black text-orange-500">{isLoading ? '...' : stats.requests}</div>
  </div>


</div>