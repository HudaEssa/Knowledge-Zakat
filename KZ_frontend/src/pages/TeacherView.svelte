<script>
    import { onMount } from 'svelte';
    import api from '../lib/api';
    import { fade, scale, slide } from 'svelte/transition';
    import { user, currentPage, selectedTeacherId } from '../lib/stores';

    let teacher = $state(null);
    let teacherSessions = $state([]);
    let isLoading = $state(true);
    let commentPages = $state({}); 

    onMount(async () => {
        const tId = $selectedTeacherId;
        if (!tId) return currentPage.set('home');

        try {
            const [tRes, sRes] = await Promise.all([
                api.get(`/users/${tId}`),
                api.get(`/sessions/?teacher_id=${tId}`)
            ]);
            teacher = tRes.data;
            teacherSessions = sRes.data;
            teacherSessions.forEach(s => commentPages[s.id] = 0);
        } catch (e) { console.error(e); }
        finally { isLoading = false; }
    });

    async function enroll(sessionId) {
        try {
            const token = localStorage.getItem("token");
            if (!token) return alert("يرجى تسجيل الدخول أولاً للمشاركة في هذه المحاضرة.");
            await api.post('/enrollments/', { session_id: sessionId }, {
                headers: { Authorization: `Bearer ${token}` }
            });
            alert("تم إرسال طلب انضمامك بنجاح! سيصلك تنبيه عند موافقة المعلم.");
        } catch (e) { alert("حدث خطأ في التسجيل، ربما أنت مشترك بالفعل."); }
    }

    function goBack() {
        currentPage.set('home');
    }
</script>

<div class="min-h-screen bg-slate-50 text-right pb-20 font-sans" dir="rtl">
    {#if isLoading}
        <div class="flex flex-col items-center justify-center h-[80vh] gap-6">
            <div class="w-16 h-16 border-8 border-[#6b8cce] border-t-transparent rounded-full animate-spin"></div>
            <p class="font-black text-[#6b8cce] text-2xl animate-pulse italic">جاري تحميل السيرة العلمية...</p>
        </div>
    {:else if teacher}
        <header class="relative h-[500px] w-full shadow-2xl overflow-hidden bg-[#2a3c54]">
            <img src={teacher.profile_image ? `data:image/jpeg;base64,${teacher.profile_image}` : 'https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=1200'} 
                 class="w-full h-full object-cover brightness-[0.4] blur-[2px] scale-105" alt="bg" />
            <div class="absolute inset-0 bg-gradient-to-t from-[#1e2a3b] via-transparent to-black/30"></div>
            
            <div class="absolute inset-0 flex flex-col justify-end items-center pb-12 px-6">
                <div class="w-48 h-48 rounded-[3.5rem] border-[10px] border-white/10 backdrop-blur-md shadow-2xl overflow-hidden bg-white/20 mb-6">
                    <img src={teacher.profile_image ? `data:image/jpeg;base64,${teacher.profile_image}` : `https://ui-avatars.com/api/?name=${teacher.firstname}&size=256`} 
                         class="w-full h-full object-cover" alt="teacher" />
                </div>
                <h1 class="text-6xl font-black text-white drop-shadow-2xl mb-4">{teacher.firstname} {teacher.lastname}</h1>
                <p class="text-2xl text-[#6b8cce] font-bold max-w-3xl text-center italic">{teacher.bio || 'معلم خبير مكرس لنشر المعرفة في مجتمع زكاة العلم.'}</p>
                
                <button onclick={goBack} class="absolute top-10 right-10 bg-white/10 hover:bg-white/20 text-white px-8 py-3 rounded-2xl font-black border border-white/20 backdrop-blur transition-all">
                   ← العودة للرئيسية
                </button>
            </div>
        </header>

        <main class="max-w-6xl mx-auto px-6 -mt-10 relative z-10 space-y-16">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="bg-white p-8 rounded-[2.5rem] shadow-lg text-center border-t-4 border-[#6b8cce]">
                    <span class="block text-4xl font-black text-[#2a3c54] mb-2">{teacherSessions.length}</span>
                    <span class="text-slate-400 font-bold">دورة علمية</span>
                </div>
                <div class="bg-white p-8 rounded-[2.5rem] shadow-lg text-center border-t-4 border-emerald-400">
                    <span class="block text-4xl font-black text-[#2a3c54] mb-2">⭐ {teacher.avg_rating || '5.0'}</span>
                    <span class="text-slate-400 font-bold">تقييم الطلاب</span>
                </div>
                <div class="bg-white p-8 rounded-[2.5rem] shadow-lg text-center border-t-4 border-amber-400">
                    <span class="block text-4xl font-black text-[#2a3c54] mb-2">✅</span>
                    <span class="text-slate-400 font-bold">معلم موثق</span>
                </div>
            </div>

            <div class="space-y-10">
                <h2 class="text-4xl font-black text-[#2a3c54] border-r-8 border-[#6b8cce] pr-6">الدورات والمحاضرات المتاحة</h2>
                
                <div class="grid grid-cols-1 gap-12">
                    {#each teacherSessions as session}
                        <div class="bg-white rounded-[4rem] shadow-xl border border-slate-50 overflow-hidden flex flex-col lg:flex-row hover:shadow-2xl transition-all duration-500">
                            <div class="lg:w-[450px] h-80 lg:h-auto bg-slate-200 relative overflow-hidden">
                                <img src={`http://localhost:8000/pics/${session.cover_image_url}`} class="w-full h-full object-cover transition-transform duration-700 hover:scale-110" alt="cover" />
                                <div class="absolute bottom-6 left-6 bg-white/95 px-6 py-2 rounded-2xl text-xs font-black text-[#2a3c54] shadow-2xl">
                                    ⭐ {session.avg_rating || 'جديد'}
                                </div>
                            </div>

                            <div class="flex-1 p-12 flex flex-col justify-between space-y-8">
                                <div class="space-y-6">
                                    <div class="flex justify-between items-start">
                                        <h3 class="text-3xl font-black text-[#2a3c54]">{session.title}</h3>
                                        <button onclick={() => enroll(session.id)} class="bg-[#2a3c54] text-white px-10 py-4 rounded-2xl font-black hover:bg-emerald-500 hover:scale-105 transition-all shadow-xl">شارك في الدورة</button>
                                    </div>
                                    <p class="text-slate-500 font-medium text-lg leading-relaxed">{session.description}</p>
                                    
                                    <div class="bg-[#eff3fa]/50 p-6 rounded-[2.5rem] border-2 border-dashed border-[#6b8cce]/20">
                                        <h4 class="font-black text-[#2a3c54] text-sm mb-4">🗓️ مواعيد المحاضرات المباشرة:</h4>
                                        <div class="flex flex-wrap gap-3">
                                            {#each (session.lecture_days || ['السبت', 'الإثنين', 'الأربعاء']) as day}
                                                <span class="bg-white border border-slate-100 px-6 py-2.5 rounded-2xl text-xs font-black text-[#6b8cce] shadow-sm italic">
                                                    {day} - 08:30 مساءً
                                                </span>
                                            {/each}
                                        </div>
                                    </div>
                                </div>

                                <div class="pt-8 border-t border-slate-100">
                                    <div class="flex justify-between items-center mb-6 px-2">
                                        <h4 class="font-black text-slate-400 text-sm">آراء طلاب الدورة ({session.comments?.length || 0})</h4>
                                        {#if session.comments?.length > 3}
                                            <div class="flex gap-4">
                                                <button disabled={commentPages[session.id] === 0} 
                                                        onclick={() => commentPages[session.id]--} 
                                                        class="text-xs font-black text-slate-400 hover:text-[#2a3c54] disabled:opacity-10 transition-colors">← السابق</button>
                                                <button disabled={(commentPages[session.id] + 1) * 3 >= session.comments.length} 
                                                        onclick={() => commentPages[session.id]++} 
                                                        class="text-xs font-black text-slate-400 hover:text-[#2a3c54] disabled:opacity-10 transition-colors">التالي →</button>
                                            </div>
                                        {/if}
                                    </div>

                                    <div class="space-y-4">
                                        {#each (session.comments || []).slice(commentPages[session.id] * 3, (commentPages[session.id] + 1) * 3) as comment}
                                            <div in:slide class="bg-slate-50 p-6 rounded-[2rem] flex gap-5 border border-white group/comment">
                                                <div class="w-12 h-12 rounded-2xl bg-white text-[#6b8cce] flex items-center justify-center font-black shadow-sm shrink-0 border border-slate-100 group-hover/comment:bg-[#2a3c54] group-hover/comment:text-white transition-colors">
                                                    {comment.user_name.charAt(0)}
                                                </div>
                                                <div class="flex-1">
                                                    <p class="text-sm font-black text-[#2a3c54] mb-1">{comment.user_name}</p>
                                                    <p class="text-xs text-slate-500 font-medium leading-relaxed italic">{comment.content}</p>
                                                </div>
                                            </div>
                                        {/each}
                                    </div>
                                </div>
                            </div>
                        </div>
                    {/each}
                </div>
            </div>
        </main>
    {/if}
</div>