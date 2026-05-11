<!--
  Knowledge Zakat — Teacher dashboard.

  Three KPI cards + two Chart.js plots:
    - Enrollment growth (last 7 days, line chart).
    - Rating distribution (1–5 stars, bar chart).

  Data comes from a single endpoint: GET /teacher/dashboard-stats.

  Refactor highlights:
   - Strict TypeScript on the stats payload (DashboardStats type).
   - Charts are torn down in Svelte's onDestroy hook so re-mounting the
     page (or hot-reloading during dev) doesn't leak canvas instances.
     The legacy code stored chart refs in a module-level array but only
     destroyed them on data refresh, leaving leaks on full unmount.
   - Loading state now shows shimmer cards rather than empty space, so
     the page doesn't visibly "jump" when the data arrives.
   - All errors flow through `notify.error` (was a swallowed console.error).
-->

<script lang="ts">
  import { onMount, onDestroy, tick } from 'svelte';
  import { fade, scale } from 'svelte/transition';
  import Chart, { type ChartConfiguration } from 'chart.js/auto';
  import api from '../lib/api';
  import { user } from '../lib/stores';
  import { notify } from '../lib/notifications';

  // ---- Local types --------------------------------------------------------
  interface DashboardStats {
    totalStudents: number;
    pendingRequests: number;
    avgRating: number;
    /** Cumulative enrollment count for the last 7 days. */
    enrollmentGrowth: number[];
    /** Buckets for ratings 1..5. Length 5. */
    ratingDistribution: number[];
  }

  // ---- State --------------------------------------------------------------
  let stats = $state<DashboardStats>({
    totalStudents: 0,
    pendingRequests: 0,
    avgRating: 0,
    enrollmentGrowth: [],
    ratingDistribution: [],
  });
  let isLoading = $state(true);

  // Canvas element refs and chart instances. The canvas refs come
  // from `bind:this`; the chart instances are kept in a separate
  // array so we can dispose them cleanly.
  let enrollmentChartEl = $state<HTMLCanvasElement | null>(null);
  let ratingChartEl = $state<HTMLCanvasElement | null>(null);
  let chartInstances: Chart[] = [];

  // ---- Data fetch ---------------------------------------------------------
  async function fetchDashboardData(): Promise<void> {
    try {
      const res = await api.get<DashboardStats>('/teacher/dashboard-stats');
      stats = res.data;
    } catch {
      notify.error('تعذّر تحميل إحصائيات لوحة التحكم');
    } finally {
      isLoading = false;
      // Wait for Svelte to commit the new DOM before grabbing canvas refs.
      await tick();
      buildCharts();
    }
  }

  // ---- Chart construction -------------------------------------------------
// ---- Chart construction -------------------------------------------------
  function buildCharts(): void {
    // Refuse to build until both canvases exist AND we have data.
    if (!enrollmentChartEl || !ratingChartEl) return;

    // Tear down anything previously rendered to keep the canvas clean.
    disposeCharts();

    const lineCfg: ChartConfiguration<'line'> = {
      type: 'line',
      data: {
        labels: ['منذ 6 أيام', '5 أيام', '4 أيام', '3 أيام', 'يومين', 'أمس', 'اليوم'],
        datasets: [
          {
            label: 'إجمالي الطلاب',
            // 👇 التعديل هنا: استخدام [...] لفك الـ Proxy
            data: [...stats.enrollmentGrowth], 
            borderColor: '#6b8cce',
            backgroundColor: 'rgba(107, 140, 206, 0.1)',
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointBackgroundColor: '#2a3c54',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, ticks: { stepSize: 1 } },
        },
      },
    };

    const barCfg: ChartConfiguration<'bar'> = {
      type: 'bar',
      data: {
        labels: ['1 ★', '2 ★', '3 ★', '4 ★', '5 ★'],
        datasets: [
          {
            // 👇 التعديل هنا: استخدام [...] لفك الـ Proxy
            data: [...stats.ratingDistribution], 
            backgroundColor: '#2a3c54',
            borderRadius: 8,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, ticks: { stepSize: 1 } },
        },
      },
    };

    chartInstances = [
      new Chart(enrollmentChartEl, lineCfg),
      new Chart(ratingChartEl, barCfg),
    ];
  }

  function disposeCharts(): void {
    chartInstances.forEach((c) => c.destroy());
    chartInstances = [];
  }

  // ---- Lifecycle ----------------------------------------------------------
  onMount(fetchDashboardData);
  onDestroy(disposeCharts);
</script>

<div class="space-y-10 md:space-y-12 pb-12 md:pb-20 text-right" dir="rtl">
  <!-- Header -->
  <header in:fade>
    <h1 class="text-3xl md:text-4xl font-black text-[#2a3c54]">لوحة الإحصائيات</h1>
    <p class="text-slate-400 font-bold mt-2 italic text-sm md:text-base">
      مرحباً أستاذ {$user?.firstname ?? ''}، هذه أرقام نشاطك العلمي المسجلة حالياً
    </p>
  </header>

  <!-- KPI cards -->
  {#if isLoading}
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
      {#each Array(3) as _, i (i)}
        <div class="bg-white p-8 rounded-[2.5rem] md:rounded-[3rem] border border-slate-50">
          <div class="h-3 bg-slate-100 rounded animate-pulse w-1/2"></div>
          <div class="h-12 bg-slate-100 rounded-xl animate-pulse mt-3 w-1/3"></div>
        </div>
      {/each}
    </div>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
      <div
        in:scale={{ delay: 100 }}
        class="bg-white p-6 md:p-8 rounded-[2.5rem] md:rounded-[3rem] shadow-sm border border-slate-50 hover:shadow-md transition-shadow"
      >
        <span class="text-[10px] font-black text-slate-300 uppercase tracking-widest">
          إجمالي الطلاب المقبولين
        </span>
        <div class="text-4xl md:text-5xl font-black text-[#2a3c54] mt-3">
          {stats.totalStudents}
        </div>
      </div>

      <div
        in:scale={{ delay: 200 }}
        class="bg-gradient-to-br from-[#2a3c54] to-[#1f3047] p-6 md:p-8 rounded-[2.5rem] md:rounded-[3rem] shadow-xl text-white hover:shadow-2xl transition-shadow"
      >
        <span class="text-[10px] font-black opacity-50 uppercase tracking-widest">
          طلبات معلقة
        </span>
        <div class="text-4xl md:text-5xl font-black text-[#6b8cce] mt-3">
          {stats.pendingRequests}
        </div>
      </div>

      <div
        in:scale={{ delay: 300 }}
        class="bg-white p-6 md:p-8 rounded-[2.5rem] md:rounded-[3rem] shadow-sm border border-slate-50 hover:shadow-md transition-shadow"
      >
        <span class="text-[10px] font-black text-slate-300 uppercase tracking-widest">
          متوسط التقييم
        </span>
        <div class="text-4xl md:text-5xl font-black text-emerald-500 mt-3">
          ⭐ {stats.avgRating > 0 ? stats.avgRating.toFixed(1) : '—'}
        </div>
      </div>
    </div>
  {/if}

  <!-- Charts -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 md:gap-10">
    <div
      in:fade={{ delay: 400 }}
      class="bg-white p-8 md:p-10 rounded-[2.5rem] md:rounded-[3.5rem] shadow-sm border border-slate-50"
    >
      <h3 class="text-lg md:text-xl font-black text-[#2a3c54] mb-8 md:mb-10 border-r-4 border-[#6b8cce] pr-4">
        منحنى نمو الطلاب
      </h3>
      <div class="h-56 md:h-64 relative">
        {#if !isLoading}
          <canvas bind:this={enrollmentChartEl}></canvas>
        {:else}
          <div
            class="h-full w-full bg-slate-50 rounded-2xl animate-pulse flex items-center justify-center"
          >
            <span class="text-slate-300 font-black text-sm">جاري تحميل الرسم البياني...</span>
          </div>
        {/if}
      </div>
    </div>

    <div
      in:fade={{ delay: 500 }}
      class="bg-white p-8 md:p-10 rounded-[2.5rem] md:rounded-[3.5rem] shadow-sm border border-slate-50"
    >
      <h3 class="text-lg md:text-xl font-black text-[#2a3c54] mb-8 md:mb-10 border-r-4 border-[#6b8cce] pr-4">
        تحليل مستويات الرضا
      </h3>
      <div class="h-56 md:h-64 relative">
        {#if !isLoading}
          <canvas bind:this={ratingChartEl}></canvas>
        {:else}
          <div
            class="h-full w-full bg-slate-50 rounded-2xl animate-pulse flex items-center justify-center"
          >
            <span class="text-slate-300 font-black text-sm">جاري تحميل الرسم البياني...</span>
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>
