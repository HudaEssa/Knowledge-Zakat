<script lang="ts">
  import { onMount } from 'svelte';
  import { scale, fly, fade } from 'svelte/transition';
  import { 
    Bell, X, Trash2, UserPlus, CheckCircle, XCircle, 
    BellOff, ChevronLeft 
  } from 'lucide-svelte';
  import axios from 'axios';
  import { user } from '../lib/stores';
  import { navigate } from '../lib/router';

  let notifications = $state<any[]>([]);
  let isOpen = $state(false);
  let isLoading = $state(true);

  const TYPE_CONFIG: any = {
    approved: { icon: CheckCircle, color: 'text-emerald-500', bg: 'bg-emerald-50' },
    rejected: { icon: XCircle, color: 'text-rose-500', bg: 'bg-rose-50' },
    new_request: { icon: UserPlus, color: 'text-indigo-500', bg: 'bg-indigo-50' }
  };

  async function fetchNotifications() {
    const token = localStorage.getItem('kz.token'); 
    if (!token || !$user) { isLoading = false; return; }
    try {
      const res = await axios.get('http://127.0.0.1:8000/sessions/notifications/all', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      notifications = res.data;
    } catch (err) { console.warn("Fetch failed"); } finally { isLoading = false; }
  }

  // حذف تنبيه واحد
  async function deleteOne(id: number) {
    const token = localStorage.getItem('kz.token');
    // تحديث الواجهة فوراً (Optimistic UI)
    notifications = notifications.filter(n => n.session_id !== id);
    try {
      await axios.delete(`http://127.0.0.1:8000/sessions/notifications/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
    } catch (err) { console.error("Delete failed"); }
  }

  // حذف الكل
  async function clearAll() {
    const token = localStorage.getItem('kz.token');
    notifications = [];
    try {
      await axios.delete('http://127.0.0.1:8000/sessions/notifications/clear-all', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
    } catch (err) { console.error("Clear failed"); }
  }

  onMount(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 60000); 
    return () => clearInterval(interval);
  });

  function handleAction(notif: any) {
    if (notif.type === 'rejected') return; // لا تفاعل مع الرفض
    isOpen = false;
    if (notif.target_page) navigate(notif.target_page as any);
  }
</script>

<div class="relative">
  <button 
    onclick={() => isOpen = !isOpen} 
    class="p-2.5 bg-brand-soft/30 border border-brand-100 text-brand rounded-2xl hover:bg-brand-soft transition-all active:scale-90 relative shadow-sm"
  >
    <Bell size={22} strokeWidth={2.5} class={notifications.length > 0 ? 'text-brand' : 'opacity-40'} />
    {#if notifications.length > 0}
      <span class="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[10px] font-black text-white ring-4 ring-white" in:scale>{notifications.length}</span>
    {/if}
  </button>

  {#if isOpen}
    <div class="fixed inset-0 z-[-1]" onclick={() => isOpen = false} role="presentation"></div>

    <div in:fly={{ y: 15, duration: 400 }} class="absolute left-0 mt-4 w-96 bg-white/95 backdrop-blur-xl border border-brand-100 shadow-2xl rounded-[2.5rem] overflow-hidden z-[9999]" dir="rtl">
      
      <div class="p-6 border-b border-brand-50 flex justify-between items-center bg-brand-soft/10">
        <div>
          <h3 class="text-sm font-black text-brand">التنبيهات</h3>
          <p class="text-[10px] font-bold text-slate-400">لديك {notifications.length} إشعارات</p>
        </div>
        <div class="flex gap-2">
          {#if notifications.length > 0}
            <button onclick={clearAll} class="px-3 py-1.5 text-[10px] font-black text-rose-500 hover:bg-rose-50 rounded-full transition-colors">مسح الكل</button>
          {/if}
          <button onclick={() => isOpen = false} class="p-1.5 text-slate-300 hover:text-rose-500 transition-colors"><X size={18} /></button>
        </div>
      </div>

      <div class="max-h-[450px] overflow-y-auto custom-scrollbar p-3 space-y-2">
        {#if isLoading}
          <div class="p-12 text-center text-xs font-bold text-slate-300 animate-pulse">جاري جلب البيانات...</div>
        {:else if notifications.length === 0}
          <div class="p-12 text-center flex flex-col items-center gap-4">
            <div class="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center">
              <BellOff size={32} class="text-slate-200" />
            </div>
            <p class="text-xs font-bold text-slate-400">لا توجد تنبيهات جديدة</p>
          </div>
        {:else}
          {#each notifications as notif (notif.id)}
            {@const cfg = TYPE_CONFIG[notif.type] || TYPE_CONFIG.new_request}
            {@const Icon = cfg.icon}
            
            <div 
              class="w-full p-4 flex gap-4 items-center rounded-3xl border border-transparent transition-all group relative
              {notif.type === 'rejected' ? 'cursor-default opacity-80' : 'cursor-pointer hover:bg-brand-soft/30 hover:border-brand-100 shadow-sm bg-white'}"
              onclick={() => handleAction(notif)}
              role="button"
              tabindex="0"
            >
              <div class="w-11 h-11 rounded-2xl flex items-center justify-center shrink-0 {cfg.bg} {cfg.color}">
                <Icon size={20} />
              </div>

              <div class="min-w-0 flex-1">
                <p class="text-xs font-black text-slate-800 mb-0.5">{notif.title}</p>
                <p class="text-[10px] font-bold text-slate-500 leading-relaxed line-clamp-2">{notif.message}</p>
              </div>

              <div class="flex items-center gap-1">
                {#if notif.type !== 'rejected'}
                  <ChevronLeft size={14} class="text-brand/30 group-hover:text-brand transition-colors" />
                {/if}
                <button 
                  onclick={(e) => { e.stopPropagation(); deleteOne(notif.session_id); }}
                  class="opacity-0 group-hover:opacity-100 p-2 text-slate-300 hover:text-rose-500 hover:bg-rose-50 rounded-xl transition-all"
                  title="حذف التنبيه"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          {/each}
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar { width: 4px; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 10px; }
  div { font-family: 'Tajawal', sans-serif; }
</style>