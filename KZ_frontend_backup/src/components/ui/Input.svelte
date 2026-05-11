<!--
  Knowledge Zakat — Input component.

  Replaces the dozens of ad-hoc <input> styles with one consistent
  component that has:
   - Label support (proper <label for=> association)
   - Optional left-side icon (Lucide)
   - Validation states (idle / success / error)
   - Helper / error text under the field
   - Smooth focus glow ring (220ms cubic-bezier)
   - Show/hide toggle for password fields

  Validation visual contract:
   - idle:    Blue 200 border
   - hover:   Blue 300 border
   - focus:   Navy 900 border + 3px navy glow ring
   - success: Green 600 border + soft green tint
   - error:   Red 600 border + soft red tint
-->

<script lang="ts">
  import { Eye, EyeOff } from 'lucide-svelte';

  type State = 'idle' | 'success' | 'error';
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  type IconType = any;

  interface Props {
    /** Field id (auto-generated if omitted, but a stable id is better). */
    id?: string;
    label?: string;
    type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'date' | 'datetime-local';
    value?: string | number;
    placeholder?: string;
    disabled?: boolean;
    readonly?: boolean;
    required?: boolean;
    autocomplete?: HTMLInputElement['autocomplete'];
    /** Lucide icon to render at the start of the input. */
    icon?: IconType;
    /** Validation state (drives border colour + glow). */
    validation?: State;
    /** Helper text under the field (only shown when no error message). */
    helperText?: string;
    /** Error message under the field — overrides helperText if present. */
    errorMessage?: string;
    /** Optional dir override. Auto: 'rtl' for text fields, 'ltr' for url/email/tel. */
    dir?: 'rtl' | 'ltr' | 'auto';
    min?: string;
    max?: string;
    step?: number;
    onchange?: (e: Event) => void;
    oninput?: (e: Event) => void;
    onblur?: (e: FocusEvent) => void;
    onfocus?: (e: FocusEvent) => void;
    class?: string;
  }

  let {
    id = `kz-input-${Math.random().toString(36).slice(2, 9)}`,
    label,
    type = 'text',
    value = $bindable(''),
    placeholder,
    disabled = false,
    readonly = false,
    required = false,
    autocomplete,
    icon,
    validation = 'idle',
    helperText,
    errorMessage,
    dir = 'auto',
    min,
    max,
    step,
    onchange,
    oninput,
    onblur,
    onfocus,
    class: className = '',
  }: Props = $props();

  // Toggle for password visibility.
  let showPassword = $state(false);
  let effectiveType = $derived(
    type === 'password' && showPassword ? 'text' : type,
  );

  // Choose dir automatically if user passed 'auto'.
  let effectiveDir = $derived.by(() => {
    if (dir !== 'auto') return dir;
    // English-only fields get LTR; everything else inherits RTL from page.
    if (type === 'email' || type === 'tel' || type === 'url') return 'ltr';
    return undefined; // inherit
  });

  // Border / background colour based on state.
  let stateClasses = $derived.by(() => {
    if (errorMessage) {
      return 'border-kz-error bg-red-50/50 focus:border-kz-error focus:shadow-[0_0_0_3px_rgba(220,38,38,0.1)]';
    }
    if (validation === 'success') {
      return 'border-kz-success bg-green-50/50 focus:border-kz-success focus:shadow-[0_0_0_3px_rgba(22,163,74,0.1)]';
    }
    if (validation === 'error') {
      return 'border-kz-error bg-red-50/50 focus:border-kz-error focus:shadow-[0_0_0_3px_rgba(220,38,38,0.1)]';
    }
    return 'border-brand-200 bg-surface-input hover:border-brand-300 focus:border-brand focus:bg-surface-elevated focus:shadow-kz-glow';
  });

  let baseClasses =
    'w-full rounded-button border-kz outline-none font-medium text-sm text-ink-primary placeholder:text-ink-muted transition-all duration-kz-normal ease-kz disabled:opacity-60 disabled:cursor-not-allowed';
</script>

<div class={`flex flex-col gap-2 ${className}`}>
  {#if label}
    <label for={id} class="text-xs font-semibold text-ink-secondary px-1">
      {label}
      {#if required}
        <span class="text-kz-error">*</span>
      {/if}
    </label>
  {/if}

  <div class="relative">
    {#if icon}
      {@const IconComp = icon}
      <span
        class="absolute right-4 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none"
      >
        <IconComp size={18} />
      </span>
    {/if}

    <input
      {id}
      type={effectiveType}
      bind:value
      {placeholder}
      {disabled}
      {readonly}
      {required}
      {autocomplete}
      {min}
      {max}
      {step}
      dir={effectiveDir}
      class={`${baseClasses} ${stateClasses} ${icon ? 'pr-12' : 'pr-4'} ${type === 'password' ? 'pl-12' : 'pl-4'} py-3.5`}
      {onchange}
      {oninput}
      {onblur}
      {onfocus}
    />

    {#if type === 'password'}
      <button
        type="button"
        onclick={() => (showPassword = !showPassword)}
        tabindex="-1"
        class="absolute left-4 top-1/2 -translate-y-1/2 text-ink-muted hover:text-brand transition-colors duration-kz-normal ease-kz"
        aria-label={showPassword ? 'إخفاء كلمة المرور' : 'إظهار كلمة المرور'}
      >
        {#if showPassword}
          <EyeOff size={18} />
        {:else}
          <Eye size={18} />
        {/if}
      </button>
    {/if}
  </div>

  {#if errorMessage}
    <p class="text-xs font-medium text-kz-error px-1">{errorMessage}</p>
  {:else if helperText}
    <p class="text-xs font-medium text-ink-muted px-1">{helperText}</p>
  {/if}
</div>
