<script>
  import { onMount } from "svelte";
  import api from "../lib/api";
  import { fade, scale } from "svelte/transition";

  // --- الحالة (State) ---
  let users = $state([]);
  let isLoading = $state(true);
  let viewingUser = $state(null); 
  let searchTerm = $state(""); // نص البحث

  // متغيرات الإشعارات (Modal)
  let showNotify = $state(false);
  let modalMsg = $state("");
  let modalIcon = $state("");

  // متغيرات واجهة تأكيد الحذف
  let showDeleteConfirm = $state(false);
  let userToDelete = $state(null);

  // إعدادات الترقيم
  let currentPage = $state(0);
  const itemsPerPage = 6;

  // --- الدوال (Functions) ---

  function notify(msg, icon = "") {
    modalMsg = msg; modalIcon = icon; showNotify = true;
  }

  async function fetchUsers() {
    try {
      const res = await api.get("/users/");
      // الترتيب الأبجدي العربي حسب الاسم الأول
      users = res.data.sort((a, b) => {
        const nameA = a.firstname.toLowerCase();
        const nameB = b.firstname.toLowerCase();
        return nameA.localeCompare(nameB, 'ar');
      });
    } catch (err) {
      console.error("فشل جلب المستخدمين");
    } finally {
      isLoading = false;
    }
  }

  // --- منطق البحث والفلترة (Derived State) ---
  
  // فلترة المستخدمين بناءً على نص البحث
  let filteredUsers = $derived(
    users.filter(u => 
      u.firstname.toLowerCase().includes(searchTerm.toLowerCase()) || 
      u.lastname.toLowerCase().includes(searchTerm.toLowerCase()) || 
      u.email.toLowerCase().includes(searchTerm.toLowerCase())
    )
  );

  // تحديث عدد الصفحات بناءً على نتائج البحث
  let totalPages = $derived(Math.ceil(filteredUsers.length / itemsPerPage));
  
  // استقطاع المستخدمين للصفحة الحالية من النتائج المفلترة
  let paginatedUsers = $derived(
    filteredUsers.slice(currentPage * itemsPerPage, (currentPage + 1) * itemsPerPage)
  );

  // تصفير رقم الصفحة عند البدء ببحث جديد لضمان ظهور النتائج
  $effect(() => {
    if (searchTerm) {
      currentPage = 0;
    }
  });

  async function toggleStatus(id) {
    try {
      await api.patch(`/admin/users/${id}/status`, {}, {
        headers: { Authorization: "Bearer " + localStorage.getItem("token") }
      });
      fetchUsers();
      notify("تم تحديث حالة الحساب بنجاح", "تنبيه");
    } catch (err) {
      notify("فشل تحديث الحالة", "خطأ");
    }
  }

  function requestDelete(user) {
    userToDelete = user;
    showDeleteConfirm = true;
  }

  async function executeDelete() {
    if (!userToDelete) return;
    try {
      await api.delete(`/admin/users/${userToDelete.id}/delete`, {
        headers: { Authorization: "Bearer " + localStorage.getItem("token") }
      });
      showDeleteConfirm = false;
      notify(`تم حذف المستخدم "${userToDelete.firstname}" نهائيا`, "نجاح");
      userToDelete = null;
      fetchUsers();
    } catch (err) {
      showDeleteConfirm = false;
      notify("فشل الحذف، تأكد من صلاحيات المسؤول", "خطأ");
    }
  }

  onMount(fetchUsers);
</script>

{#if showNotify}
<div in:fade out:fade class="fixed inset-0 z-[10000] flex items-center justify-center p-4 bg-[#2a3c54]/60 backdrop-blur-sm" dir="rtl">
  <div in:scale={{duration: 300, start: 0.9}} class="bg-[#fafcff] rounded-[2.5rem] p-10 max-w-sm w-full text-center shadow-2xl border-t-8 border-[#6b8cce]">
    {#if modalIcon}
      <div class="text-lg font-black text-[#6b8cce] mb-4 uppercase tracking-widest">{modalIcon}</div>
    {/if}
    <p class="text-xl font-black text-[#2a3c54] leading-relaxed">{modalMsg}</p>
    <button onclick={() => showNotify = false} class="mt-8 w-full py-4 bg-[#2a3c54] text-white rounded-2xl font-black hover:bg-[#4a6583] transition-colors shadow-lg">حسناً</button>
  </div>
</div>
{/if}

{#if showDeleteConfirm}
<div in:fade out:fade class="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-red-900/40 backdrop-blur-md" dir="rtl">
  <div in:scale class="bg-white p-10 rounded-[3rem] max-w-md w-full text-center shadow-2xl border-t-8 border-rose-500">
    <div class="w-16 h-16 bg-rose-50 text-rose-500 rounded-full flex items-center justify-center text-xs font-black mx-auto mb-6 shadow-inner">تنبيه</div>
    <h3 class="text-2xl font-black text-[#2a3c54] mb-4">هل أنت متأكد؟</h3>
    <p class="text-slate-500 font-medium leading-relaxed mb-8">
      أنت على وشك حذف حساب <span class="text-rose-600 font-black">{userToDelete?.firstname} {userToDelete?.lastname}</span> نهائياً من النظام. لا يمكن التراجع عن هذا الإجراء.
    </p>
    <div class="flex gap-4">
      <button onclick={executeDelete} class="flex-1 py-4 bg-rose-500 text-white rounded-2xl font-black hover:bg-rose-600 transition-all shadow-lg shadow-rose-200">تأكيد الحذف</button>
      <button onclick={() => {showDeleteConfirm = false; userToDelete = null;}} class="flex-1 py-4 bg-slate-100 text-slate-500 rounded-2xl font-black hover:bg-slate-200 transition-all">إلغاء</button>
    </div>
  </div>
</div>
{/if}

<div class="bg-white rounded-[2.5rem] p-8 shadow-sm border border-slate-50 text-right" dir="rtl">
  
  <div class="flex justify-between items-center mb-8">
    <h2 class="text-2xl font-black text-[#2a3c54] border-r-4 border-[#6b8cce] pr-4">إدارة حسابات المنصة</h2>
    <span class="text-xs font-bold text-slate-300 bg-slate-50 px-4 py-2 rounded-full">إجمالي المستخدمين: {users.length}</span>
  </div>

  <div class="mb-8 relative">
    <input 
      type="text" 
      bind:value={searchTerm} 
      placeholder="ابحث بالاسم أو البريد الإلكتروني..." 
      class="w-full p-4 pr-12 bg-slate-50 rounded-2xl outline-none border border-slate-100 focus:border-[#6b8cce] focus:bg-white transition-all font-medium text-sm text-[#2a3c54]"
    />
    <div class="absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-none text-slate-300 font-bold text-xs">
      بحث
    </div>
  </div>
  
  {#if isLoading}
    <div class="py-20 text-center font-bold text-slate-400 animate-pulse italic">جاري جلب البيانات...</div>
  {:else}
    <div class="overflow-x-auto">
      <table class="w-full text-right">
        <thead>
          <tr class="text-slate-400 border-b font-black">
            <th class="pb-6">المستخدم</th>
            <th class="pb-6 text-center">الحالة</th>
            <th class="pb-6 text-left">الإجراءات</th>
          </tr>
        </thead>
        <tbody>
          {#each paginatedUsers as u (u.id)}
            <tr in:fade class="border-b hover:bg-slate-50/50 transition-all group">
              <td class="py-6">
                <div class="font-black text-[#2a3c54] group-hover:text-[#6b8cce] transition-colors">{u.firstname} {u.lastname}</div>
                <div class="text-xs text-slate-400 font-bold">{u.email}</div>
              </td>
              <td class="py-6 text-center">
                <span class="px-4 py-1.5 rounded-xl text-[10px] font-black {u.is_active ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'}">
                  {u.is_active ? 'نشط' : 'محظور'}
                </span>
              </td>
              <td class="py-6 text-left flex gap-2 justify-end">
                <button onclick={() => viewingUser = u} class="bg-blue-50 text-blue-600 px-5 py-2 rounded-xl text-xs font-black hover:bg-blue-100 transition-colors">التفاصيل</button>
                <button onclick={() => requestDelete(u)} class="bg-rose-50 text-rose-600 px-5 py-2 rounded-xl text-xs font-black hover:bg-rose-100 transition-colors">حذف</button>
                <button onclick={() => toggleStatus(u.id)} class="px-5 py-2 rounded-xl text-xs font-black transition-all {u.is_active ? 'bg-amber-50 text-amber-600' : 'bg-green-50 text-green-600'}">
                  {u.is_active ? 'حظر' : 'تفعيل'}
                </button>
              </td>
            </tr>
          {/each}
          {#if filteredUsers.length === 0}
            <tr>
              <td colspan="3" class="py-20 text-center font-bold text-slate-400 italic">لا توجد نتائج تطابق بحثك.</td>
            </tr>
          {/if}
        </tbody>
      </table>
    </div>

    {#if totalPages > 1}
      <div class="mt-10 flex items-center justify-center gap-4">
        <button 
          disabled={currentPage === 0} 
          onclick={() => currentPage--} 
          class="w-10 h-10 flex items-center justify-center rounded-xl bg-slate-100 text-[#2a3c54] font-black disabled:opacity-20 hover:bg-slate-200 transition-all font-sans"
        >
          {'>'}
        </button>
        <div class="flex gap-2">
          {#each Array(totalPages) as _, i}
            <button 
              onclick={() => currentPage = i} 
              class="w-10 h-10 rounded-xl font-black text-xs transition-all {currentPage === i ? 'bg-[#2a3c54] text-white shadow-lg' : 'bg-slate-50 text-slate-400 hover:bg-slate-100'}"
            >
              {i + 1}
            </button>
          {/each}
        </div>
        <button 
          disabled={currentPage === totalPages - 1} 
          onclick={() => currentPage++} 
          class="w-10 h-10 flex items-center justify-center rounded-xl bg-slate-100 text-[#2a3c54] font-black disabled:opacity-20 hover:bg-slate-200 transition-all font-sans"
        >
          {'<'}
        </button>
      </div>
    {/if}
  {/if}
</div>

{#if viewingUser}
<div in:fade class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[999] p-4" dir="rtl">
  <div in:scale class="bg-white p-10 rounded-[3rem] w-full max-w-xl shadow-2xl text-right relative overflow-hidden">
    <div class="absolute top-0 right-0 w-full h-2 bg-[#6b8cce]"></div>
    
    <div class="mb-8">
      <h3 class="text-2xl font-black text-[#2a3c54]">ملف المستخدم</h3>
      <p class="text-xs font-bold text-slate-400">معاينة البيانات المسجلة حالياً</p>
    </div>
    
    <div class="space-y-6">
      <div class="grid grid-cols-2 gap-4">
        <div class="bg-slate-50 p-4 rounded-2xl border border-slate-100">
          <span class="text-[10px] font-bold text-slate-400 block mb-1">الاسم الكامل</span>
          <p class="font-black text-[#2a3c54]">{viewingUser.firstname} {viewingUser.lastname}</p>
        </div>
        <div class="bg-slate-50 p-4 rounded-2xl border border-slate-100">
          <span class="text-[10px] font-bold text-slate-400 block mb-1">حالة الحساب</span>
          <p class="font-black {viewingUser.is_active ? 'text-green-600' : 'text-red-600'}">
            {viewingUser.is_active ? 'نشط' : 'محظور'}
          </p>
        </div>
      </div>

      <div class="bg-slate-50 p-4 rounded-2xl border border-slate-100">
        <span class="text-[10px] font-bold text-slate-400 block mb-1">البريد الإلكتروني</span>
        <p class="font-black text-[#2a3c54]">{viewingUser.email}</p>
      </div>

      <div class="bg-slate-50 p-5 rounded-2xl border border-slate-100">
        <span class="text-[10px] font-bold text-slate-400 block mb-1">النبذة الشخصية</span>
        <p class="text-sm text-slate-600 leading-relaxed font-medium">
          {viewingUser.bio || "لا توجد معلومات مضافة."}
        </p>
      </div>
    </div>

    <div class="mt-10">
      <button onclick={() => viewingUser = null} class="w-full py-4 bg-[#2a3c54] text-white rounded-2xl font-black hover:bg-[#4a6583] transition-all shadow-lg shadow-[#2a3c54]/20">
        إغلاق المعاينة
      </button>
    </div>
  </div>
</div>
{/if}