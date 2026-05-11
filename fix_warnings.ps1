# ============================================================
# Knowledge Zakat - Fix All 12 Svelte Warnings
# ============================================================
# هذا السكريبت يصلح كل التحذيرات الـ 12 بضغطة زر
#
# الاستخدام:
#   1. ضعي هذا الملف في جذر المشروع (نفس مكان KZ_frontend)
#   2. افتحي PowerShell في نفس المكان
#   3. شغّلي: .\fix_warnings.ps1
#
# الإصلاحات:
#   - UserManager.svelte: ربط labels بـ inputs (5 fixes)
#   - Home.svelte: article→button, aria-label, حذف CSS غير مستخدم (5 fixes)
#   - TeacherView.svelte: حذف text-right المكرر (2 fixes)
# ============================================================

$ErrorActionPreference = "Stop"

# المسارات
$frontendPath = "KZ_frontend/src"
$userManagerPath = "$frontendPath/components/UserManager.svelte"
$homePath = "$frontendPath/pages/Home.svelte"
$teacherViewPath = "$frontendPath/pages/TeacherView.svelte"

# التحقق من وجود الملفات
Write-Host "`n🔍 التحقق من وجود الملفات..." -ForegroundColor Cyan

$files = @($userManagerPath, $homePath, $teacherViewPath)
foreach ($file in $files) {
    if (-not (Test-Path $file)) {
        Write-Host "❌ خطأ: الملف $file غير موجود!" -ForegroundColor Red
        Write-Host "تأكدي إنك شغّلتي السكريبت من جذر المشروع." -ForegroundColor Yellow
        exit 1
    }
    Write-Host "✓ $file" -ForegroundColor Green
}

# نسخة احتياطية
Write-Host "`n💾 إنشاء نسخ احتياطية..." -ForegroundColor Cyan
$backupDir = "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $backupDir | Out-Null

foreach ($file in $files) {
    $backupName = Split-Path $file -Leaf
    Copy-Item $file "$backupDir/$backupName"
    Write-Host "  → $backupDir/$backupName" -ForegroundColor Gray
}

# ============================================================
# الإصلاح 1: UserManager.svelte
# ============================================================
Write-Host "`n🔧 إصلاح UserManager.svelte (5 warnings)..." -ForegroundColor Cyan

$content = Get-Content $userManagerPath -Raw -Encoding UTF8

# label 1: الاسم الأول
$content = $content -replace `
    '<label class="block text-\[10px\] font-bold text-slate-500 mb-1">الاسم الأول <span class="text-rose-500">\*</span></label>\s*<input type="text" bind:value=\{adminForm\.firstname\}', `
    '<label for="admin-firstname" class="block text-[10px] font-bold text-slate-500 mb-1">الاسم الأول <span class="text-rose-500">*</span></label>
            <input id="admin-firstname" type="text" bind:value={adminForm.firstname}'

# label 2: اسم العائلة
$content = $content -replace `
    '<label class="block text-\[10px\] font-bold text-slate-500 mb-1">اسم العائلة</label>\s*<input type="text" bind:value=\{adminForm\.lastname\}', `
    '<label for="admin-lastname" class="block text-[10px] font-bold text-slate-500 mb-1">اسم العائلة</label>
            <input id="admin-lastname" type="text" bind:value={adminForm.lastname}'

# label 3: البريد الإلكتروني
$content = $content -replace `
    '<label class="block text-\[10px\] font-bold text-slate-500 mb-1">البريد الإلكتروني <span class="text-rose-500">\*</span></label>\s*<input type="email" bind:value=\{adminForm\.email\}', `
    '<label for="admin-email" class="block text-[10px] font-bold text-slate-500 mb-1">البريد الإلكتروني <span class="text-rose-500">*</span></label>
          <input id="admin-email" type="email" bind:value={adminForm.email}'

# label 4: رقم الهاتف
$content = $content -replace `
    '<label class="block text-\[10px\] font-bold text-slate-500 mb-1">رقم الهاتف</label>\s*<input type="tel" bind:value=\{adminForm\.phone\}', `
    '<label for="admin-phone" class="block text-[10px] font-bold text-slate-500 mb-1">رقم الهاتف</label>
          <input id="admin-phone" type="tel" bind:value={adminForm.phone}'

# label 5: كلمة المرور
$content = $content -replace `
    '<label class="block text-\[10px\] font-bold text-slate-500 mb-1">كلمة المرور <span class="text-rose-500">\*</span></label>\s*<input type="text" bind:value=\{adminForm\.password\}', `
    '<label for="admin-password" class="block text-[10px] font-bold text-slate-500 mb-1">كلمة المرور <span class="text-rose-500">*</span></label>
          <input id="admin-password" type="text" bind:value={adminForm.password}'

Set-Content -Path $userManagerPath -Value $content -Encoding UTF8 -NoNewline
Write-Host "  ✓ تم إضافة id/for على 5 inputs" -ForegroundColor Green

# ============================================================
# الإصلاح 2: Home.svelte
# ============================================================
Write-Host "`n🔧 إصلاح Home.svelte (5 warnings)..." -ForegroundColor Cyan

$content = Get-Content $homePath -Raw -Encoding UTF8

# إصلاح 2-أ: تحويل <article role="button"> إلى <button>
$content = $content -replace `
    '<article\s*class="course-card-clickable"\s*onclick=\{\(\) => openCourse\(c\)\}\s*role="button"\s*tabindex="0"\s*onkeydown=\{\(e\) => e\.key === ''Enter'' && openCourse\(c\)\}', `
    '<button
                type="button"
                class="course-card-clickable"
                onclick={() => openCourse(c)}'

# إصلاح closing tag </article> ← </button>
# نلقّط الـ </article> الذي يلي card-footer-action
$content = $content -replace `
    '(<div class="card-footer-action">\s*عرض التفاصيل <ChevronLeft size=\{16\} strokeWidth=\{2\.5\} />\s*</div>\s*)</article>', `
    '$1</button>'

# إصلاح 2-ب: إضافة aria-label للزر بدون نص (t-dot)
$content = $content -replace `
    '<button class="t-dot \{teacherPage === i \? ''active'' : ''''\}" onclick=\{\(\) => teacherPage = i\}></button>', `
    '<button class="t-dot {teacherPage === i ? ''active'' : ''''}" onclick={() => teacherPage = i} aria-label="انتقل لصفحة المعلمين {i + 1}"></button>'

# إصلاح 2-ج: حذف CSS غير مستخدم
# .t-search-icon
$content = $content -replace `
    '\s*\.t-search-icon \{ color: var\(--muted\); margin-left: 0\.5rem; \}', ''

# .skeleton-grid في @media
$content = $content -replace `
    '\.courses-grid, \.skeleton-grid \{ grid-template-columns: 1fr; \}', `
    '.courses-grid { grid-template-columns: 1fr; }'

# .course-card في @media
$content = $content -replace `
    '\s*\.course-card \{ border-radius: var\(--radius-lg\); \}', ''

Set-Content -Path $homePath -Value $content -Encoding UTF8 -NoNewline
Write-Host "  ✓ تحويل article → button" -ForegroundColor Green
Write-Host "  ✓ إضافة aria-label على t-dot" -ForegroundColor Green
Write-Host "  ✓ حذف 3 CSS classes غير مستخدمة" -ForegroundColor Green

# ============================================================
# الإصلاح 3: TeacherView.svelte
# ============================================================
Write-Host "`n🔧 إصلاح TeacherView.svelte (2 warnings)..." -ForegroundColor Cyan

$content = Get-Content $teacherViewPath -Raw -Encoding UTF8

# حذف text-right المكرر
$content = $content -replace `
    'class="bg-white rounded-\[2rem\] border border-slate-100 overflow-hidden shadow-sm hover:shadow-xl hover:-translate-y-2 transition-all duration-300 text-right group flex flex-col w-full text-right"', `
    'class="bg-white rounded-[2rem] border border-slate-100 overflow-hidden shadow-sm hover:shadow-xl hover:-translate-y-2 transition-all duration-300 text-right group flex flex-col w-full"'

Set-Content -Path $teacherViewPath -Value $content -Encoding UTF8 -NoNewline
Write-Host "  ✓ حذف text-right المكرر" -ForegroundColor Green

# ============================================================
# النهاية
# ============================================================
Write-Host "`n✅ تم إصلاح كل المشاكل الـ 12!" -ForegroundColor Green
Write-Host "`n📝 الخطوات التالية:" -ForegroundColor Cyan
Write-Host "  1. افتحي VS Code وتأكدي إن الـ Problems panel فاضي" -ForegroundColor White
Write-Host "  2. شغّلي: cd KZ_frontend && npx svelte-check" -ForegroundColor White
Write-Host "  3. لو فيه مشكلة، النسخ الاحتياطية في: $backupDir" -ForegroundColor White
Write-Host "`n🎓 موفقة بمشروع التخرج!" -ForegroundColor Magenta