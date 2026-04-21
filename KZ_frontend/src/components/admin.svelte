<script>
  import { onMount } from 'svelte';
  import api from '../lib/api';
  import { fade, slide } from 'svelte/transition';

  // --- الحالة العامة ---
  let isLoading = $state(true);

  // --- بيانات التصنيفات ---
  let categories = $state([]);
  let newCatName = $state("");
  let editingCatId = $state(null);
  let editCatValue = $state("");
  let activeCatMenu = $state(null);

  // --- وظائف الجلب ---
  async function loadCategories() {
    isLoading = true;
    try {
      const res = await api.get('/categories/');
      // ترتيب التصنيفات أبجدياً لسهولة البحث [cite: 2026-02-23]
      categories = res.data.sort((a, b) => a.category_name.localeCompare(b.category_name, 'ar'));
    } catch (e) {
      console.error("خطأ في جلب التصنيفات من قاعدة البيانات");
    } finally {
      isLoading = false;
    }
  }

  // --- عمليات التصنيفات ---
  async function addCategory() {
    if (!newCatName.trim()) return;
    try {
      await api.post("/categories/", { category_name: newCatName });
      newCatName = "";
      loadCategories();
    } catch (e) { 
      alert("عذراً، هذا التصنيف موجود مسبقاً"); 
    }
  }

  async function updateCategory() {
    if (!editCatValue.trim()) return;
    try {
      await api.put(`/categories/${editingCatId}`, { category_name: editCatValue });
      editingCatId = null;
      activeCatMenu = null;
      loadCategories();
    } catch (e) { 
      alert("فشل تحديث اسم التصنيف"); 
    }
  }

  async function deleteCategory(id) {
    if (!confirm("هل أنت متأكد من حذف هذا التصنيف؟ سيؤدي ذلك لإزالته من كافة الجلسات المرتبطة.")) return;
    try {
      await api.delete(`/categories/${id}`);
      loadCategories();
    } catch (e) { 
      alert("فشل عملية الحذف"); 
    }
  }

  onMount(loadCategories);
</script>

<div class="space-y-8" dir="rtl">
  <header>
    <h2 class="text-3xl font-black text-[#2a3c54]">إدارة التصنيفات العلمية</h2>
   
  </header>

  {#if isLoading}
    <div class="py-20 text-center font-black text-slate-300 animate-pulse text-xl">جاري مزامنة التصنيفات...</div>
  {:else}
    <div in:fade class="bg-white p-10 rounded-[2.5rem] shadow-sm border border-slate-50">
      <h3 class="text-xl font-black mb-6 text-[#2a3c54] border-r-4 border-[#6b8cce] pr-4">إضافة تصنيف جديد</h3>
      <div class="flex gap-4">
        <input 
          bind:value={newCatName} 
          placeholder="مثال: هندسة البرمجيات، الأمن السيبراني..." 
          class="flex-1 bg-slate-50 px-6 py-4 rounded-2xl outline-none focus:ring-2 ring-[#6b8cce] font-bold border-0 transition-all"
        >
        <button 
          onclick={addCategory} 
          class="bg-[#6b8cce] text-white px-10 rounded-2xl font-black hover:scale-105 active:scale-95 transition-all shadow-lg shadow-[#6b8cce]/20"
        >
          تأكيد الإضافة
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      {#each categories as cat (cat.id)}
        <div class="relative group" in:slide>
          <button 
            onclick={() => activeCatMenu = activeCatMenu === cat.id ? null : cat.id}
            class="w-full p-6 bg-white border border-slate-100 rounded-[2rem] shadow-sm font-black text-[#2a3c54] text-right transition-all hover:border-[#6b8cce] hover:shadow-md
            {activeCatMenu === cat.id ? 'ring-2 ring-[#6b8cce]' : ''}">
            {cat.category_name}
          </button>

          {#if activeCatMenu === cat.id}
            <div in:slide class="absolute top-full left-0 right-0 mt-2 p-4 bg-[#2a3c54] rounded-2xl z-20 shadow-2xl border border-white/10">
              {#if editingCatId === cat.id}
                <input 
                  bind:value={editCatValue} 
                  class="w-full p-3 bg-white/10 text-white rounded-xl outline-none font-bold text-sm mb-3 border border-white/10" 
                />
                <div class="flex gap-2">
                  <button onclick={updateCategory} class="flex-1 bg-emerald-500 text-white py-2.5 rounded-xl text-[10px] font-black hover:bg-emerald-600 transition-colors">حفظ التعديل</button>
                  <button onclick={() => editingCatId = null} class="flex-1 bg-white/10 text-white py-2.5 rounded-xl text-[10px] font-black hover:bg-white/20 transition-colors">إلغاء</button>
                </div>
              {:else}
                <button 
                  onclick={() => { editingCatId = cat.id; editCatValue = cat.category_name; }} 
                  class="w-full py-2.5 text-white/70 hover:text-white font-black text-xs text-right px-4 rounded-lg hover:bg-white/5 transition-all"
                >
                  تعديل التسمية ✏️
                </button>
                <button 
                  onclick={() => deleteCategory(cat.id)} 
                  class="w-full py-2.5 text-red-400 hover:text-red-500 font-black text-xs text-right px-4 rounded-lg hover:bg-red-500/10 mt-1 transition-all"
                >
                  حذف التصنيف 🗑️
                </button>
              {/if}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  /* تحسينات بصرية إضافية */
  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>