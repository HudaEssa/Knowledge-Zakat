<script>
  import { user } from "../lib/stores"; 
  import api from "../lib/api"; 
  import { fade, scale } from "svelte/transition"; 

  let isEditing = $state(false); 
  let showOld = $state(false); 
  let showNew = $state(false); 
  let showSuccessModal = $state(false); 
  let showErrorModal = $state(false); 
  let errorMessage = $state(""); 
  
  // حالة الخطأ من السيرفر فقط للرمز الحالي
  let serverOldPwdError = $state(false);

  let profileData = $state({
    firstname: $user?.firstname || "",
    lastname: $user?.lastname || "", 
    bio: $user?.bio || "",
    old_password: "",
    new_password: "",
    confirm_password: ""
  });
async function handleImage(event) {
    const file = event.target.files[0];
    if (!file) return;

    // تحضير الملف للإرسال
    const formData = new FormData();
    formData.append("file", file);

    try {
      // إرسال الصورة للباك إند
      const res = await api.post("/me/upload-image", formData, {
        headers: {
          "Content-Type": "multipart/form-data"
        }
      });

      // تحديث بيانات المستخدم بالواجهة (حتى تطلع الصورة فوراً بدون ريفريش)
      user.set(res.data);
      localStorage.setItem('user', JSON.stringify(res.data));
      
      alert("تم تحديث صورة البروفايل بنجاح! 🖼️");
    } catch (error) {
      console.error("Error uploading image:", error);
      alert("حدث خطأ أثناء رفع الصورة.");
    }
  }
  // --- التحقق اللحظي الصارم جداً (المنقذ) ---
  function validateNewPwd(pwd) {
    if (pwd === "") return 'idle';
    // 8 حروف + حرف كبير + حرف صغير + رقم
    const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
    return regex.test(pwd) ? 'success' : 'error';
  }

  // 1. حواف الرمز الحالي (أحمر فقط إذا السيرفر گال خطأ)
  let oldPwdClass = $derived(serverOldPwdError ? 'border-red-500 ring-2 ring-red-100' : 'border-transparent');

  // 2. حواف الرمز الجديد (لحظي حسب الشروط)
  let newPwdClass = $derived(
    validateNewPwd(profileData.new_password) === 'idle' ? 'border-transparent' : 
    (validateNewPwd(profileData.new_password) === 'success' ? 'border-green-500 ring-2 ring-green-100' : 'border-red-500 ring-2 ring-red-100')
  );

  // 3. حواف التأكيد (لحظي حسب التطابق)
  let confirmClass = $derived(
    profileData.confirm_password === "" ? 'border-transparent' : 
    (profileData.confirm_password === profileData.new_password ? 'border-green-500 ring-2 ring-green-100' : 'border-red-500 ring-2 ring-red-100')
  );

  // دالة تبديل حالة التعديل مع تصفير شامل لضمان النظافة
  function toggleEditing() {
    isEditing = !isEditing; // [cite: 2]
    
    // تصفير كل قيم كلمات المرور (لحظياً) 
    profileData.old_password = "";
    profileData.new_password = "";
    profileData.confirm_password = "";
    
    // تصغير وإخفاء أي رسائل خطأ أو ألوان تنبيه 
    serverOldPwdError = false;
    errorMessage = "";
  }

  async function saveAll() {
    errorMessage = "";
    serverOldPwdError = false;

    // تشييك الشروط قبل الإرسال (حتى لا نتعب السيرفر)
    if (profileData.new_password !== "" && validateNewPwd(profileData.new_password) === 'error') {
        errorMessage = "كلمة المرور يجب أن تكون 8 رموز وتتضمن حرفاً كبيراً وصغيراً ورقماً";
        showErrorModal = true;
        return;
    }
    
    if (profileData.new_password !== profileData.confirm_password) {
      errorMessage = "كلمات المرور الجديدة غير متطابقة";
      showErrorModal = true;
      return;
    }

    try {
      const res = await api.put(`/users/${$user.id}`, profileData);
      user.set(res.data); 
      showSuccessModal = true;
      isEditing = false;
    } catch (err) { 
      errorMessage = err.response?.data?.detail || "فشل في تحديث البيانات";
      // إذا السيرفر رجع خطأ بالرمز الحالي (عادة 400 Bad Request)
      if (err.response?.status === 400) {
        serverOldPwdError = true;
      }
      showErrorModal = true; 
    }
  }
</script>

<div class="max-w-4xl mx-auto space-y-6 text-right relative" dir="rtl">
  
  {#if showSuccessModal}
    <div in:fade out:fade class="fixed inset-0 z-[5000] flex items-center justify-center p-4 bg-[#2a3c54]/40 backdrop-blur-md">
      <div in:scale={{ duration: 300, start: 0.9 }} class="bg-white rounded-[2.5rem] shadow-2xl p-10 max-w-sm w-full text-center space-y-6 border border-white">
        <div class="w-20 h-20 bg-[#eff3fa] rounded-full flex items-center justify-center mx-auto text-4xl text-[#2a3c54] font-black">ok</div>
        <div class="space-y-2">
          <h3 class="text-2xl font-black text-[#2a3c54]">تم الحفظ بنجاح</h3>
          <p class="text-sm font-bold text-slate-400 leading-relaxed">تم تحديث بيانات ملفك الشخصي بنجاح</p>
        </div>
        <button onclick={() => showSuccessModal = false} class="w-14 h-14 bg-[#2a3c54] text-white rounded-2xl font-black text-2xl flex items-center justify-center mx-auto hover:scale-110 transition-all shadow-lg active:scale-95">
            {'>'}
        </button>
      </div>
    </div>
  {/if}

  {#if showErrorModal}
    <div in:fade out:fade class="fixed inset-0 z-[5001] flex items-center justify-center p-4 bg-red-900/20 backdrop-blur-md">
        <div in:scale={{ duration: 300, start: 0.9 }} class="bg-white rounded-[2.5rem] shadow-2xl p-10 max-w-sm w-full text-center space-y-6 border border-red-100">
            <div class="w-20 h-20 bg-red-50 rounded-full flex items-center justify-center mx-auto text-4xl text-red-500 font-black">!</div>
            <div class="space-y-2">
                <h3 class="text-2xl font-black text-red-600">عذراً، فشل الحفظ</h3>
                <p class="text-sm font-bold text-slate-400 leading-relaxed">{errorMessage}</p>
            </div>
            <button onclick={() => showErrorModal = false} class="w-14 h-14 bg-red-500 text-white rounded-2xl font-black text-2xl flex items-center justify-center mx-auto hover:scale-110 transition-all shadow-lg active:scale-95">
                تراجع
            </button>
        </div>
    </div>
  {/if}

  <div class="bg-white rounded-[2.5rem] shadow-sm border border-slate-100 overflow-hidden">
    <div class="bg-[#2a3c54] h-44 relative"> 
      <div class="absolute -bottom-12 right-12 flex items-center gap-6 z-20">
        <div class="relative group">
          <div class="w-32 h-32 rounded-[2.5rem] bg-white p-1 shadow-2xl overflow-hidden border-4 border-white">
            {#if $user?.profile_image}
              <img src={$user.profile_image} alt="Profile" class="w-full h-full object-cover rounded-[2.2rem]" />
            {:else}
              <div class="w-full h-full bg-[#eff3fa] flex items-center justify-center text-4xl font-black text-[#6b8cce]">
                {$user?.firstname?.charAt(0).toUpperCase()}
              </div>
            {/if}
          </div>
          {#if isEditing}
            <label in:fade class="absolute inset-0 bg-black/40 flex items-center justify-center cursor-pointer transition-all rounded-[2.2rem] opacity-0 group-hover:opacity-100">
              <span class="text-sm text-white font-black">تغيير الصورة</span>
              <input type="file" class="hidden" onchange={handleImage} accept="image/*" />
            </label>
          {/if}
        </div>
        <div class="mb-4 text-white"> 
          <h2 class="text-3xl font-black tracking-tight drop-shadow-md">{$user?.firstname} {$user?.lastname}</h2>
        </div>
      </div>
    </div>

    <div class="pt-16 p-10 space-y-6">
      {#if isEditing}
        <div class="space-y-8" in:fade>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-1">
              <label class="text-xs font-black text-slate-400 pr-2">الاسم الشخصي</label>
              <input bind:value={profileData.firstname} class="w-full p-4 bg-slate-50 border-0 rounded-2xl outline-none focus:ring-2 ring-[#6b8cce] font-bold text-sm" />
            </div> 
            <div class="space-y-1">
              <label class="text-xs font-black text-slate-400 pr-2">الاسم الثاني</label>
              <input bind:value={profileData.lastname} class="w-full p-4 bg-slate-50 border-0 rounded-2xl outline-none focus:ring-2 ring-[#6b8cce] font-bold text-sm" />
            </div> 
            
            <div class="md:col-span-2 space-y-1">
              <label class="text-xs font-black text-slate-400 pr-2">نبذة عن طموحاتك العلمية</label>
              <textarea bind:value={profileData.bio} class="w-full p-4 bg-slate-50 border-0 rounded-2xl outline-none focus:ring-2 ring-[#6b8cce] font-bold text-sm h-32"></textarea>
            </div>

            <div class="relative space-y-1">
                <label class="text-xs font-black text-slate-400 pr-2">كلمة المرور الحالية</label>
                <input 
                  type={showOld ? 'text' : 'password'} 
                  bind:value={profileData.old_password} 
                  autocomplete="new-password"
                  oninput={() => serverOldPwdError = false}
                  class="w-full p-4 bg-slate-50 border-2 rounded-2xl outline-none font-bold text-sm transition-all {oldPwdClass}" 
                  placeholder="أدخل الرمز الحالي" 
                />
                <button onclick={() => showOld = !showOld} class="absolute left-4 top-10 text-[11px] font-bold text-[#6b8cce]">{showOld ? 'إخفاء' : 'إظهار'}</button>
            </div>

            <div class="relative space-y-1">
                <label class="text-xs font-black text-slate-400 pr-2">كلمة المرور الجديدة</label>
                <input 
                  type={showNew ? 'text' : 'password'} 
                  bind:value={profileData.new_password} 
                  autocomplete="off"
                  class="w-full p-4 bg-slate-50 border-2 rounded-2xl outline-none font-bold text-sm transition-all {newPwdClass}" 
                  placeholder="أدخل الرمز الجديد" 
                /> 
                <button onclick={() => showNew = !showNew} class="absolute left-4 top-10 text-[11px] font-bold text-[#6b8cce]">{showNew ? 'إخفاء' : 'إظهار'}</button> 
            </div>

            <div class="relative space-y-1 md:col-span-2">
                <label class="text-xs font-black text-slate-400 pr-2">تأكيد كلمة المرور الجديدة</label>
                <input 
                  type="password" 
                  bind:value={profileData.confirm_password} 
                  class="w-full p-4 bg-slate-50 border-2 rounded-2xl outline-none font-bold text-sm transition-all {confirmClass}" 
                  placeholder="أعد كتابة الرمز الجديد" 
                />
            </div>

            <button onclick={saveAll} class="md:col-span-2 py-5 bg-[#2a3c54] text-white rounded-2xl font-black shadow-lg hover:bg-[#1a2a3a] transition-all text-sm active:scale-95">حفظ كافة التغييرات النهائية</button>
          </div>
        </div>
      {:else}
        <div class="space-y-6" in:fade>
          <div class="bg-slate-50 p-8 rounded-[2rem] border border-white shadow-inner">
            <div class="mb-4">
              <h3 class="text-[11px] font-black text-slate-300 uppercase mb-4 tracking-widest">MY BIOGRAPHY</h3>
              <p class="text-base font-bold text-[#2a3c54] leading-relaxed italic">
                {$user?.bio || 'لا توجد نبذة شخصية بعد.. ابدأ بكتابة طموحاتك!'}
              </p> 
            </div>
          </div>
        </div> 
      {/if}

      <button onclick={toggleEditing} class="w-full py-5 rounded-2xl font-black text-sm shadow-xl transition-all active:scale-[0.98] {isEditing ? 'bg-red-500 hover:bg-red-600 text-white' : 'bg-[#2a3c54] hover:bg-[#1a2a3a] text-white'}">
        {isEditing ? 'إلغاء التعديل' : 'تعديل البيانات الشخصية'}
      </button>

    </div>
  </div>
</div>

<style>
  input, textarea { font-size: 15px !important; }
</style>