<script>
  import { onMount } from "svelte";
  import api from "../lib/api";
  import { user, currentPage } from "../lib/stores";
  import { fade, slide, scale } from "svelte/transition";

  let { sessionId } = $props();

  let details = $state(null);
  let isLoading = $state(true);
  
  let newComment = $state("");
  let replyContent = $state("");
  let replyingTo = $state(null); 

  let sessionRate = $state(0);
  let teacherRate = $state(0);
  let hasRated = $state(false);

  let showModal = $state(false);
  let modalMsg = $state("");
  let modalIcon = $state("");

  onMount(async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await api.get(`/sessions/${sessionId}/details`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      details = res.data;
    } catch (e) {
      console.error(e);
    } finally {
      isLoading = false;
    }
  });

  function notify(msg, icon) {
    modalMsg = msg; modalIcon = icon; showModal = true;
  }

  function goBack() {
    if ($user?.roles?.some(r => r.role_name === 'teacher')) {
      currentPage.set('my_lectures');
    } else {
      currentPage.set('my_learning');
    }
  }

  async function submitComment(parentId = null) {
    const content = parentId ? replyContent : newComment;
    if (!content.trim()) return;
    try {
      const token = localStorage.getItem("token");
      await api.post("/comments/", {
        session_id: sessionId, content: content, parent_id: parentId
      }, { headers: { Authorization: `Bearer ${token}` } });
      newComment = ""; replyContent = ""; replyingTo = null;
      const res = await api.get(`/sessions/${sessionId}/details`);
      details = res.data;
    } catch (e) { notify("فشل إرسال التعليق", "❌"); }
  }

  
  async function submitRating() {
    if (sessionRate === 0 || teacherRate === 0) {
      notify("يرجى تقييم المحتوى وأداء المعلم معاً", "⚠️"); return;
    }
    try {
      const token = localStorage.getItem("token");
      await api.post("/ratings/", {
        session_id: Number(sessionId),
        teacher_id: Number(details.teacher_id),
        session_rate: sessionRate,
        teacher_rate: teacherRate
      }, { headers: { Authorization: `Bearer ${token}` } });
      
      hasRated = true;
      notify("شكراً لتقييمك! ", "✅");
      const res = await api.get(`/sessions/${sessionId}/details`);
      details = res.data;
    } catch (e) {
  
        if (e.response?.status === 400) { 
          notify(e.response.data.detail || "لقد قمت بالتقييم مسبقاً", "✅"); 
          hasRated = true; 
        } 

        else if (e.response?.status === 403) {
          notify(e.response.data.detail, "⚠️"); 
        }
     
        else {
          notify("حدث خطأ في الإرسال، يرجى المحاولة لاحقاً", "❌");
        }
    }
  }

  function addEmoji(emoji) {
    if (replyingTo) replyContent += emoji;
    else newComment += emoji;
  }
</script>

{#if showModal}
<div in:fade out:fade class="fixed inset-0 z-[9000] flex items-center justify-center p-4 bg-[#2a3c54]/60 backdrop-blur-sm" dir="rtl">
  <div in:scale={{duration: 300, start: 0.9}} class="bg-[#fafcff] rounded-[2.5rem] p-10 max-w-sm w-full text-center shadow-2xl border-t-8 border-[#6b8cce]">
    <div class="text-6xl mb-6">{modalIcon}</div>
    <p class="text-xl font-black text-[#2a3c54] leading-relaxed">{modalMsg}</p>
    <button onclick={() => showModal = false} class="mt-8 w-full py-4 bg-[#2a3c54] text-white rounded-2xl font-black hover:bg-[#4a6583] transition-colors shadow-lg">حسناً</button>
  </div>
</div>
{/if}

<div class="min-h-screen bg-slate-100 py-8 px-4 md:px-10 font-sans text-right pb-20" dir="rtl">
  
  <div class="max-w-5xl mx-auto mb-6 flex justify-start">
    <button onclick={goBack} class="flex items-center gap-2 bg-white px-6 py-3 rounded-2xl shadow-sm text-[#4a6583] font-black hover:bg-[#6b8cce] hover:text-white transition-all border border-slate-200">
      <span>رجوع للقائمة</span>
      <svg class="w-5 h-5 rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
    </button>
  </div>

  {#if isLoading}
    <div class="text-center mt-20 text-[#6b8cce] font-black animate-pulse text-xl">جاري تحميل مساحة النقاش...</div>
  {:else if details}
    <div class="max-w-5xl mx-auto space-y-8">
      
      <div class="bg-white rounded-[2.5rem] shadow-sm border border-slate-200 overflow-hidden flex flex-col">
        <div class="w-full h-64 md:h-80 bg-slate-200 overflow-hidden relative border-b border-slate-100">
          <img 
            src="http://localhost:8000/pics/{details.session.cover || details.session.display_cover}" 
            alt="Session Cover" 
            class="w-full h-full object-cover" 
          />
        </div>

        <div class="p-8 md:p-10 flex flex-col md:flex-row gap-8 items-start">
          <div class="flex-1">
            <h1 class="text-3xl font-black text-[#2a3c54] mb-2">{details.session.title}</h1>
            <p class="text-[#6b8cce] font-bold mb-4 text-lg">بإشراف الأستاذ: {details.teacher_name}</p>
            <p class="text-slate-600 leading-relaxed font-medium mb-8 text-lg">{details.session.description}</p>
            
            <div class="flex flex-wrap gap-4 items-center mt-6">
              <div class="bg-amber-50 text-amber-700 px-5 py-2.5 rounded-2xl text-base font-black border border-amber-100 shadow-sm flex items-center gap-2">
                 <span>⭐ التقييم العام:</span>
                 <span class="text-lg">{details.avg_session_rating > 0 ? details.avg_session_rating : 'جديد'}</span>
              </div>
              
              <span class="text-sm md:text-base font-bold text-slate-400">
                ({details.ratings_count} أصوات تم تسجيلها حالياً)
              </span>

              {#if details.session.meeting_link}
                <a href={details.session.meeting_link} target="_blank" class="mr-auto bg-[#2a3c54] text-white px-8 py-3.5 rounded-2xl font-black text-sm hover:scale-105 transition-all shadow-md">🔗 رابط الجلسة المباشرة</a>
              {/if}
            </div>
          </div>
        </div>
      </div>

      {#if !hasRated && $user?.roles?.some(r => r.role_name === 'student')}
        <div in:fade class="bg-gradient-to-br from-[#2a3c54] to-[#4a6583] p-8 rounded-[2.5rem] shadow-lg text-white border border-[#1e2a3b]">
          <h3 class="text-xl font-black mb-6">شاركنا رأيك حول الجلسة 🌟</h3>
          <div class="grid md:grid-cols-2 gap-8">
            <div>
              <p class="mb-3 font-bold text-slate-200">تقييم المحتوى العلمي:</p>
              <div class="flex gap-2">
                {#each [1, 2, 3, 4, 5] as star}
                  <button onclick={() => sessionRate = star} class="text-3xl hover:scale-125 transition-transform {sessionRate >= star ? 'text-amber-400' : 'text-white/20'}">★</button>
                {/each}
              </div>
            </div>
            <div>
              <p class="mb-3 font-bold text-slate-200">تقييم أداء المعلم:</p>
              <div class="flex gap-2">
                {#each [1, 2, 3, 4, 5] as star}
                  <button onclick={() => teacherRate = star} class="text-3xl hover:scale-125 transition-transform {teacherRate >= star ? 'text-amber-400' : 'text-white/20'}">★</button>
                {/each}
              </div>
            </div>
          </div>
          <button onclick={submitRating} class="mt-8 bg-emerald-500 text-white px-8 py-3 rounded-xl font-black shadow-md hover:bg-emerald-600 transition-all">إرسال التقييم النهائي</button>
        </div>
      {/if}

      <div class="bg-white p-8 rounded-[2.5rem] shadow-sm border border-slate-200">
        <h3 class="text-2xl font-black text-[#2a3c54] mb-8 border-r-8 border-[#6b8cce] pr-4">ساحة النقاش 💬</h3>
        
        <div class="mb-10 bg-slate-100 p-4 rounded-3xl border border-slate-300 focus-within:border-[#6b8cce] transition-colors shadow-inner">
          <textarea bind:value={newComment} placeholder="اترك تعليقاً للأستاذ أو للطلبة الذين بعدك..." class="w-full bg-transparent outline-none resize-none h-20 font-medium text-[#2a3c54] p-2 text-right"></textarea>
          <div class="flex justify-between items-center border-t border-slate-200 pt-3 mt-2">
            <div class="flex gap-2">
              <button onclick={() => addEmoji('👍')} class="text-xl hover:scale-110 transition-transform">👍</button>
              <button onclick={() => addEmoji('❤️')} class="text-xl hover:scale-110 transition-transform">❤️</button>
              <button onclick={() => addEmoji('🔥')} class="text-xl hover:scale-110 transition-transform">🔥</button>
              <button onclick={() => addEmoji('💡')} class="text-xl hover:scale-110 transition-transform">💡</button>
            </div>
            <div class="flex gap-2">
              <button onclick={() => newComment = ""} class="px-5 py-2 text-slate-500 font-bold hover:bg-slate-200 rounded-xl transition-colors text-sm">إلغاء</button>
              <button onclick={() => submitComment(null)} class="px-6 py-2 bg-[#6b8cce] text-white font-black rounded-xl hover:bg-[#4a6583] transition-colors shadow-md text-sm">نشر التعليق</button>
            </div>
          </div>
        </div>

        <div class="space-y-6">
          {#each details.comments as comment}
            <div class="flex gap-4">
              <div class="w-12 h-12 shrink-0 bg-white border border-slate-200 rounded-2xl overflow-hidden text-[#6b8cce] flex items-center justify-center font-black shadow-sm">
                {#if comment.user_image}
                  <img src={comment.user_image} alt="user" class="w-full h-full object-cover" />
                {:else}
                  {comment.user_name.charAt(0)}
                {/if}
              </div>
              
              <div class="flex-1 text-right">
                <div class="bg-slate-50 p-5 rounded-2xl rounded-tr-none border border-slate-200 shadow-sm">
                  <h4 class="font-black text-[#2a3c54] text-sm mb-1">{comment.user_name}</h4>
                  <p class="text-slate-600 text-sm leading-relaxed">{comment.content}</p>
                </div>
                <div class="flex gap-4 mt-2 px-2 justify-start flex-row-reverse">
                  <button onclick={() => replyingTo = replyingTo === comment.id ? null : comment.id} class="text-xs font-bold text-slate-500 hover:text-[#6b8cce] transition-colors">رد ↩️</button>
                  <span class="text-[10px] font-bold text-slate-400">{new Date(comment.created_at).toLocaleDateString('ar-IQ')}</span>
                </div>

                {#if replyingTo === comment.id}
                  <div in:slide class="mt-4 bg-white p-3 rounded-2xl border border-[#6b8cce]/40 flex gap-2 shadow-sm">
                    <input bind:value={replyContent} placeholder="اكتب ردك هنا..." class="flex-1 bg-transparent outline-none text-sm px-2 text-[#2a3c54] text-right" />
                    <button onclick={() => submitComment(comment.id)} class="bg-[#6b8cce] text-white px-4 py-1.5 rounded-xl font-bold text-xs hover:bg-[#4a6583]">إرسال</button>
                  </div>
                {/if}

                {#if comment.replies && comment.replies.length > 0}
                  <div class="mt-4 space-y-4 pr-6 border-r-2 border-slate-200">
                    {#each comment.replies as reply}
                      <div class="flex gap-3 flex-row-reverse text-right">
                        <div class="w-8 h-8 shrink-0 bg-slate-200 rounded-xl overflow-hidden flex items-center justify-center font-bold text-slate-500 text-xs border border-slate-300">
                          {#if reply.user_image}
                            <img src={reply.user_image} alt="user" class="w-full h-full object-cover"/>
                          {:else}
                            {reply.user_name.charAt(0)}
                          {/if}
                        </div>
                        <div class="flex-1">
                          <div class="bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
                            <h4 class="font-bold text-[#2a3c54] text-xs mb-1">{reply.user_name}</h4>
                            <p class="text-slate-600 text-xs">{reply.content}</p>
                          </div>
                        </div>
                      </div>
                    {/each}
                  </div>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  textarea::placeholder {
    text-align: right;
  }
</style>