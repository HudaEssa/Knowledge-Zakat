<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, slide, scale } from 'svelte/transition'; // ضفنا scale هنا حتى يروح الخط الأحمر
  import api from '../lib/api';
  import { notify } from '../lib/notifications';
  import type { Category } from '../lib/types';
  import { Tags, Plus, Trash2, Edit3, Check, X } from 'lucide-svelte';

  let categories = $state<Category[]>([]);
  let isLoading = $state(true);
  let newCatName = $state('');
  let editingId = $state<number | null>(null);
  let editValue = $state('');
  let pendingDelete = $state<Category | null>(null);

  async function loadCategories() {
    try {
      const res = await api.get<Category[]>('/admin/categories');
      categories = res.data.sort((a, b) => a.category_name.localeCompare(b.category_name, 'ar'));
    } catch { notify.error('تعذّر جلب التصنيفات'); }
    finally { isLoading = false; }
  }

  async function addCategory() {
    if (!newCatName.trim()) return;
    try {
      await api.post('/admin/categories/', { category_name: newCatName.trim() });
      newCatName = '';
      await loadCategories();
      notify.success('تمت الإضافة');
    } catch { notify.error('التصنيف موجود مسبقاً'); }
  }

  async function saveEdit(id: number) {
    if (!editValue.trim()) return;
    try {
      await api.put(`/admin/categories/${id}`, { category_name: editValue.trim() });
      editingId = null;
      await loadCategories();
      notify.success('تم التعديل');
    } catch { notify.error('فشل التعديل'); }
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    try {
      await api.delete(`/admin/categories/${pendingDelete.id}`); // صلحنا الرابط هنا
      pendingDelete = null;
      await loadCategories();
      notify.success('تم الحذف');
    } catch { notify.error('فشل الحذف'); }
  }

  onMount(loadCategories);
</script>

<div class="space-y-6 text-right" dir="rtl">
  <div class="bg-white p-6 rounded-2xl shadow-sm border border-brand-100">
    <div class="flex gap-3">
      <input bind:value={newCatName} placeholder="إضافة تصنيف جديد..." class="flex-1 bg-brand-soft/50 px-4 py-2 rounded-xl outline-none font-bold text-sm border-none" />
      <button onclick={addCategory} class="bg-brand text-white px-6 py-2 rounded-xl font-black text-xs flex items-center gap-2">
        <Plus size={16} /> إضافة
      </button>
    </div>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
    {#each categories as cat (cat.id)}
      <div in:fade class="bg-white p-4 rounded-xl border border-brand-50 flex justify-between items-center group hover:border-brand transition-all">
        {#if editingId === cat.id}
          <input bind:value={editValue} class="flex-1 bg-slate-50 px-2 py-1 rounded-md text-sm font-bold outline-none border-b-2 border-brand" />
          <div class="flex gap-1 mr-2">
            <button onclick={() => saveEdit(cat.id)} class="text-emerald-500"><Check size={16} /></button>
            <button onclick={() => editingId = null} class="text-slate-400"><X size={16} /></button>
          </div>
        {:else}
          <span class="font-bold text-slate-700 text-sm">{cat.category_name}</span>
          <div class="flex gap-2 opacity-0 group-hover:opacity-100 transition-all">
            <button onclick={() => { editingId = cat.id; editValue = cat.category_name; }} class="text-blue-400 hover:text-brand"><Edit3 size={16} /></button>
            <button onclick={() => pendingDelete = cat} class="text-red-300 hover:text-red-500"><Trash2 size={16} /></button>
          </div>
        {/if}
      </div>
    {/each}
  </div>
</div>

{#if pendingDelete}
  <div class="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4" dir="rtl">
    <div in:scale class="bg-white p-8 rounded-3xl max-w-sm w-full text-center shadow-2xl border-t-4 border-red-500">
      <h3 class="font-black text-lg mb-4 text-slate-800">حذف "{pendingDelete.category_name}"؟</h3>
      <div class="flex gap-3">
        <button onclick={confirmDelete} class="flex-1 bg-red-500 text-white py-2 rounded-xl font-black text-sm">حذف</button>
        <button onclick={() => pendingDelete = null} class="flex-1 bg-slate-100 text-slate-500 py-2 rounded-xl font-black text-sm">إلغاء</button>
      </div>
    </div>
  </div>
{/if}