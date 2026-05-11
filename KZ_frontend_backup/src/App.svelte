<!--
  Knowledge Zakat — Application root (with guest browsing).

  Responsibilities:
   1. Boot the router (so URL <-> store sync starts working).
   2. Mount the global Notification overlay exactly once.
   3. Mount the global AuthPromptToast (nudges guests to sign in).
   4. Decide which top-level layout (Auth / Student / Teacher / Admin)
      to render based on auth + role.
   5. Inside each layout, dispatch the active page based on `route.name`.
   6. Apply role-based redirects when the URL points at a page the
      current user shouldn't see.

  Guest mode:
   - A user with NO token may visit a subset of student pages
     (home, session_details, teacher_view, session_view).
   - All other routes redirect to /login.
   - Inside guest-allowed pages, any action that requires auth pops
     the AuthPromptToast via the authPrompt store.
-->

<script lang="ts">
  import { onMount } from 'svelte';
  import { token, user, hasRole } from './lib/stores';
  import { route, navigate, initRouter } from './lib/router';
  import type { RouteName } from './lib/types';

  // Pages — auth (unified flip card)
  import Auth from './pages/Auth.svelte';

  // Pages — student
  import Home from './pages/Home.svelte';
  import MyLearning from './pages/MyLearning.svelte';
  import StudentProfile from './pages/StudentProfile.svelte';
  import SessionView from './pages/SessionView.svelte';
  import TeacherView from './pages/TeacherView.svelte';
  import SessionDetails from './pages/SessionDetails.svelte';

  // Pages — teacher
  import TeacherHome from './pages/TeacherHome.svelte';
  import CreateSession from './pages/CreateSession.svelte';
  import MyLectures from './pages/MyLectures.svelte';
  import TeacherRequests from './components/TeacherRequests.svelte';
  import Profile from './pages/Profile.svelte';
  import UpdateSession from './components/UpdateSession.svelte';

  // Pages — admin
  import AdminPanel from './pages/AdminPanel.svelte';

  // Layouts
  import StudentLayout from './components/StudentLayout.svelte';
  import TeacherLayout from './components/TeacherLayout.svelte';
  import AdminLayout from './components/AdminLayout.svelte';

  // Global UI
  import Notification from './components/Notification.svelte';
  import AuthPromptToast from './components/AuthPromptToast.svelte';

  // ---- Role flags ---------------------------------------------------------
  let isAdmin = $derived(hasRole($user, 'admin'));
  let isTeacher = $derived(hasRole($user, 'teacher'));
  let isAuthed = $derived(!!$token);

  // ---- Route guards -------------------------------------------------------
  // Routes a guest (no token) is allowed to land on. Anything else
  // bounces them to /login. Note: session_view is included so that
  // clicking a course card from Home doesn't dead-end; the per-day
  // enrollment buttons inside it are individually guarded.
  const GUEST_ROUTES: ReadonlySet<RouteName> = new Set<RouteName>([
    'home',
    'session_details',
    'teacher_view',
    'session_view',
  ]);

  const STUDENT_ROUTES: ReadonlySet<RouteName> = new Set<RouteName>([
    'home',
    'my_learning',
    'student_profile',
    'session_view',
    'session_details',
    'teacher_view',
  ]);
  const TEACHER_ROUTES: ReadonlySet<RouteName> = new Set<RouteName>([
    'teacher_home',
    'create_session',
    'my_lectures',
    'teacher_requests',
    'profile',
    'update_session',
    'session_details',
  ]);
  const ADMIN_ROUTES: ReadonlySet<RouteName> = new Set<RouteName>([
    'admin_logs',
    'admin_dashboard',
    'admin_panel',
  ]);
  const PUBLIC_ROUTES: ReadonlySet<RouteName> = new Set<RouteName>([
    'login',
    'register',
  ]);

  $effect(() => {
    // ─── Unauthenticated visitor ──────────────────────────────
    if (!isAuthed) {
      // Auth pages are always fine.
      if (PUBLIC_ROUTES.has($route.name)) return;
      // Guest-allowed pages are fine.
      if (GUEST_ROUTES.has($route.name)) return;
      // Anything else (profile, my_learning, admin, etc.) → login.
      navigate('login', null, true);
      return;
    }

    // ─── Authenticated user on an auth page ──────────────────
    if (PUBLIC_ROUTES.has($route.name)) {
      if (isAdmin) navigate('admin_panel', null, true);
      else if (isTeacher) navigate('teacher_home', null, true);
      else navigate('home', null, true);
      return;
    }

    // ─── Role-based redirect when role doesn't match URL ─────
    if (isAdmin && !ADMIN_ROUTES.has($route.name)) {
      navigate('admin_panel', null, true);
    } else if (isTeacher && !TEACHER_ROUTES.has($route.name)) {
      navigate('teacher_home', null, true);
    } else if (!isAdmin && !isTeacher && !STUDENT_ROUTES.has($route.name)) {
      navigate('home', null, true);
    }
  });

  // ---- Boot ---------------------------------------------------------------
  onMount(() => {
    initRouter();
    const isDark = localStorage.getItem('kz.theme') === 'dark';
    document.documentElement.classList.toggle('dark', isDark);
  });
</script>

<Notification />
<AuthPromptToast />

<main class="font-sans antialiased min-h-screen bg-brand-100 overflow-x-hidden">
  {#if !isAuthed && PUBLIC_ROUTES.has($route.name)}
    <!-- Guest on auth page → unified Auth (flip card) -->
    <Auth />

  {:else if !isAuthed}
    <!-- Guest browsing public pages → student-style layout in guest mode -->
    <StudentLayout>
      {#if $route.name === 'session_view'}
        <SessionView />
      {:else if $route.name === 'session_details'}
        <SessionDetails />
      {:else if $route.name === 'teacher_view'}
        <TeacherView />
      {:else}
        <Home />
      {/if}
    </StudentLayout>

  {:else if isAdmin}
    <AdminLayout>
      <AdminPanel />
    </AdminLayout>

  {:else if isTeacher}
    <TeacherLayout>
      {#if $route.name === 'create_session'}
        <CreateSession />
      {:else if $route.name === 'my_lectures'}
        <MyLectures />
      {:else if $route.name === 'teacher_requests'}
        <TeacherRequests />
      {:else if $route.name === 'profile'}
        <Profile />
      {:else if $route.name === 'update_session'}
        <UpdateSession />
      {:else if $route.name === 'session_details'}
        <SessionDetails />
      {:else}
        <TeacherHome />
      {/if}
    </TeacherLayout>

  {:else}
    <StudentLayout>
      {#if $route.name === 'my_learning'}
        <MyLearning />
      {:else if $route.name === 'student_profile'}
        <StudentProfile />
      {:else if $route.name === 'session_view'}
        <SessionView />
      {:else if $route.name === 'session_details'}
        <SessionDetails />
      {:else if $route.name === 'teacher_view'}
        <TeacherView />
      {:else}
        <Home />
      {/if}
    </StudentLayout>
  {/if}
</main>