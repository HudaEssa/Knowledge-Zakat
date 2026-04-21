<script>
  // استيراد المكونات الصحيحة للأدمن
  import UserManager from "../components/UserManager.svelte";
  // 👈 هنا استبدلنا المكون القديم بمكون الأدمن الحقيقي لطلبات التوظيف
  import AdminDashboard from "../components/AdminDashboard.svelte"; 
  import CategoryManager from "../components/admin.svelte"; 
  import LogViewer from "../components/LogViewer.svelte";
  import AdminStats from "../components/AdminStats.svelte";

  // إدارة التبويبات باستخدام Svelte 5 Runes 
  let activeTab = $state("users");
</script>

<div class="space-y-8" dir="rtl">
  <AdminStats />

  <div class="flex flex-wrap gap-4 mb-10 bg-white p-4 rounded-[2rem] shadow-sm border border-slate-100 w-fit">
    {#each [
      {id: 'users', label: 'إدارة المستخدمين', icon: '👥'},
      {id: 'requests', label: 'طلبات الانضمام كمعلم', icon: '🎓'}, // تصحيح التسمية لبيان الوظيفة
      {id: 'sessions', label: 'إدارة التصنيفات', icon: '🏷️'},
      {id: 'logs', label: 'سجل النشاطات', icon: '📜'}
    ] as tab}
      <button 
        onclick={() => activeTab = tab.id}
        class="px-8 py-3 rounded-2xl font-black transition-all flex items-center gap-2
        {activeTab === tab.id ? 'bg-[#6b8cce] text-white shadow-lg' : 'text-slate-400 hover:bg-slate-50'}">
        <span class="text-xl">{tab.icon}</span>
        {tab.label}
      </button>
    {/each}
  </div>

  <div class="transition-all duration-300">
    {#if activeTab === 'users'}
      <UserManager />
    {:else if activeTab === 'requests'}
      <AdminDashboard /> 
    {:else if activeTab === 'sessions'}
      <CategoryManager />
    {:else if activeTab === 'logs'}
      <LogViewer />
    {/if}
  </div>
</div>