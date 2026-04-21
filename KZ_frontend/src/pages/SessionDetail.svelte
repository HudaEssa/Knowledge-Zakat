<script>
  export let session; // نمرر بيانات الجلسة
  import { currentPage } from "../lib/stores";

  // محاكاة لزيادة المشاهدات +1 لليوزر الواحد
  let views = session.views || 45;
  let hasViewed = false;
  if (!hasViewed) { views++; hasViewed = true; }
</script>

<div class="max-w-5xl mx-auto space-y-8 text-right" dir="rtl">
  <button on:click={() => currentPage.set('home')} class="text-blue-600 font-bold text-lg">← رجوع للجلسات</button>

  <div class="bg-white p-10 rounded-[3rem] shadow-xl border border-slate-50">
    <div class="flex justify-between items-start border-b pb-8 mb-8">
      <div>
        <span class="bg-blue-100 text-blue-700 px-4 py-1 rounded-full font-bold text-sm">قسم: {session.category}</span>
        <h1 class="text-4xl font-black text-slate-800 mt-4">{session.title}</h1>
      </div>
      <div class="text-left">
        <div class="text-2xl">⭐ {session.rating || '4.8'}</div>
        <div class="text-slate-500 font-bold">👁️ {views} مشاهدة</div>
      </div>
    </div>

    <div class="flex items-center gap-6 p-6 bg-slate-50 rounded-[2rem] mb-8">
      <img src={session.teacher_img || 'teacher_default.png'} class="w-20 h-20 rounded-full border-4 border-white shadow-sm" alt="" />
      <div>
        <h3 class="font-black text-xl text-slate-800">الأستاذ: {session.teacher_name}</h3>
        <p class="text-slate-500 text-sm font-medium">خبير في تكنولوجيا المعلومات وباحث أكاديمي.</p>
      </div>
    </div>

    <div class="prose prose-lg max-w-none text-slate-700 font-medium">
        {session.content}
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-10">
      <button class="bg-blue-900 text-white py-5 rounded-2xl font-black text-xl">انضمام للجلسة الآن 🚀</button>
      <button class="bg-slate-100 text-slate-700 py-5 rounded-2xl font-black text-xl">⏰ ذكرني لاحقاً</button>
    </div>
  </div>
</div>