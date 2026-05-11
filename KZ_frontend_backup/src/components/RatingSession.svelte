<script>
  import api from "../lib/api";
  import { fade, scale } from "svelte/transition";
  
  let { sessionId, onRatingSuccess } = $props(); // Svelte 5 Props
  
  let rate = $state(0);
  let comment = $state("");
  let isSubmitting = $state(false);
  let showFeedback = $state(false);
  let message = $state("");

  async function submitRating() {
    if (rate === 0) return;
    isSubmitting = true;
    try {
      await api.post("/ratings/", { session_id: sessionId, rate, comment });
      message = "شكراً لك! تم إرسال تقييمك بنجاح.";
      showFeedback = true;
      if (onRatingSuccess) onRatingSuccess();
    } catch (e) {
      message = e.response?.data?.detail || "عذراً، فشل إرسال التقييم.";
      showFeedback = true;
    } finally {
      isSubmitting = false;
    }
  }
</script>

<div class="bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-sm">
  <h3 class="text-xl font-black text-[#2a3c54] mb-6">ما هو تقييمك لهذه الجلسة؟</h3>
  
  <div class="flex gap-3 mb-8">
    {#each [1, 2, 3, 4, 5] as star}
      <button 
        onclick={() => rate = star}
        class="text-4xl transition-transform hover:scale-125 {rate >= star ? 'text-amber-400' : 'text-slate-200'}">
        {rate >= star ? '★' : '☆'}
      </button>
    {/each}
  </div>

  <textarea 
    bind:value={comment}
    placeholder="اكتب ملاحظاتك للأستاذ هنا (اختياري)..."
    class="w-full p-5 bg-slate-50 rounded-2xl border-2 border-transparent focus:border-[#6b8cce] outline-none font-bold text-sm h-32 resize-none transition-all"
  ></textarea>

  <button 
    onclick={submitRating}
    disabled={rate === 0 || isSubmitting}
    class="w-full mt-6 py-4 bg-[#2a3c54] text-white rounded-2xl font-black shadow-lg disabled:opacity-30 transition-all">
    {isSubmitting ? 'جاري الإرسال...' : 'إرسال التقييم العلمي ✅'}
  </button>
</div>

{#if showFeedback}
  <div in:fade class="fixed inset-0 z-[9000] flex items-center justify-center p-4 bg-[#2a3c54]/40 backdrop-blur-md">
    <div in:scale class="bg-white rounded-[2rem] p-10 max-w-sm w-full text-center">
      <div class="text-5xl mb-4">✨</div>
      <p class="font-black text-[#2a3c54] mb-6">{message}</p>
      <button onclick={() => showFeedback = false} class="w-full py-4 bg-[#2a3c54] text-white rounded-xl font-black">حسناً</button>
    </div>
  </div>
{/if}