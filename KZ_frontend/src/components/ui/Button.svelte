<!--
  Knowledge Zakat — Button component.

  A single, polished button with all the variants we need across the app.
  Replaces ~60 different ad-hoc <button> styles scattered across pages
  with one consistent component.

  Variants:
   - primary:     navy filled, the "main action" of a screen (1 per screen)
   - secondary:   blue-soft filled, alternate action
   - outline:     border-only, neutral action
   - ghost:       transparent, low-priority action
   - success:     green, "approve" / "save"
   - danger:      red, "delete" / "reject"
   - warning:     amber, "edit" / "modify"
   - info:        blue 600, informational

  Sizes:
   - sm:  smaller padding, 12px text
   - md:  default
   - lg:  larger, hero buttons

  Loading: when `loading` is true, shows a spinner and disables the button.
  Icon: pass `icon` to put a Lucide icon before the label, or `iconRight`
  for after. Use either, not both — visually noisy.

  Animations:
   - Hover: translateY(-1px) + shadow-color glow
   - Active: scale(0.98) for 80ms — tactile press feedback
   - Focus-visible: 2px navy ring (keyboard nav)
   - Loading: spinner replaces icon, label dims slightly
-->

<script lang="ts">
  import type { Snippet } from 'svelte';
  import { Loader2 } from 'lucide-svelte';

  type Variant =
    | 'primary'
    | 'secondary'
    | 'outline'
    | 'ghost'
    | 'success'
    | 'danger'
    | 'warning'
    | 'info';

  type Size = 'sm' | 'md' | 'lg';
  type ButtonType = 'button' | 'submit' | 'reset';

  /**
   * Lucide icon components have a complex generic signature; using
   * the more permissive `any` here avoids the generic-mismatch error
   * when consumers pass icons like `Mail`, `Lock`, `LogIn`, etc. The
   * runtime contract (Svelte component with `size` and `class` props)
   * is identical across the entire Lucide set.
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  type IconType = any;

  interface Props {
    variant?: Variant;
    size?: Size;
    type?: ButtonType;
    disabled?: boolean;
    loading?: boolean;
    fullWidth?: boolean;
    icon?: IconType;
    iconRight?: IconType;
    href?: string;
    target?: '_self' | '_blank';
    onclick?: (e: MouseEvent) => void;
    class?: string;
    children?: Snippet;
    ariaLabel?: string;
  }

  let {
    variant = 'primary',
    size = 'md',
    type = 'button',
    disabled = false,
    loading = false,
    fullWidth = false,
    icon,
    iconRight,
    href,
    target = '_self',
    onclick,
    class: className = '',
    children,
    ariaLabel,
  }: Props = $props();

  // Variant -> Tailwind class lookup. Keeping these as strings (not
  // dynamically built) lets Tailwind's compiler pick them up.
  const variantClasses: Record<Variant, string> = {
    primary:
      'bg-brand text-white hover:bg-brand-hover hover:shadow-kz-brand active:bg-brand-hover',
    secondary:
      'bg-brand-soft text-brand hover:bg-brand-200 active:bg-brand-300',
    outline:
      'bg-transparent text-brand border-kz border-brand-200 hover:border-brand hover:bg-brand-50 active:bg-brand-100',
    ghost:
      'bg-transparent text-ink-secondary hover:bg-brand-50 hover:text-brand active:bg-brand-100',
    success:
      'bg-kz-success text-white hover:shadow-kz-success hover:brightness-105 active:brightness-95',
    danger:
      'bg-kz-error text-white hover:shadow-kz-error hover:brightness-105 active:brightness-95',
    warning:
      'bg-kz-warning text-white hover:shadow-kz-warning hover:brightness-105 active:brightness-95',
    info:
      'bg-kz-info text-white hover:brightness-105 active:brightness-95',
  };

  const sizeClasses: Record<Size, string> = {
    sm: 'px-4 py-2 text-xs gap-1.5',
    md: 'px-6 py-3 text-sm gap-2',
    lg: 'px-8 py-4 text-base gap-2.5',
  };

  const iconSizes: Record<Size, number> = { sm: 14, md: 16, lg: 18 };

  let computedClass = $derived(
    [
      // Base layout
      'inline-flex items-center justify-center',
      'font-medium rounded-button select-none',
      'transition-all duration-kz-normal ease-kz',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2',
      // Press behaviour
      'hover:-translate-y-px active:translate-y-0 active:scale-[0.98]',
      // Disabled state
      'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 disabled:hover:shadow-none disabled:active:scale-100',
      // Variant
      variantClasses[variant],
      // Size
      sizeClasses[size],
      // Width
      fullWidth ? 'w-full' : '',
      className,
    ].join(' '),
  );
</script>

{#if href && !disabled && !loading}
  <a
    {href}
    {target}
    rel={target === '_blank' ? 'noopener noreferrer' : undefined}
    class={computedClass}
    aria-label={ariaLabel}
  >
    {#if loading}
      <Loader2 size={iconSizes[size]} class="animate-spin" />
    {:else if icon}
      {@const IconComp = icon}
      <IconComp size={iconSizes[size]} />
    {/if}
    {#if children}
      <span class={loading ? 'opacity-70' : ''}>{@render children()}</span>
    {/if}
    {#if iconRight && !loading}
      {@const IconRightComp = iconRight}
      <IconRightComp size={iconSizes[size]} />
    {/if}
  </a>
{:else}
  <button
    {type}
    disabled={disabled || loading}
    {onclick}
    class={computedClass}
    aria-label={ariaLabel}
    aria-busy={loading}
  >
    {#if loading}
      <Loader2 size={iconSizes[size]} class="animate-spin" />
    {:else if icon}
      {@const IconComp = icon}
      <IconComp size={iconSizes[size]} />
    {/if}
    {#if children}
      <span class={loading ? 'opacity-70' : ''}>{@render children()}</span>
    {/if}
    {#if iconRight && !loading}
      {@const IconRightComp = iconRight}
      <IconRightComp size={iconSizes[size]} />
    {/if}
  </button>
{/if}
