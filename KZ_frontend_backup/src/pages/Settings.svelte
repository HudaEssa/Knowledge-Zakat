<script>
  import { onMount } from "svelte";

  let darkMode = $state(localStorage.getItem('theme') === 'dark');

  function toggleDark() {
    darkMode = !darkMode;
    // التطبيق على جذور الموقع (html) لضمان تغطية كافة الـ Layouts
    document.documentElement.classList.toggle('dark', darkMode);
    localStorage.setItem('theme', darkMode ? 'dark' : 'light');
  }
</script>

<div class="max-w-4xl mx-auto space-y-10 p-12 bg-white dark:bg-[#1a2535] rounded-[3rem] shadow-sm border border-slate-50 dark:border-slate-800">
  <h1 class="text-4xl font-black text-[#2a3c54] dark:text-white">إعدادات المنصة</h1>

  <div class="p-8 bg-slate-50 dark:bg-[#2a3c54] rounded-[2rem] flex justify-between items-center transition-colors">
    <div>
      <span class="text-xl font-black text-[#2a3c54] dark:text-white text-right block">مظهر المنصة (الوضع الداكن)</span>
      <p class="text-slate-400 font-bold mt-1 text-sm">تغيير ألوان الواجهة لتناسب الإضاءة المحيطة وتوفير الراحة للعين.</p>
    </div>
    
    <button onclick={toggleDark} class="px-10 py-3 rounded-2xl font-black transition-all shadow-md
      {darkMode ? 'bg-[#6b8cce] text-white' : 'bg-[#2a3c54] text-white'}">
      {darkMode ? 'تفعيل الوضع الفاتح' : 'تفعيل الوضع الداكن'}
    </button>
  </div>
</div>