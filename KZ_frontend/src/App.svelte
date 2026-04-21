<script>
  import { onMount } from 'svelte';
  import { currentPage, token, user, selectedTeacherId, selectedSessionId } from "./lib/stores";

  // ==========================================
  // استيراد جميع الصفحات
  // ==========================================
  
  // صفحات مشتركة / مصادقة
  import Login from "./pages/Login.svelte";
  import Register from "./pages/Register.svelte";
  
  // صفحات الطالب
  import Home from "./pages/Home.svelte";
  import MyLearning from "./pages/MyLearning.svelte";
  import StudentProfile from "./pages/StudentProfile.svelte";
  import SessionView from "./pages/SessionView.svelte"; 
  import TeacherView from "./pages/TeacherView.svelte"; // 👈 تأكدي إن الاسم مطابق لملفج
  
  // صفحات المعلم
  import TeacherHome from "./pages/TeacherHome.svelte";
  import CreateSession from "./pages/CreateSession.svelte";
  import MyLectures from "./pages/MyLectures.svelte";
  import TeacherRequests from "./components/TeacherRequests.svelte";
  import Profile from "./pages/Profile.svelte"; 
  
  // صفحات الآدمن والمكونات الإضافية
  import AdminPanel from "./pages/AdminPanel.svelte";
  import StudentLayout from "./components/StudentLayout.svelte";
  import TeacherLayout from "./components/TeacherLayout.svelte";
  import AdminLayout from "./components/AdminLayout.svelte";
  import UpdateSession from "./components/UpdateSession.svelte";
  import SessionDetails from "./pages/SessionDetails.svelte"; 

  // ==========================================
  // تحديد الأدوار
  // ==========================================
  let isAdmin = $derived($user?.roles?.some(r => r.id === 3 || r.role_name === 'admin'));
  let isTeacher = $derived($user?.roles?.some(r => r.id === 2 || r.role_name === 'teacher'));
  let isStudent = $derived($user?.roles?.some(r => r.id === 1 || r.role_name === 'student'));

  // منطق تحويل الصفحات التلقائي للأدوار
  $effect(() => {
    if ($user) {
      if (isTeacher && $currentPage === 'home') {
        currentPage.set('teacher_home');
      }
      if (isStudent && $currentPage === 'teacher_home') {
        currentPage.set('home');
      }
    }
  });

  onMount(() => {
    const isDark = localStorage.getItem('theme') === 'dark';
    document.documentElement.classList.toggle('dark', isDark);
  });
</script>

<main class="font-sans antialiased min-h-screen bg-slate-50 overflow-x-hidden">
  
  {#if !$token}
    {#if $currentPage === 'register'} 
      <Register /> 
    {:else} 
      <Login /> 
    {/if}

  {:else}
    
    {#if isAdmin}
      <AdminLayout> 
        <AdminPanel /> 
      </AdminLayout>

    {:else if isTeacher}
      <TeacherLayout>
        {#if $currentPage === 'teacher_home'} 
          <TeacherHome />
        {:else if $currentPage === 'create_session'} 
          <CreateSession />
        {:else if $currentPage === 'my_lectures'} 
          <MyLectures />
        {:else if $currentPage === 'teacher_requests' || $currentPage === 'student_requests'} 
          <TeacherRequests />
        {:else if $currentPage === 'profile'} 
          <Profile /> 
        {:else if $currentPage.name === 'update_session'}
          <UpdateSession />
        {:else if $currentPage.name === 'session_details'}
          <SessionDetails sessionId={$currentPage.data.sessionId} />
        {:else} 
          <TeacherHome /> 
        {/if}
      </TeacherLayout>

    {:else}
      <StudentLayout>
        {#if $currentPage === 'home'}
          <Home />
        {:else if $currentPage === 'my_learning'}
          <MyLearning />
        {:else if $currentPage === 'student_profile'}
          <StudentProfile />
        
        {:else if $currentPage === 'session_view'}
          <SessionView />

        {:else if $currentPage === 'teacher_view'}
          <TeacherView />

        {:else if typeof $currentPage === 'object'}
          {#if $currentPage.name === 'view_teacher'}
            <TeacherView /> 
          {:else if $currentPage.name === 'session_details'}
            <SessionDetails sessionId={$currentPage.data.sessionId} />
          {:else if $currentPage.name === 'session_view'}
            <SessionView />
          {/if}
        
        {:else}
          <Home />
        {/if}
      </StudentLayout>
    {/if}

  {/if}
  
</main>