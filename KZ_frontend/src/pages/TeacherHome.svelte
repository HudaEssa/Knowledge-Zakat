<script>
  import { onMount } from "svelte";
  import api from "../lib/api";
  import { user } from "../lib/stores";
  import Chart from 'chart.js/auto';
  import { fade, scale } from "svelte/transition";

  let stats = $state({ totalStudents: 0, pendingRequests: 0, avgRating: 0 });
  let isLoading = $state(true);
  
  let enrollmentChartRef;
  let ratingChartRef;
  let charts = []; // لتخزين مراجع الرسوم البيانية وحذفها عند التحديث

  onMount(async () => {
    await fetchDashboardData();
  });

  async function fetchDashboardData() {
    try {
      const res = await api.get('/teacher/dashboard-stats');
      stats = res.data;
      
      // تهيئة الرسوم البيانية بالبيانات الحقيقية
      initializeCharts(res.data);
    } catch (error) {
      console.error("فشل في استرداد الإحصائيات:", error);
    } finally {
      isLoading = false;
    }
  }

  function initializeCharts(data) {
    // تدمير الرسوم القديمة إذا وجدت لمنع تداخل البيانات
    charts.forEach(c => c.destroy());

    // 1. رسم بياني لنمو انضمام الطلاب (بيانات حقيقية)
    const ctx1 = new Chart(enrollmentChartRef, {
      type: 'line',
      data: {
        labels: ['منذ 6 أيام', '5 أيام', '4 أيام', '3 أيام', 'يومين', 'أمس', 'اليوم'],
        datasets: [{
          label: 'إجمالي الطلاب',
          data: data.enrollmentGrowth, 
          borderColor: '#6b8cce',
          backgroundColor: 'rgba(107, 140, 206, 0.1)',
          fill: true,
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } }
      }
    });

    // 2. رسم بياني لتوزيع التقييمات (بيانات حقيقية)
    const ctx2 = new Chart(ratingChartRef, {
      type: 'bar',
      data: {
        labels: ['1⭐', '2⭐', '3⭐', '4⭐', '5⭐'],
        datasets: [{
          data: data.ratingDistribution, 
          backgroundColor: '#2a3c54',
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
      }
    });

    charts = [ctx1, ctx2];
  }
</script>

<div class="space-y-12 pb-20 text-right" dir="rtl">
  <header in:fade>
    <h1 class="text-4xl font-black text-[#2a3c54]">لوحة الإحصائيات</h1>
    <p class="text-slate-400 font-bold mt-2 italic text-sm">مرحباً أستاذ {$user?.firstname}، هذه أرقام نشاطك العلمي المسجلة حالياً.</p>
  </header>

  <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
    <div in:scale={{ delay: 100 }} class="bg-white p-8 rounded-[3rem] shadow-sm border border-slate-50">
      <span class="text-[10px] font-black text-slate-300 uppercase tracking-widest">إجمالي الطلاب المقبولين</span>
      <div class="text-5xl font-black text-[#2a3c54] mt-3">{stats.totalStudents}</div>
    </div>

    <div in:scale={{ delay: 200 }} class="bg-[#2a3c54] p-8 rounded-[3rem] shadow-xl text-white">
      <span class="text-[10px] font-black opacity-40 uppercase tracking-widest">طلبات معلقة</span>
      <div class="text-5xl font-black text-[#6b8cce] mt-3">{stats.pendingRequests}</div>
    </div>

    <div in:scale={{ delay: 300 }} class="bg-white p-8 rounded-[3rem] shadow-sm border border-slate-50">
      <span class="text-[10px] font-black text-slate-300 uppercase tracking-widest">متوسط التقييم</span>
      <div class="text-5xl font-black text-emerald-500 mt-3">⭐ {stats.avgRating}</div>
    </div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-10">
    <div in:fade={{ delay: 400 }} class="bg-white p-10 rounded-[3.5rem] shadow-sm border border-slate-50">
      <h3 class="text-xl font-black text-[#2a3c54] mb-10 border-r-4 border-[#6b8cce] pr-4">منحنى نمو الطلاب</h3>
      <div class="h-64">
        <canvas bind:this={enrollmentChartRef}></canvas>
      </div>
    </div>

    <div in:fade={{ delay: 500 }} class="bg-white p-10 rounded-[3.5rem] shadow-sm border border-slate-50">
      <h3 class="text-xl font-black text-[#2a3c54] mb-10 border-r-4 border-[#6b8cce] pr-4">تحليل مستويات الرضا</h3>
      <div class="h-64">
        <canvas bind:this={ratingChartRef}></canvas>
      </div>
    </div>
  </div>
</div>