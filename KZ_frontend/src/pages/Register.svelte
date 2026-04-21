<script>
  import { token, currentPage, user } from "../lib/stores";
  import api from "../lib/api";
  import { fly, fade } from 'svelte/transition';

  let firstname = "";
  let lastname = "";
  let email = "";
  let password = "";
  let bio = "";
  let birthdayDate = "";
  
  // 👈 متغيرات المعلم الجديدة
  let phone = "";
  let cvFile = null;

  let errorMessage = "";
  let isLoading = false;
  let registerStep = 1; 
  let role = ""; 
  let showPassword = false;
  
  let showSuccessModal = false;

  let tempToken = null;
  let tempUser = null;
// ضيفي هذا المتغير وية المتغيرات اللي فوك
  let phoneError = "";

  // ضيفي هاي الدالة اللي تفحص الرقم
  function validatePhone(p) {
    if (!p) return;
    // الشرط: يبدأ بـ 07 وبعده 9 أرقام (المجموع 11 رقم بالضبط)
    const regex = /^07\d{9}$/; 
    if (!regex.test(p)) {
      phoneError = "رقم الهاتف يجب أن يتكون من 11 رقماً ويبدأ بـ 07";
      return false;
    }
    phoneError = "";
    return true;
  }
  async function handleRegister(event) {
    if (event) event.preventDefault();
    if (role === 'teacher' && !validatePhone(phone)) return;
    isLoading = true;
    errorMessage = "";
    
    try {
      // 1. إنشاء الحساب
      await api.post("/users/", {
        firstname: firstname,
        lastname: lastname,
        email: email,
        password: password,
        bio: bio || "مستخدم جديد في منصة زكاة العلم",
        birthday_date: birthdayDate ? birthdayDate : null 
      });
      
      // 2. تسجيل دخول للحصول على التوكن
      const loginRes = await api.post("/token", { 
        email: email, 
        password: password 
      });
      const accessToken = loginRes.data.access_token;
      tempToken = accessToken;

      // 3. إذا اختار "معلم"، نرفع الصورة أولاً بعدين ندز الطلب
      if (role === 'teacher') {
        let finalCvLink = "لم يتم إرفاق ملف";
        
        // رفع الصورة/الملف إذا كان موجود
        if (cvFile && cvFile.length > 0) {
          const formData = new FormData();
          formData.append("file", cvFile[0]);
          
          const uploadRes = await api.post("/upload-cv/", formData, {
            headers: { 
              "Content-Type": "multipart/form-data",
              Authorization: `Bearer ${accessToken}` 
            }
          });
          finalCvLink = uploadRes.data.cv_url; // حفظ المسار الحقيقي
        }
        
        // إرسال طلب الانضمام كمعلم مع الرقم ورابط الصورة
        await api.post("/request-teacher/", { 
          cv_link: finalCvLink,
          phone: phone 
        }, {
          headers: { Authorization: `Bearer ${accessToken}` }
        });
      }

      // 4. جلب بيانات المستخدم الكاملة
      const userRes = await api.get("/users/me", {
        headers: { Authorization: `Bearer ${accessToken}` }
      });
      
      tempUser = userRes.data;
      isLoading = false;
      showSuccessModal = true;

    } catch (error) {
      console.error("Register Error:", error);
      if (error.response && error.response.data && error.response.data.detail) {
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        } else {
          errorMessage = "يرجى التأكد من صحة البيانات المدخلة.";
        }
      } else {
        errorMessage = "حدث خطأ: تأكد أن سيرفر الباك إند يعمل، أو أن الإيميل مستخدم مسبقاً.";
      }
      isLoading = false;
    }
  }

  function handleModalConfirm() {
    if (tempToken && tempUser) {
      token.set(tempToken);
      localStorage.setItem('token', tempToken);
      
      user.set(tempUser);
      localStorage.setItem('user', JSON.stringify(tempUser));
    }
    
    showSuccessModal = false;
    currentPage.set("home");
  }

  function goToNextStep() {
    if (role) {
      registerStep = 2;
    } else {
      errorMessage = "يرجى اختيار دورك (طالب أو معلم) للمتابعة";
    }
  }
</script>

{#if showSuccessModal}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm" in:fade out:fade>
    <div class="bg-white rounded-3xl p-8 shadow-2xl flex flex-col items-center max-w-sm w-full mx-4 border-t-8 border-[#6b8cce]" in:fly={{ y: 50, duration: 400 }}>
      
      <div class="w-20 h-20 bg-[#eff3fa] text-[#6b8cce] rounded-full flex items-center justify-center mb-5 shadow-inner">
        <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path>
        </svg>
      </div>
      
      <h3 class="text-2xl font-extrabold text-[#4a6583] mb-2 text-center">تم بنجاح!</h3>
      <p class="text-gray-600 text-center font-medium text-lg mb-8">
        تم إنشاء حسابك كـ <span class="font-bold text-[#6b8cce]">{role === 'teacher' ? 'معلم' : 'طالب'}</span> بنجاح.
      </p>
      
      <button type="button" onclick={handleModalConfirm} class="w-full rounded-xl bg-[#6b8cce] py-3.5 px-4 text-sm font-bold text-white hover:bg-[#5a7abb] focus:ring-4 focus:ring-[#eff3fa] transition-all shadow-md hover:shadow-lg">
        تأكيد والذهاب للحساب
      </button>
      
    </div>
  </div>
{/if}

<div dir="rtl" class="flex min-h-screen items-center justify-center bg-slate-50 p-4 sm:p-6 lg:p-8 font-sans">
  <div class="flex flex-col md:flex-row w-full max-w-5xl bg-white rounded-[2rem] shadow-2xl overflow-hidden border border-slate-100 min-h-[600px]">
    
    <div class="w-full md:w-1/2 p-8 sm:p-10 relative overflow-hidden flex flex-col justify-center bg-white overflow-y-auto">
      
      {#if errorMessage}
        <div class="absolute top-4 right-8 left-8 rounded-xl bg-red-50 p-4 border-r-4 border-red-500 flex items-center z-50">
          <p class="text-sm font-medium text-red-800">{errorMessage}</p>
        </div>
      {/if}

      {#if registerStep === 1}
        <div in:fly={{ x: -50, duration: 400 }} out:fade={{duration: 200}} class="flex flex-col h-full justify-center">
        
          <div class="flex gap-2 mb-8">
            <div class="h-1.5 w-1/2 bg-[#6b8cce] rounded-full"></div>
            <div class="h-1.5 w-1/2 bg-gray-200 rounded-full"></div>
          </div>

          <div class="text-center mb-8">
            <h2 class="text-3xl font-extrabold text-[#4a6583]">دعنا نبدأ!</h2>
            <p class="mt-2 text-sm text-gray-500">كيف تخطط لاستخدام هذه المنصة؟</p>
          </div>

          <div class="grid grid-cols-2 gap-4 mb-8">
            <button type="button" onclick={() => {role = 'teacher'; errorMessage='';}} class={`flex flex-col items-center justify-center p-6 border-2 rounded-2xl transition-all ${role === 'teacher' ? 'border-[#6b8cce] bg-[#eff3fa]' : 'border-gray-200 hover:border-gray-300 bg-white'}`}>
              <svg class="w-10 h-10 mb-3 text-[#4a6583]" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
              <span class="font-bold text-gray-800">معلم</span>
              <span class="text-xs text-gray-500 text-center mt-2">أريد مشاركة علمي وخبراتي</span>
            </button>

            <button type="button" onclick={() => {role = 'student'; errorMessage='';}} class={`flex flex-col items-center justify-center p-6 border-2 rounded-2xl transition-all ${role === 'student' ? 'border-[#6b8cce] bg-[#eff3fa]' : 'border-gray-200 hover:border-gray-300 bg-white'}`}>
              <svg class="w-10 h-10 mb-3 text-[#4a6583]" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M12 14l9-5-9-5-9 5 9 5z" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"></path><path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"></path><path d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"></path></svg>
              <span class="font-bold text-gray-800">طالب</span>
              <span class="text-xs text-gray-500 text-center mt-2">أبحث عن معلمين لتطوير مهاراتي</span>
            </button>
          </div>

          <button type="button" onclick={goToNextStep} class="w-full rounded-xl bg-gray-200 py-3.5 px-4 text-sm font-bold text-gray-700 hover:bg-gray-300 transition-all">
            التالي ⬅
          </button>

          <div class="mt-6 text-center">
            <p class="text-sm text-gray-600">لديك حساب بالفعل؟ <button type="button" onclick={() => currentPage.set('login')} class="font-bold text-[#6b8cce] hover:underline">تسجيل الدخول</button></p>
          </div>
        </div>

      {:else if registerStep === 2}
        <div in:fly={{ x: 50, duration: 400 }} out:fade={{duration: 200}} class="flex flex-col h-full justify-center py-4">
           
           <div class="flex gap-2 mb-6">
            <div class="h-1.5 w-1/2 bg-[#6b8cce] rounded-full"></div>
            <div class="h-1.5 w-1/2 bg-[#6b8cce] rounded-full"></div>
          </div>

          <div class="text-center mb-6">
            <h2 class="text-2xl font-extrabold text-[#4a6583]">أدخل معلوماتك</h2>
            <p class="mt-1 text-sm text-gray-500">يرجى إدخال معلوماتك الشخصية لإكمال التسجيل.</p>
          </div>

          <form class="space-y-4" onsubmit={handleRegister} autocomplete="off">
            <div class="flex gap-4">
              <div class="w-1/2">
                <label for="firstname" class="block text-sm font-semibold text-gray-700 mb-1.5">الاسم الأول</label>
                <input id="firstname" type="text" bind:value={firstname} required class="block w-full rounded-xl border border-gray-300 px-4 py-2.5 text-gray-900 placeholder-gray-400 focus:border-[#6b8cce] bg-slate-50 outline-none transition-all">
              </div>
              <div class="w-1/2">
                <label for="lastname" class="block text-sm font-semibold text-gray-700 mb-1.5">الاسم الأخير</label>
                <input id="lastname" type="text" bind:value={lastname} required class="block w-full rounded-xl border border-gray-300 px-4 py-2.5 text-gray-900 placeholder-gray-400 focus:border-[#6b8cce] bg-slate-50 outline-none transition-all">
              </div>
            </div>

            <div>
              <label for="email" class="block text-sm font-semibold text-gray-700 mb-1.5">البريد الإلكتروني</label>
              <input id="email" type="email" bind:value={email} required class="block w-full rounded-xl border border-gray-300 px-4 py-2.5 text-gray-900 placeholder-gray-400 focus:border-[#6b8cce] bg-slate-50 outline-none transition-all">
            </div>

            <div>
              <label for="password" class="block text-sm font-semibold text-gray-700 mb-1.5">كلمة المرور (8 أحرف على الأقل)</label>
              <div class="relative">
                <input id="password" type={showPassword ? "text" : "password"} bind:value={password} minlength="8" required class="block w-full rounded-xl border border-gray-300 px-4 py-2.5 pl-12 text-gray-900 placeholder-gray-400 focus:border-[#6b8cce] bg-slate-50 outline-none transition-all">
                <button type="button" onclick={() => showPassword = !showPassword} class="absolute inset-y-0 left-0 flex items-center pl-4 text-gray-400 hover:text-[#6b8cce]">
                  {#if showPassword}
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg>
                  {:else}
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"></path></svg>
                  {/if}
                </button>
              </div>
            </div>

            {#if role === 'teacher'}
              <div class="p-4 bg-[#eff3fa] rounded-xl border border-[#6b8cce] mb-4">
                <p class="text-xs font-bold text-[#4a6583] mb-3">معلومات المعلم المطلوبة:</p>
                <div class="space-y-4">
                  <div>
                    <label class="block text-sm font-semibold text-gray-700 mb-1.5">رقم الهاتف</label>
                    <input 
                      type="tel" 
                      bind:value={phone} 
                      oninput={() => validatePhone(phone)} 
                      required 
                      maxlength="11"
                      class="block w-full rounded-xl border border-gray-300 px-4 py-2.5 bg-white outline-none focus:border-[#6b8cce] transition-all text-left" 
                      placeholder="07..." 
                      dir="ltr"
                    >
                    {#if phoneError}
                      <p class="text-xs text-red-500 mt-1 font-bold">{phoneError}</p>
                    {/if}
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-gray-700 mb-1.5">صورة الهوية أو الشهادة</label>
                    <input type="file" bind:files={cvFile} accept="image/*,.pdf" required class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-[#6b8cce] file:text-white hover:file:bg-[#5a7abb] transition-all cursor-pointer">
                  </div>
                </div>
              </div>
            {/if}

            <div class="flex gap-4">
              <div class="w-1/2">
                <label for="birthdayDate" class="block text-sm font-semibold text-gray-700 mb-1.5">تاريخ الميلاد (اختياري)</label>
                <input id="birthdayDate" type="date" bind:value={birthdayDate} class="block w-full rounded-xl border border-gray-300 px-4 py-2.5 text-gray-900 placeholder-gray-400 focus:border-[#6b8cce] bg-slate-50 outline-none transition-all">
              </div>
            </div>

            <div>
              <label for="bio" class="block text-sm font-semibold text-gray-700 mb-1.5">نبذة تعريفية (اختياري)</label>
              <textarea id="bio" bind:value={bio} rows="2" class="block w-full rounded-xl border border-gray-300 px-4 py-2.5 text-gray-900 placeholder-gray-400 focus:border-[#6b8cce] bg-slate-50 outline-none transition-all resize-none" placeholder="اكتب نبذة مختصرة عنك..."></textarea>
            </div>
            
            <div class="flex gap-3 pt-4">
              <button type="button" onclick={() => registerStep = 1} class="w-1/3 rounded-xl bg-gray-100 py-3 px-4 text-sm font-bold text-gray-700 hover:bg-gray-200 transition-all">
                رجوع
              </button>
              <button 
                 type="submit" 
                 disabled={isLoading || phoneError !== ""} 
                 class="w-2/3 rounded-xl bg-[#6b8cce] py-3 px-4 text-sm font-bold text-white hover:bg-[#5a7abb] transition-all shadow-md hover:shadow-lg disabled:opacity-70"
              >
                {isLoading ? 'جاري التسجيل...' : 'إكمال التسجيل'}
              </button>
            </div>
          </form>
        </div>
      {/if}
    </div>

    <div class="hidden md:flex md:w-1/2 bg-gradient-to-br from-[#6b8cce] to-[#4a6583] text-white p-12 flex-col justify-center items-center text-center relative overflow-hidden">
      <div class="absolute top-0 right-0 -mr-20 -mt-20 w-64 h-64 rounded-full bg-white opacity-10 blur-2xl"></div>
      <div class="absolute bottom-0 left-0 -ml-20 -mb-20 w-80 h-80 rounded-full bg-[#2a3c54] opacity-20 blur-3xl"></div>
      
      <div class="relative z-10 space-y-6">
        <h1 class="text-4xl font-extrabold leading-tight">منصة زكاة العلم</h1>
        <p class="text-lg leading-relaxed text-[#e2e8f0]">
          مكان تلتقي فيه العقول لنشر المعرفة وتأدية زكاة العلم. أنشئ حسابك الآن وابدأ رحلتك.
        </p>
      </div>
    </div>

  </div>
</div>