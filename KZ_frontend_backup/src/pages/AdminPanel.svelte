<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { fade } from 'svelte/transition';
  import api from '../lib/api';
  
  import UserManager from '../components/UserManager.svelte';
  import AdminDashboard from '../components/AdminDashboard.svelte';
  import CategoryManager from '../components/admin.svelte';
  import LogViewer from '../components/LogViewer.svelte';
  import AdminStats from '../components/AdminStats.svelte';

  // استيراد الأيقونات الاحترافية
  import { 
    Users, 
    UserStar, 
    Tags, 
    History 
  } from 'lucide-svelte';

  // ---- تعريف التبويبات (حل إيرور TabId) --------------------------------------
  type TabId = 'users' | 'requests' | 'categories' | 'logs';
  interface TabDef { id: TabId; label: string; icon: any; }

  const TABS: TabDef[] = [
    { id: 'users', label: 'إدارة المستخدمين', icon: Users },
    { id: 'requests', label: 'طلبات الانضمام', icon: UserStar },
    { id: 'categories', label: 'إدارة التصنيفات', icon: Tags },
    { id: 'logs', label: 'سجل النشاطات', icon: History },
  ];

  // ---- الحالة (State) باستخدام Svelte 5 ------------------------------------
  let activeTab = $state<TabId>('users');
  // حالة الإحصائيات مع التايب لضمان التوافق مع AdminStats
  let stats = $state({ students: 0, teachers: 0, sessions: 0, requests: 0 });
  let isLoadingStats = $state(true);
  let syncInterval: any;

  // دالة جلب الإحصائيات الموحدة (Auto-Sync)
 // دالة جلب الإحصائيات الموحدة (Auto-Sync)
  async function fetchLiveStats() {
    try {
      const [uRes, sRes, rRes] = await Promise.all([
        // 👈 نطلب limit عالي (مثلاً 10000) بس حتى نجيبهم كلهم ونحسبهم للإحصائيات
        api.get('/users/?limit=10000').catch(() => ({ data: { items: [], total: 0 } })),
        api.get('/sessions/').catch(() => ({ data: [] })),
        api.get('/admin/teacher-requests?status=pending&limit=1').catch(() => ({ data: { total: 0 } }))
      ]);

      // 👈 السر هنا: نقرأ الداتا من حقل items اللي سويناه بالـ Pagination
      const usersArray = uRes.data.items || [];

      stats = {
        students: usersArray.filter((u: any) => u.roles?.some((r: any) => r.role_name === 'student')).length,
        teachers: usersArray.filter((u: any) => u.roles?.some((r: any) => r.role_name === 'teacher')).length,
        sessions: sRes.data.length || 0,
        requests: rRes.data.total || 0 
      };
    } finally {
      isLoadingStats = false;
    }
  }
  // ---- Lifecycle ----------------------------------------------------------
  onMount(() => {
    // استعادة التبويب من الـ LocalStorage
    const saved = localStorage.getItem('kz.admin.activeTab');
    if (saved && TABS.some(t => t.id === saved)) activeTab = saved as TabId;

    fetchLiveStats();
    // تحديث الأرقام كل 10 ثواني تلقائياً (بدون ريفرش)
    syncInterval = setInterval(fetchLiveStats, 10000);
  });

  onDestroy(() => {
    if (syncInterval) clearInterval(syncInterval);
  });

  // حفظ التبويب الحالي في الـ LocalStorage
  $effect(() => {
    localStorage.setItem('kz.admin.activeTab', activeTab);
  });
</script>

<div class="min-h-screen bg-transparent pb-20 text-right" dir="rtl">
  
  <div class="max-w-7xl mx-auto px-8 pt-12">
    <AdminStats {stats} isLoading={isLoadingStats} />
  </div>

  <main class="max-w-7xl mx-auto px-8 mt-6">
    
    <nav class="flex gap-2 bg-white/60 backdrop-blur-md p-2.5 rounded-[2.5rem] shadow-sm mb-12 border border-white/40 overflow-x-auto no-scrollbar">
      {#each TABS as tab}
        <button
          onclick={() => activeTab = tab.id}
          class="flex items-center gap-4 px-3 py-2 rounded-full transition-all whitespace-nowrap
          {activeTab === tab.id 
            ? 'bg-[#2a3c54] text-white shadow-lg' 
            : 'text-slate-500 hover:bg-white/50'}"
        >
          <div class="p-3 rounded-xl flex items-center justify-center shrink-0 
              {activeTab === tab.id ? 'bg-white/10 text-white' : 'bg-slate-100 text-brand-dark/40'}">
             <tab.icon size={20} />
          </div>
          <span class="font-black text-sm pl-6">{tab.label}</span>
        </button>
      {/each}
    </nav>

    <div class="relative min-h-[500px]">
      {#if activeTab === 'users'}
        <div in:fade={{ duration: 250 }}><UserManager /></div>
      {:else if activeTab === 'requests'}
        <div in:fade={{ duration: 250 }}><AdminDashboard /></div>
      {:else if activeTab === 'categories'}
        <div in:fade={{ duration: 250 }}><CategoryManager /></div>
      {:else if activeTab === 'logs'}
        <div in:fade={{ duration: 250 }}><LogViewer /></div>
      {/if}
    </div>

  </main>
</div>

<style>
  .no-scrollbar::-webkit-scrollbar { display: none; }
</style>