<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, scale, slide } from 'svelte/transition';
  import api from '../lib/api';
  import { notify } from '../lib/notifications';
  import type { EnrollmentStatus } from '../lib/types';
  import { 
    Check, 
    X, 
    BookOpen, 
    Calendar, 
    ScrollText, 
    CheckCircle, 
    AlertTriangle, 
    XCircle,
    RotateCcw,
    ChevronRight,
    ChevronLeft
  } from 'lucide-svelte';

  // ---- Local types --------------------------------------------------------
  interface PendingRequest {
    user_id: number;
    session_id: number;
    student_name: string;
    session_title: string;
    date: string | null;
    isProcessing: boolean;
    processedMessage: 'success' | 'rejected' | 'error' | null;
  }

  interface HistoryRequest {
    user_id: number;
    session_id: number;
    student_name: string;
    session_title: string;
    date: string | null;
    status: EnrollmentStatus;
    isProcessing?: boolean;
  }

  // ---- State --------------------------------------------------------------
  let pendingRequests = $state<PendingRequest[]>([]);
  let historyRequests = $state<HistoryRequest[]>([]);
  let isLoading = $state(true);

  // حالة نافذة التأكيد
  let confirmActionData = $state<{ req: PendingRequest; status: EnrollmentStatus } | null>(null);

  // ---- Pagination State ---------------------------------------------------
  let currentPage = $state(1);
  const pageSize = 6;
  
  let totalPages = $derived(Math.ceil(historyRequests.length / pageSize));
  let paginatedHistory = $derived(
    historyRequests.slice((currentPage - 1) * pageSize, currentPage * pageSize)
  );

  // ---- Helpers ------------------------------------------------------------
  // دالة لترتيب وعرض التاريخ بشكل مقروء
  function formatDateTime(isoStr: string | null | undefined): string {
    if (!isoStr) return 'موعد غير محدد';
    try {
      const d = new Date(isoStr);
      if (isNaN(d.getTime())) return 'موعد غير محدد';
      return new Intl.DateTimeFormat('ar-IQ', { 
        weekday: 'long', 
        day: 'numeric', 
        month: 'short', 
        hour: '2-digit', 
        minute: '2-digit' 
      }).format(d);
    } catch {
      return 'موعد غير محدد';
    }
  }

  // ---- Data load ----------------------------------------------------------
  onMount(async () => {
    try {
      const [pendingRes, historyRes] = await Promise.all([
        api.get<any[]>('/teacher/enrollments/pending'),
        api.get<any[]>('/teacher/enrollments/history'),
      ]);

      // ربط الحقل session_date القادم من السيرفر بالحقل date
      pendingRequests = (pendingRes.data ?? []).map((r) => ({
        ...r,
        date: r.session_date || r.date || null,
        isProcessing: false,
        processedMessage: null,
      }));
      
      historyRequests = (historyRes.data ?? []).map(r => ({
        ...r,
        date: r.session_date || r.date || null,
        isProcessing: false
      }));
    } catch {
      notify.error('تعذّر جلب طلبات الانضمام');
    } finally {
      isLoading = false;
    }
  });

  // ---- Actions ------------------------------------------------------------
  async function executeConfirmedAction(): Promise<void> {
    if (!confirmActionData) return;
    const { req, status } = confirmActionData;
    confirmActionData = null;

    if (req.isProcessing) return;
    req.isProcessing = true;

    try {
      await api.patch('/enrollments/update', {
        user_id: req.user_id,
        session_id: req.session_id,
        status: status,
      });

      req.processedMessage = status === 'approved' ? 'success' : 'rejected';

      setTimeout(() => {
        pendingRequests = pendingRequests.filter((r) => r !== req);
        historyRequests = [
          {
            user_id: req.user_id,
            session_id: req.session_id,
            student_name: req.student_name,
            session_title: req.session_title,
            date: req.date,
            status: status,
            isProcessing: false
          },
          ...historyRequests,
        ];
        currentPage = 1;
      }, 1500);
    } catch {
      req.processedMessage = 'error';
      req.isProcessing = false;
      setTimeout(() => (req.processedMessage = null), 2500);
    }
  }

  async function undoAction(hReq: HistoryRequest): Promise<void> {
    if (hReq.isProcessing) return;
    hReq.isProcessing = true;

    try {
      await api.patch('/enrollments/update', {
        user_id: hReq.user_id,
        session_id: hReq.session_id,
        status: 'pending',
      });

      historyRequests = historyRequests.filter(
        (r) => !(r.user_id === hReq.user_id && r.session_id === hReq.session_id)
      );

      pendingRequests = [
        {
          user_id: hReq.user_id,
          session_id: hReq.session_id,
          student_name: hReq.student_name,
          session_title: hReq.session_title,
          date: hReq.date,
          isProcessing: false,
          processedMessage: null,
        },
        ...pendingRequests,
      ];

      if (paginatedHistory.length === 0 && currentPage > 1) {
        currentPage--;
      }

      notify.success('تم التراجع عن القرار، الطلب الآن في قائمة الانتظار');
    } catch {
      notify.error('تعذّر التراجع عن القرار، يرجى المحاولة لاحقاً');
      hReq.isProcessing = false;
    }
  }

  function goToPage(p: number) {
    if (p >= 1 && p <= totalPages) {
      currentPage = p;
      const el = document.getElementById('history-section');
      el?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }
</script>

{#if confirmActionData}
  <div
    in:fade
    out:fade
    class="fixed inset-0 z-[8000] flex items-center justify-center p-4 bg-[#2a3c54]/60 backdrop-blur-sm"
    dir="rtl"
    onclick={(e) => {
      if (e.target === e.currentTarget) confirmActionData = null;
    }}
    role="presentation"
  >
    <div
      in:scale={{ start: 0.92, duration: 250 }}
      class="bg-white rounded-[2.5rem] p-8 md:p-10 max-w-md w-full text-center shadow-2xl"
    >
      <div
        class="w-16 h-16 md:w-20 md:h-20 rounded-full flex items-center justify-center mx-auto mb-6
        {confirmActionData.status === 'approved' ? 'bg-emerald-50 text-emerald-500' : 'bg-red-50 text-red-500'}"
      >
        {#if confirmActionData.status === 'approved'}
          <CheckCircle size={40} strokeWidth={2} />
        {:else}
          <XCircle size={40} strokeWidth={2} />
        {/if}
      </div>
      <h3 class="text-xl md:text-2xl font-black text-[#2a3c54] mb-2">تأكيد القرار</h3>
      <p class="text-slate-500 font-bold mb-8 text-sm md:text-base leading-relaxed">
        هل أنت متأكد من
        {confirmActionData.status === 'approved' ? 'قبول' : 'رفض'}
        انضمام الطالب <span class="text-[#2a3c54]">{confirmActionData.req.student_name}</span>
        في دورة <span class="text-[#2a3c54]">"{confirmActionData.req.session_title}"</span>؟
      </p>
      <div class="flex gap-3 md:gap-4">
        <button
          onclick={executeConfirmedAction}
          class="flex-1 py-3 md:py-4 text-white rounded-2xl font-black text-sm shadow-lg transition-all flex items-center justify-center gap-2
          {confirmActionData.status === 'approved' ? 'bg-emerald-500 hover:bg-emerald-600' : 'bg-red-500 hover:bg-red-600'}"
        >
          تأكيد القرار
        </button>
        <button
          onclick={() => (confirmActionData = null)}
          class="flex-1 py-3 md:py-4 bg-slate-100 text-slate-500 rounded-2xl font-black text-sm hover:bg-slate-200 transition-colors"
        >
          إلغاء وتراجع
        </button>
      </div>
    </div>
  </div>
{/if}

<div class="space-y-10 md:space-y-12 text-right pb-12 md:pb-20" dir="rtl">
  <section>
    <h1
      class="text-2xl md:text-3xl font-black text-[#2a3c54] border-r-4 md:border-r-8 border-[#6b8cce] pr-3 md:pr-4 mb-6 md:mb-8"
    >
      طلبات الانضمام الجديدة
    </h1>

    {#if isLoading}
      <div class="space-y-4">
        {#each Array(2) as _, i (i)}
          <div class="bg-white p-6 md:p-8 rounded-[2rem] border border-slate-50 flex justify-between items-center gap-4">
            <div class="flex items-center gap-4 flex-1">
              <div class="w-14 h-14 bg-slate-100 rounded-2xl animate-pulse"></div>
              <div class="flex-1 space-y-2">
                <div class="h-5 bg-slate-100 rounded animate-pulse w-2/3"></div>
                <div class="h-4 bg-slate-100 rounded animate-pulse w-1/2"></div>
              </div>
            </div>
            <div class="flex gap-3">
              <div class="h-12 w-24 bg-slate-100 rounded-2xl animate-pulse"></div>
            </div>
          </div>
        {/each}
      </div>
    {:else if pendingRequests.length === 0}
      <div in:fade class="py-16 text-center text-slate-400 font-black text-lg border-4 border-dashed border-white rounded-[2.5rem] bg-white/50">
        <div class="flex justify-center mb-4 text-slate-300">
          <ScrollText size={56} strokeWidth={1.5} />
        </div>
        لا توجد طلبات انضمام جديدة حالياً
      </div>
    {:else}
      <div class="grid grid-cols-1 gap-4 md:gap-6">
        {#each pendingRequests as req (req.user_id + '_' + req.session_id)}
          <div
            class="group bg-white p-6 md:p-8 rounded-[2rem] md:rounded-[3.5rem] shadow-sm border border-slate-50 flex flex-col md:flex-row justify-between items-center gap-4 transition-all hover:shadow-2xl hover:scale-[1.005]"
            in:scale={{ duration: 250 }}
          >
            <div class="flex items-center gap-4 md:gap-6 text-right w-full">
              <div
                class="w-14 h-14 md:w-16 md:h-16 bg-[#eff3fa] rounded-[1.25rem] md:rounded-[1.5rem] flex items-center justify-center text-xl md:text-2xl font-black text-[#6b8cce] shadow-inner group-hover:bg-[#2a3c54] group-hover:text-white transition-colors shrink-0"
              >
                {req.student_name.charAt(0).toUpperCase()}
              </div>
              <div class="flex-1 min-w-0">
                <p class="font-black text-[#2a3c54] text-lg md:text-xl line-clamp-1 mb-2">{req.student_name}</p>
                <div class="flex flex-wrap gap-2">
                  <span class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 text-[#6b8cce] rounded-xl text-xs md:text-sm font-bold border border-blue-100">
                    <BookOpen size={14} strokeWidth={2.5} /> {req.session_title}
                  </span>
                  <span class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-50 text-slate-500 rounded-xl text-xs md:text-sm font-bold border border-slate-200">
                    <Calendar size={14} strokeWidth={2.5} /> {formatDateTime(req.date)}
                  </span>
                </div>
              </div>
            </div>

            <div class="flex items-center min-w-[260px] justify-end shrink-0 mt-4 md:mt-0">
              {#if req.processedMessage}
                <div
                  in:scale
                  class="px-6 md:px-8 py-3 rounded-2xl font-black text-xs md:text-sm border transition-all flex items-center justify-center gap-2
                  {req.processedMessage === 'success' ? 'bg-emerald-50 text-emerald-600 border-emerald-100' : 
                   req.processedMessage === 'error' ? 'bg-amber-50 text-amber-600 border-amber-100' : 
                   'bg-red-50 text-red-600 border-red-100'}"
                >
                  {#if req.processedMessage === 'success'}<CheckCircle size={18} /> تم قبول الطالب بنجاح
                  {:else if req.processedMessage === 'error'}<AlertTriangle size={18} /> تعذّر تنفيذ الإجراء
                  {:else}<XCircle size={18} /> تم رفض الطلب{/if}
                </div>
              {:else}
                <div class="flex gap-3 md:gap-4 w-full md:w-auto" in:fade>
                  <button
                    onclick={() => (confirmActionData = { req, status: 'approved' })}
                    disabled={req.isProcessing}
                    class="flex-1 md:flex-none flex items-center justify-center gap-2 px-6 md:px-8 py-3 md:py-4 bg-emerald-500 text-white rounded-[1.25rem] font-black text-xs hover:bg-emerald-600 transition-all shadow-lg active:scale-90 disabled:opacity-40"
                  >
                    موافقة <Check size={16} strokeWidth={3} />
                  </button>
                  <button
                    onclick={() => (confirmActionData = { req, status: 'rejected' })}
                    disabled={req.isProcessing}
                    class="flex-1 md:flex-none flex items-center justify-center gap-2 px-6 md:px-8 py-3 md:py-4 bg-white border-2 border-red-100 text-red-500 rounded-[1.25rem] font-black text-xs hover:bg-red-500 hover:text-white transition-all active:scale-90 disabled:opacity-40"
                  >
                    رفض <X size={16} strokeWidth={3} />
                  </button>
                </div>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </section>

  {#if !isLoading && historyRequests.length > 0}
    <section id="history-section" in:fade class="pt-6 md:pt-8 border-t-2 border-dashed border-slate-200">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-xl md:text-2xl font-black text-slate-400">
          سجل القرارات السابقة
        </h2>
        <span class="bg-slate-100 text-slate-400 px-4 py-1.5 rounded-full text-[10px] font-black">
          إجمالي العمليات: {historyRequests.length}
        </span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        {#each paginatedHistory as hReq (hReq.user_id + '_h_' + hReq.session_id)}
          <div
            class="bg-white/80 p-5 rounded-[2rem] border border-slate-100 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 hover:bg-white hover:shadow-md transition-all"
          >
            <div class="flex items-center gap-4 min-w-0 w-full sm:w-auto">
              <div class="w-12 h-12 bg-slate-100 rounded-[1rem] flex items-center justify-center text-lg font-black text-slate-400 shadow-inner shrink-0">
                {hReq.student_name.charAt(0).toUpperCase()}
              </div>
              <div class="min-w-0 flex-1">
                <p class="font-black text-[#2a3c54] text-sm md:text-base line-clamp-1 mb-1.5">{hReq.student_name}</p>
                <div class="flex flex-wrap gap-1.5">
                  <span class="inline-flex items-center gap-1 px-2 py-1 bg-slate-50 text-slate-500 rounded-md text-[10px] md:text-xs font-bold border border-slate-200">
                    <BookOpen size={10} strokeWidth={2.5} /> {hReq.session_title}
                  </span>
                  <span class="inline-flex items-center gap-1 px-2 py-1 bg-slate-50 text-slate-500 rounded-md text-[10px] md:text-xs font-bold border border-slate-200">
                    <Calendar size={10} strokeWidth={2.5} /> {formatDateTime(hReq.date)}
                  </span>
                </div>
              </div>
            </div>

            <div class="shrink-0 flex sm:flex-col items-center sm:items-end gap-3 sm:gap-2 w-full sm:w-auto justify-between sm:justify-start border-t sm:border-0 pt-3 sm:pt-0 border-slate-100 mt-2 sm:mt-0">
              {#if hReq.status === 'approved'}
                <span class="flex items-center justify-center gap-1.5 px-4 py-2 bg-emerald-50 text-emerald-600 rounded-xl font-black text-xs border border-emerald-100 w-fit sm:w-full">
                  مقبول <Check size={14} strokeWidth={3} />
                </span>
              {:else}
                <span class="flex items-center justify-center gap-1.5 px-4 py-2 bg-red-50 text-red-500 rounded-xl font-black text-xs border border-red-100 w-fit sm:w-full">
                  مرفوض <X size={14} strokeWidth={3} />
                </span>
              {/if}

              <button
                onclick={() => undoAction(hReq)}
                disabled={hReq.isProcessing}
                class="flex items-center gap-1.5 text-xs font-bold text-slate-400 hover:text-[#6b8cce] transition-colors disabled:opacity-50 bg-slate-50 sm:bg-transparent px-3 py-1.5 sm:px-0 sm:py-0 rounded-lg sm:rounded-none"
              >
                <RotateCcw size={12} strokeWidth={2.5} /> 
                {hReq.isProcessing ? 'جاري...' : 'تراجع وتعديل'}
              </button>
            </div>
          </div>
        {/each}
      </div>

      {#if totalPages > 1}
        <div class="mt-10 flex flex-col items-center gap-4">
          <div class="flex items-center gap-2">
            <button
              onclick={() => goToPage(currentPage + 1)} 
              disabled={currentPage === totalPages}
              class="w-10 h-10 flex items-center justify-center rounded-xl bg-white border border-slate-100 text-[#2a3c54] shadow-sm hover:bg-[#6b8cce] hover:text-white transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              aria-label="الصفحة السابقة"
            >
              <ChevronRight size={20} />
            </button>

            <div class="flex gap-1">
              {#each Array(totalPages) as _, i}
                <button
                  onclick={() => goToPage(i + 1)}
                  class="w-10 h-10 rounded-xl font-black text-xs transition-all
                  {currentPage === i + 1 
                    ? 'bg-[#2a3c54] text-white shadow-lg scale-110' 
                    : 'bg-white text-slate-400 hover:bg-slate-50 border border-slate-100'}"
                >
                  {i + 1}
                </button>
              {/each}
            </div>

            <button
              onclick={() => goToPage(currentPage - 1)}
              disabled={currentPage === 1}
              class="w-10 h-10 flex items-center justify-center rounded-xl bg-white border border-slate-100 text-[#2a3c54] shadow-sm hover:bg-[#6b8cce] hover:text-white transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              aria-label="الصفحة التالية"
            >
              <ChevronLeft size={20} />
            </button>
          </div>
          
          <p class="text-[10px] font-bold text-slate-400 italic">
            عرض صفحة {currentPage} من {totalPages}
          </p>
        </div>
      {/if}
    </section>
  {/if}
</div>