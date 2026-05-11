<script>
    import { user } from "../lib/stores";
</script>

<div class="max-w-5xl mx-auto space-y-6">
    <div class="bg-white p-8 rounded-[2rem] shadow-sm border border-gray-100 text-center">
        <div class="w-20 h-20 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4 text-4xl">
            🔖
        </div>
        <h2 class="text-3xl font-bold text-blue-900 mb-2">جلساتي المشتركة</h2>
        <p class="text-gray-500 max-w-lg mx-auto">
            هنا ستظهر جميع الجلسات والمحاضرات التي قمت بالتسجيل بها.
        </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 opacity-50 pointer-events-none grayscale">
         <div class="bg-white p-6 rounded-2xl border border-gray-200">
            <h3 class="font-bold text-gray-800">مقدمة في الذكاء الاصطناعي</h3>
            <p class="text-sm text-gray-500">مشترك منذ يومين</p>
         </div>
         <div class="p-4 text-center col-span-2 text-gray-400 font-medium">
             (سيتم تفعيل هذه القائمة قريباً عند ربط قاعدة البيانات)
         </div>
    </div>
</div>