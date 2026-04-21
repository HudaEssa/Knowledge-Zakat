<script>
    import { user, currentPage } from "../lib/stores"; // 👈 ضفنا currentPage هنا
    import api from "../lib/api";
    import { onMount } from "svelte";
    import { fade, scale } from "svelte/transition";

    let showRatingModal = $state(false);
    let activeSessionId = $state(null);

    function openRatingModal(id) {
        activeSessionId = id;
        showRatingModal = true;
    }

    let enrolledSessions = $state([]);
    let isLoading = $state(true);

    // --- متغيرات المودال الاحترافي ---
    let showStatusModal = $state(false);
    let modalType = $state("info"); 
    let modalMessage = $state("");

    async function fetchMyEnrollments() {
        try {
            // نستخدم الإندبوينت اللي يسحب جلساتي المشتركة 
            const res = await api.get('/me/enrollments');
            enrolledSessions = res.data;
        } catch (err) {
            console.error("فشل جلب الجلسات");
        } finally {
            isLoading = false;
        }
    }

    function handleJoinSession(link) {
        if (!link) {
            modalType = "info";
            modalMessage = "عذراً، الأستاذ لم يقم بإرفاق رابط لهذه الجلسة بعد. يرجى المحاولة لاحقاً.";
            showStatusModal = true;
        } else {
            window.open(link, '_blank');
        }
    }

    // 👈 الدالة الجديدة للانتقال إلى صفحة تفاصيل المحاضرة
    function navigateToDetails(sessionId) {
        currentPage.set({ 
            name: 'session_details', 
            data: { sessionId: sessionId } 
        });
    }

    onMount(fetchMyEnrollments);
</script>

{#if showStatusModal}
<div in:fade out:fade class="fixed inset-0 z-[5000] flex items-center justify-center p-4 bg-[#2a3c54]/40 backdrop-blur-md">
  <div in:scale={{ duration: 250, start: 0.85 }} class="bg-white rounded-[2.5rem] shadow-2xl p-10 max-w-sm w-full text-center space-y-6 border border-white">
    <div class="w-20 h-20 rounded-full flex items-center justify-center mx-auto text-4xl font-black bg-[#eff3fa] text-[#2a3c54]">
      !
    </div>
    <div class="space-y-2">
      <h3 class="text-2xl font-black text-[#2a3c54]">تنبيه</h3>
      <p class="text-sm font-bold text-slate-400 leading-relaxed italic">{modalMessage}</p>
    </div>
    <button onclick={() => showStatusModal = false} class="w-full py-4 bg-[#2a3c54] text-white rounded-2xl font-black text-lg hover:scale-105 transition-all shadow-lg active:scale-95">
      حسناً
    </button>
  </div>
</div>
{/if}

<div class="max-w-5xl mx-auto space-y-6 text-right" dir="rtl">
    <div class="bg-white p-10 rounded-[2.5rem] shadow-sm border border-gray-100 text-center">
        <div class="w-20 h-20 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4 text-4xl">🔖</div>
        <h2 class="text-3xl font-black text-[#2a3c54] mb-2">جلساتي المشتركة</h2>
        <p class="text-gray-400 font-bold max-w-lg mx-auto italic">هنا تظهر جميع الجلسات التي قمت بالتسجيل فيها وتم قبولك.</p>
    </div>

    {#if isLoading}
        <div class="py-20 text-center text-slate-300 font-black animate-pulse">جاري جلب قائمة دروسك...</div>
    {:else if enrolledSessions.length === 0}
        <div class="py-20 text-center bg-white rounded-[2.5rem] border-2 border-dashed border-slate-100">
            <p class="text-slate-400 font-bold">لم تشترك في أي جلسة بعد..</p>
        </div>
    {:else}
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            {#each enrolledSessions as item}
                <div in:fade class="bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-sm hover:shadow-xl transition-all group">
                    <div class="flex justify-between items-start mb-4">
                        <span class="px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest
                            {item.status === 'approved' ? 'bg-green-50 text-green-600' : 'bg-orange-50 text-orange-600'}">
                            {item.status === 'approved' ? 'مقبول' : 'قيد الانتظار'}
                        </span>
                        <div class="text-left">
                            <p class="text-[10px] font-black text-slate-300 uppercase tracking-tighter">Instructor</p>
                            <button 
                                onclick={() => currentPage.set({ name: 'view_teacher', data: { teacherId: item.teacher_id } })} 
                                class="text-xs font-black text-[#2a3c54] hover:text-[#6b8cce] hover:underline transition-all cursor-pointer"
                            >
                                {item.teacher_name}
                            </button>
                        </div>
                    </div>

                    <h3 class="text-xl font-black text-[#2a3c54] mb-1 group-hover:text-[#6b8cce] transition-colors">{item.lecture_title}</h3>
                    <p class="text-sm font-bold text-slate-400 mb-6 border-b pb-4 border-slate-50">{item.session_title}</p>

                    <div class="flex items-center justify-between">
                        <div class="space-y-1">
                            <div class="flex gap-4 text-[11px] font-bold text-slate-500">
                                <span>📅 {item.date}</span>
                                <span>⏰ {item.time}</span>
                            </div>
                        </div>

                        <div class="flex gap-2">
                            <button 
                                onclick={() => navigateToDetails(item.session_id || item.id)}
                                class="px-5 py-3 bg-[#eff3fa] text-[#2a3c54] rounded-2xl font-black text-xs hover:bg-[#6b8cce] hover:text-white transition-all shadow-sm"
                                title="عرض التعليقات والتقييمات"
                            >
                                التفاصيل 
                            </button>

                            
                        </div>

                    </div>
                </div>
            {/each}
        </div>
    {/if}
</div>