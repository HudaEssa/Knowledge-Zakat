<script>
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';

    // هاي الفانكشن تشتغل أول ما تفتح الصفحة
    onMount(() => {
        // 1. نجيب بيانات اليوزر من الـ LocalStorage (اللي خزنناها ورا اللوجن)
        const savedUser = localStorage.getItem('user');
        
        if (!savedUser) {
            // إذا ماكو يوزر أصلاً، وّديه للـ Login
            goto('/login');
            return;
        }

        const user = JSON.parse(savedUser);

        // 2. نشيك الـ Roles مالته (نفس الأسماء اللي سويناها بالباكيند)
        const isAdmin = user.roles.some(role => role.role_name === 'admin');

        if (!isAdmin) {
            // إذا مو أدمن، رجعه للصفحة الرئيسية وگله ممنوع
            alert("عذراً، هذه الصفحة للأدمن فقط!");
            goto('/');
        }
    });
</script>

<slot />