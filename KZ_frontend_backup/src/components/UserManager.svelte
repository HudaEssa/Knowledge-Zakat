<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, scale, slide } from 'svelte/transition';
  import api from '../lib/api';
  
  import { user as currentUserStore } from '../lib/stores';
  import { notify } from '../lib/notifications';
  import type { User } from '../lib/types';
  import { 
    UserX, ShieldCheck, Trash2, Eye, Search, Users, 
    ChevronRight, ChevronLeft, X, UserPlus, Loader2
  } from 'lucide-svelte';

  // ---- State --------------------------------------------------------------
  let currentPage = $state(0);
  const itemsPerPage = 6;
  
  let users = $state<User[]>([]);
  let totalUsers = $state(0); // 👈 لحفظ العدد الكلي القادم من السيرفر
  let isLoading = $state(true);
  
  let viewingUser = $state<User | null>(null);
  let searchTerm = $state('');
  
  // Delete-confirmation modal
  let userToDelete = $state<User | null>(null);
  let isDeleting = $state(false);

  // Admin Creation Modal
  let showAddAdmin = $state(false);
  let isCreatingAdmin = $state(false);
  let adminForm = $state({ firstname: '', lastname: '', email: '', phone: '', password: '' });

  // ---- Data load ----------------------------------------------------------
  async function fetchUsers(): Promise<void> {
    isLoading = true;
    try {
      const offset = currentPage * itemsPerPage;
      // 👈 استدعاء الباك إند مع تمرير الصفحة الحالية
      const res = await api.get<{items: User[], total: number}>(`/users/?offset=${offset}&limit=${itemsPerPage}`);
      
      users = res.data.items.sort((a, b) =>
        a.firstname.toLowerCase().localeCompare(b.firstname.toLowerCase(), 'ar'),
      );
      totalUsers = res.data.total; // 👈 تحديث العدد الكلي
    } catch {
      notify.error('تعذّر تحميل قائمة المستخدمين');
    } finally {
      isLoading = false;
    }
  }

  // 👈 دالة التنقل بين الصفحات
  async function goToPage(page: number) {
    currentPage = page;
    await fetchUsers();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // ---- Derived: search + pagination ---------------------------------------
  let filteredUsers = $derived(
    users.filter((u) => {
      const q = searchTerm.toLowerCase().trim();
      if (!q) return true;
      return (
        u.firstname.toLowerCase().includes(q) ||
        u.lastname.toLowerCase().includes(q) ||
        u.email.toLowerCase().includes(q)
      );
    }),
  );

  // 👈 حساب عدد الصفحات الكلي بناءً على بيانات السيرفر
  let totalPages = $derived(Math.max(1, Math.ceil(totalUsers / itemsPerPage)));

  // ---- Actions ------------------------------------------------------------
  async function toggleStatus(u: User): Promise<void> {
    if (u.id === $currentUserStore?.id) {
      notify.warning('لا يمكنك حظر حسابك الخاص');
      return;
    }
    // منع حظر مدير آخر أيضاً
    if (u.roles.some(r => r.role_name === 'admin')) {
      notify.error('لا يمكن تغيير حالة حساب مدير آخر 🛡️');
      return;
    }

    try {
      await api.patch(`/admin/users/${u.id}/status`);
      notify.success(u.is_active ? 'تم تجميد الحساب بنجاح' : 'تم تفعيل الحساب بنجاح');
      await fetchUsers();
    } catch { notify.error('فشل تحديث حالة الحساب'); }
  }

  function requestDelete(u: User): void {
    if (u.id === $currentUserStore?.id) {
      notify.warning('استخدم إعدادات حسابك لحذفه');
      return;
    }
    userToDelete = u;
  }

  async function executeDelete(): Promise<void> {
    if (!userToDelete || isDeleting) return;
    isDeleting = true;
    try {
      await api.delete(`/users/${userToDelete.id}`); 
      notify.success(`تم حذف الحساب بنجاح`);
      userToDelete = null;
      await fetchUsers(); // 👈 إعادة جلب البيانات لتحديث الـ Pagination
    } catch (err: any) {
      notify.error(err.response?.data?.detail || 'تعذّر حذف الحساب');
    } finally {
      isDeleting = false;
    }
  }

  // ---- Create Admin --------------------------------------------------------
  async function handleCreateAdmin() {
    if (!adminForm.firstname || !adminForm.email || !adminForm.password) {
      notify.warning('يرجى تعبئة جميع الحقول المطلوبة');
      return;
    }
    if (adminForm.password.length < 8) {
      notify.warning('كلمة المرور يجب أن تكون 8 أحرف على الأقل');
      return;
    }

    isCreatingAdmin = true;
    try {
      await api.post('/users/create-admin', adminForm);
      notify.success('تم إنشاء حساب المدير بنجاح 🎉');
      showAddAdmin = false;
      adminForm = { firstname: '', lastname: '', email: '', phone: '', password: '' };
      await fetchUsers();
    } catch (err: any) {
      notify.error(err.response?.data?.detail || 'فشل إنشاء حساب المدير');
    } finally {
      isCreatingAdmin = false;
    }
  }

  function getRolesText(u: User): string {
    return u.roles.map((r) => r.role_name).join('، ') || 'مستخدم';
  }

  onMount(fetchUsers);
</script>

<div class="space-y-6 text-right" dir="rtl">
  
  <div class="flex justify-between items-center mb-8 flex-wrap gap-4">
    <div class="flex items-center gap-3">
      <div class="w-12 h-12 bg-brand-soft rounded-2xl flex items-center justify-center text-brand shadow-inner">
        <Users size={24} />
      </div>
      <h2 class="text-2xl font-black text-[#2a3c54]">إدارة حسابات المنصة</h2>
    </div>
    
    <button onclick={() => showAddAdmin = true} class="flex items-center gap-2 bg-[#2a3c54] text-white px-5 py-2.5 rounded-xl font-black text-sm hover:bg-[#6b8cce] transition-all shadow-md active:scale-95">
      <UserPlus size={18} /> إضافة مدير جديد
    </button>
  </div>

  <div class="relative group">
    <input
      type="text"
      bind:value={searchTerm}
      placeholder="ابحث بالاسم أو البريد الإلكتروني في هذه الصفحة..."
      class="w-full p-4 pr-12 bg-white rounded-[1.5rem] outline-none border border-brand-100 focus:border-brand focus:ring-4 focus:ring-brand-soft transition-all font-bold text-sm text-[#2a3c54] shadow-sm"
    />
    <Search class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-300 group-focus-within:text-brand transition-colors" size={20} />
  </div>

  {#if isLoading}
    <div class="space-y-4">
      {#each Array(4) as _}
        <div class="h-20 bg-white/50 rounded-3xl animate-pulse"></div>
      {/each}
    </div>
  {:else}
    <div class="bg-white rounded-[2.5rem] shadow-sm border border-brand-50 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-right border-collapse">
          <thead>
            <tr class="bg-slate-50/50 text-slate-400 font-black text-xs uppercase tracking-widest border-b border-brand-50">
              <th class="p-6">المستخدم</th>
              <th class="p-6 text-center hidden md:table-cell">الحالة</th>
              <th class="p-6 text-left">الإجراءات</th>
            </tr>
          </thead>
          <tbody>
            {#each filteredUsers as u (u.id)}
              {@const isTargetAdmin = u.roles.some(r => r.role_name === 'admin')}
              {@const isMe = u.id === $currentUserStore?.id}

              <tr in:fade class="border-b border-brand-50 hover:bg-brand-soft/20 transition-all group {isTargetAdmin ? 'bg-amber-50/20' : ''}">
                <td class="p-6">
                  <div class="flex items-center gap-2">
                    <div class="font-black text-[#2a3c54] group-hover:text-brand transition-colors text-sm">
                      {u.firstname} {u.lastname}
                    </div>
                    {#if isTargetAdmin}
                      <span title="مدير نظام"><ShieldCheck size={14} class="text-amber-500" /></span>
                    {/if}
                  </div>
                  <div class="text-[10px] text-slate-400 font-bold mt-1" dir="ltr">{u.email}</div>
                </td>
                <td class="p-6 text-center hidden md:table-cell">
                  <span class="px-4 py-1.5 rounded-xl text-[10px] font-black {u.is_active ? 'bg-emerald-50 text-emerald-600 border border-emerald-100' : 'bg-rose-50 text-rose-600 border border-rose-100'}">
                    {u.is_active ? 'نشط' : 'محظور'}
                  </span>
                </td>
                <td class="p-6">
                  <div class="flex gap-2 justify-end">
                    <button onclick={() => viewingUser = u} class="p-2.5 bg-blue-50 text-blue-600 rounded-xl hover:bg-blue-100 transition-all" title="تفاصيل">
                      <Eye size={16}/>
                    </button>
                    
                    {#if isTargetAdmin && !isMe}
                      <button disabled class="p-2.5 bg-slate-50 text-slate-300 rounded-xl cursor-not-allowed border border-slate-100" title="هذا الحساب محمي">
                        <ShieldCheck size={16}/>
                      </button>
                    {:else}
                      <button onclick={() => toggleStatus(u)} 
                        class="p-2.5 rounded-xl transition-all {u.is_active ? 'bg-amber-50 text-amber-600 hover:bg-amber-100' : 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100'}"
                        title={u.is_active ? 'حظر' : 'تفعيل'}>
                        {#if u.is_active} <UserX size={16}/> {:else} <ShieldCheck size={16}/> {/if}
                      </button>
                      
                      <button onclick={() => requestDelete(u)} class="p-2.5 bg-rose-50 text-rose-600 rounded-xl hover:bg-rose-100 transition-all" title="حذف">
                        <Trash2 size={16}/>
                      </button>
                    {/if}
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>

      {#if filteredUsers.length === 0}
        <div class="py-20 text-center text-slate-400 font-bold italic">لا توجد نتائج تطابق بحثك</div>
      {/if}
    </div>

    {#if totalPages > 1}
      <div class="mt-8 flex items-center justify-center gap-4">
        <button disabled={currentPage === 0} onclick={() => goToPage(currentPage - 1)} class="p-2 bg-white rounded-xl shadow-sm disabled:opacity-20 hover:bg-brand-soft text-brand transition-all">
          <ChevronRight size={20}/>
        </button>
        <span class="text-xs font-black text-slate-400">صفحة {currentPage + 1} من {totalPages}</span>
        <button disabled={currentPage === totalPages - 1} onclick={() => goToPage(currentPage + 1)} class="p-2 bg-white rounded-xl shadow-sm disabled:opacity-20 hover:bg-brand-soft text-brand transition-all">
          <ChevronLeft size={20}/>
        </button>
      </div>
    {/if}
  {/if}
</div>

{#if showAddAdmin}
  <div in:fade class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center z-[1000] p-4" dir="rtl">
    <div in:scale={{ duration: 300, start: 0.9 }} class="bg-white rounded-[2.5rem] w-full max-w-md shadow-2xl overflow-hidden">
      <div class="bg-gradient-to-r from-[#2a3c54] to-[#6b8cce] p-6 text-white flex justify-between items-center">
        <h3 class="text-lg font-black flex items-center gap-2"><UserPlus size={20} /> إضافة مدير جديد</h3>
        <button onclick={() => showAddAdmin = false} class="p-1 hover:bg-white/20 rounded-full transition-colors"><X size={20}/></button>
      </div>
      
      <div class="p-8 space-y-4">
        <div class="flex gap-4">
          <div class="flex-1">
            <label for="admin-firstname" class="block text-[10px] font-bold text-slate-500 mb-1">الاسم الأول <span class="text-rose-500">*</span></label>
            <input type="text" bind:value={adminForm.firstname} class="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-bold text-[#2a3c54] focus:border-[#6b8cce] outline-none" />
          </div>
          <div class="flex-1">
           <label for="admin-lastname" class="block text-[10px] font-bold text-slate-500 mb-1">اسم العائلة <span class="text-rose-500">*</span></label>
            <input type="text" bind:value={adminForm.lastname} class="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-bold text-[#2a3c54] focus:border-[#6b8cce] outline-none" />
          </div>
        </div>

        <div>
          <label for="admin-email" class="block text-[10px] font-bold text-slate-500 mb-1">البريد الإلكتروني <span class="text-rose-500">*</span></label>
          <input type="email" bind:value={adminForm.email} dir="ltr" placeholder="admin@zk.com" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-bold text-[#2a3c54] focus:border-[#6b8cce] outline-none text-left" />
        </div>

        <div>
          <label for="admin-phone" class="block text-[10px] font-bold text-slate-500 mb-1">رقم الهاتف</label>
          <input type="tel" bind:value={adminForm.phone} dir="ltr" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-bold text-[#2a3c54] focus:border-[#6b8cce] outline-none text-left" />
        </div>

        <div>
          <label for="admin-password" class="block text-[10px] font-bold text-slate-500 mb-1">كلمة المرور <span class="text-rose-500">*</span></label>
          <input type="text" bind:value={adminForm.password} dir="ltr" placeholder="8 أحرف على الأقل" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-bold text-[#2a3c54] focus:border-[#6b8cce] outline-none text-left" />
        </div>

        <button onclick={handleCreateAdmin} disabled={isCreatingAdmin} class="w-full mt-4 py-3.5 bg-[#2a3c54] text-white rounded-xl font-black shadow-md hover:bg-[#6b8cce] transition-all flex justify-center items-center gap-2">
          {#if isCreatingAdmin} <Loader2 size={18} class="animate-spin" /> جاري الإنشاء... {:else} إنشاء الحساب {/if}
        </button>
      </div>
    </div>
  </div>
{/if}

{#if viewingUser}
  <div in:fade class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center z-[1000] p-4" dir="rtl">
    <div in:scale={{ duration: 300, start: 0.9 }} class="bg-white rounded-[3rem] w-full max-w-lg shadow-2xl overflow-hidden border border-white">
      <div class="bg-[#2a3c54] p-8 text-white flex justify-between items-center">
        <div><h3 class="text-xl font-black">ملف المستخدم</h3><p class="text-xs opacity-70">المعرف #{viewingUser.id}</p></div>
        <button onclick={() => viewingUser = null} class="p-2 hover:bg-white/10 rounded-full transition-colors"><X size={24}/></button>
      </div>
      <div class="p-8 space-y-4">
        <div class="bg-slate-50 p-4 rounded-2xl border border-slate-100"><p class="text-[10px] font-bold text-slate-400 mb-1">الاسم</p><p class="font-black text-[#2a3c54]">{viewingUser.firstname} {viewingUser.lastname}</p></div>
        <div class="bg-slate-50 p-4 rounded-2xl border border-slate-100"><p class="text-[10px] font-bold text-slate-400 mb-1">البريد</p><p class="font-black text-[#2a3c54]">{viewingUser.email}</p></div>
        <div class="bg-slate-50 p-4 rounded-2xl border border-slate-100"><p class="text-[10px] font-bold text-slate-400 mb-1">الأدوار</p><p class="font-black text-brand">{getRolesText(viewingUser)}</p></div>
        <button onclick={() => viewingUser = null} class="w-full py-4 bg-[#2a3c54] text-white rounded-2xl font-black mt-4 shadow-lg">إغلاق</button>
      </div>
    </div>
  </div>
{/if}

{#if userToDelete}
  <div in:fade class="fixed inset-0 bg-rose-900/20 backdrop-blur-md flex items-center justify-center z-[1000] p-4" dir="rtl">
    <div in:scale={{ duration: 250, start: 0.95 }} class="bg-white p-10 rounded-[3rem] max-w-sm w-full text-center shadow-2xl border-t-8 border-rose-500">
      <div class="w-16 h-16 bg-rose-50 text-rose-500 rounded-full flex items-center justify-center mx-auto mb-6"><Trash2 size={32}/></div>
      <h3 class="text-2xl font-black text-[#2a3c54] mb-3">حذف الحساب؟</h3>
      <p class="text-slate-500 font-bold text-sm mb-8 leading-relaxed">أنت على وشك حذف حساب <br/><span class="text-rose-600">{userToDelete.firstname}</span> نهائياً.</p>
      <div class="flex gap-3">
        <button onclick={executeDelete} disabled={isDeleting} class="flex-1 py-3 bg-rose-500 text-white rounded-2xl font-black hover:bg-rose-600 transition-all shadow-lg shadow-rose-200">
          {isDeleting ? 'جاري الحذف...' : 'نعم، احذف'}
        </button>
        <button onclick={() => userToDelete = null} class="flex-1 py-3 bg-slate-100 text-slate-500 rounded-2xl font-black hover:bg-slate-200">إلغاء</button>
      </div>
    </div>
  </div>
{/if}