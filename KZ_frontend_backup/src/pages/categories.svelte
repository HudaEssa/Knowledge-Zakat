<script>
  import { onMount } from 'svelte';
  import api from '../lib/api';

  let categories = [];
  let isLoading = true;

  onMount(async () => {
    try {
      const res = await api.get('/categories/');
      categories = res.data;
    } catch (e) {
      console.error(e);
      // Dummy data for demo
      categories = [
        { id: 1, name: 'تطوير الويب', description: 'بناء المواقع باستخدام أحدث التقنيات', count: 12 },
        { id: 2, name: 'الأمن السيبراني', description: 'حماية الأنظمة والشبكات من الاختراقات', count: 5 }
      ];
    } finally {
      isLoading = false;
    }
  });
</script>

<div class="space-y-6">
  <div class="bg-white p-8 rounded-[2rem] shadow-sm border border-slate-100 flex justify-between items-center">
    <div>
      <h1 class="text-3xl font-black text-slate-800">إدارة التصنيفات</h1>
      <p class="text-slate-500 font-medium mt-1">تصفح وتعديل أقسام المنصة العلمية.</p>
    </div>
    <span class="bg-blue-100 text-blue-700 font-black px-6 py-3 rounded-2xl">العدد: {categories.length}</span>
  </div>

  <div class="bg-white rounded-[2rem] shadow-xl border border-slate-100 overflow-hidden">
    <table class="w-full text-right">
      <thead class="bg-slate-900 text-white">
        <tr>
          <th class="p-6 font-black text-lg">اسم التصنيف</th>
          <th class="p-6 font-black text-lg">الوصف المختصر</th>
          <th class="p-6 font-black text-lg text-center">الجلسات</th>
          <th class="p-6 font-black text-lg text-left">خيار</th>
        </tr>
      </thead>
      <tbody>
        {#each categories as cat}
          <tr class="hover:bg-blue-50/50 transition-colors">
            <td class="p-6 font-black text-slate-800 text-xl">{cat.name}</td>
            <td class="p-6 text-slate-600 font-bold leading-relaxed">{cat.description}</td>
            <td class="p-6 text-center">
              <span class="bg-slate-100 px-4 py-2 rounded-xl font-black">{cat.count}</span>
            </td>
            <td class="p-6 text-left">
              <button class="text-blue-600 font-black hover:underline">تعديل</button>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
</div>