<script>
  import { token, currentPage, user } from "../lib/stores";
  import api from "../lib/api";

  let email = "";
  let password = "";
  let errorMessage = "";
  let isLoading = false;
  let showPassword = false;

  async function handleLogin(event) {
    if (event) event.preventDefault();
    isLoading = true;
    errorMessage = "";
    
    try {
      // إرسال البيانات بصيغة JSON
      const response = await api.post("/token", { 
        email: email, 
        password: password 
      });
      
      const accessToken = response.data.access_token;
      token.set(accessToken);
      localStorage.setItem('token', accessToken);

      const userRes = await api.get("/users/me");
      const userData = userRes.data;
      user.set(userData);
      localStorage.setItem('user', JSON.stringify(userData));

      const isAdmin = userData.roles.some(r => r.role_name === 'admin');
      if (isAdmin) {
        currentPage.set("admin_logs");
      } else {
        currentPage.set("home"); 
      }
    } catch (error) {
      console.error("Login Error:", error);
      if (error.response && error.response.data && error.response.data.detail) {
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        } else {
          errorMessage = "يرجى التأكد من صحة البيانات المدخلة";
        }
      } else {
        errorMessage = "خطأ في البريد الإلكتروني أو كلمة المرور";
      }
    } finally {
      isLoading = false;
    }
  }
</script>

<div dir="rtl" class="flex min-h-screen items-center justify-center bg-slate-50 p-4 sm:p-6 lg:p-8 font-sans">
  <div class="flex flex-col md:flex-row w-full max-w-5xl bg-white rounded-[2rem] shadow-2xl overflow-hidden border border-slate-100 min-h-[600px]">
    
    <div class="w-full md:w-1/2 p-8 sm:p-12 relative overflow-hidden flex flex-col justify-center bg-white">
      
      {#if errorMessage}
        <div class="absolute top-4 right-8 left-8 rounded-xl bg-red-50 p-4 border-r-4 border-red-500 flex items-center z-50">
          <p class="text-sm font-medium text-red-800">{errorMessage}</p>
        </div>
      {/if}

      <div>
        <div class="mb-8 text-center">
         
        </div>

        <div class="text-center mb-8">
          <h2 class="text-3xl font-extrabold text-[#4a6583] tracking-tight">تسجيل الدخول</h2>
          <p class="mt-2 text-sm text-gray-500">أهلاً بك مجدداً! يرجى إدخال بياناتك للمتابعة.</p>
        </div>

        <form class="space-y-5" onsubmit={handleLogin} autocomplete="off">
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-2">البريد الإلكتروني</label>
            <input type="email" bind:value={email} required autocomplete="off" class="block w-full rounded-xl border border-gray-300 px-4 py-3.5 text-gray-900 placeholder-gray-400 focus:border-[#6b8cce] focus:ring-[#6b8cce] bg-slate-50 outline-none transition-all" placeholder="name@example.com">
          </div>
          
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-2">كلمة المرور</label>
            <div class="relative">
              <input type={showPassword ? "text" : "password"} bind:value={password} required autocomplete="new-password" class="block w-full rounded-xl border border-gray-300 px-4 py-3.5 pl-12 text-gray-900 placeholder-gray-400 focus:border-[#6b8cce] focus:ring-[#6b8cce] bg-slate-50 outline-none transition-all" placeholder="••••••••">
              <button type="button" onclick={() => showPassword = !showPassword} class="absolute inset-y-0 left-0 flex items-center pl-4 text-gray-400 hover:text-[#6b8cce] focus:outline-none transition-colors">
                {#if showPassword}
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg>
                {:else}
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"></path></svg>
                {/if}
              </button>
            </div>
          </div>
          
          <button type="submit" disabled={isLoading} class="w-full rounded-xl bg-[#6b8cce] py-3.5 px-4 text-sm font-bold text-white hover:bg-[#5a7abb] focus:ring-2 focus:ring-[#6b8cce] focus:ring-offset-2 transition-all shadow-md hover:shadow-lg disabled:opacity-70 mt-4">
            {isLoading ? 'جاري الدخول...' : 'تسجيل الدخول'}
          </button>
        </form>
        
        <div class="mt-6 text-center">
          <p class="text-sm text-gray-600">ليس لديك حساب؟ <button type="button" onclick={() => currentPage.set('register')} class="font-bold text-[#6b8cce] hover:underline">أنشئ حساباً الآن</button></p>
        </div>
      </div>
    </div>

    <div class="hidden md:flex md:w-1/2 bg-gradient-to-br from-[#6b8cce] to-[#4a6583] text-white p-12 flex-col justify-center items-center text-center relative overflow-hidden">
      <div class="absolute top-0 right-0 -mr-20 -mt-20 w-64 h-64 rounded-full bg-white opacity-10 blur-2xl"></div>
      <div class="absolute bottom-0 left-0 -ml-20 -mb-20 w-80 h-80 rounded-full bg-[#2a3c54] opacity-20 blur-3xl"></div>
      
      <div class="relative z-10 space-y-6">
        <h1 class="text-4xl font-extrabold leading-tight">منصة زكاة العلم</h1>
        <p class="text-lg leading-relaxed text-[#e2e8f0]">
          مكان تلتقي فيه العقول لنشر المعرفة وتأدية زكاة العلم.
        </p>
      </div>
    </div>

  </div>
</div>