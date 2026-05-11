<!--
  Knowledge Zakat — Badge / status chip component.

  Tiny pill-shaped element used for statuses ("approved", "pending"),
  category tags, role labels, etc. Replaces the dozens of inline
  span+class combinations across pages.
-->

<script lang="ts">
  import type { Snippet } from 'svelte';

  type Variant = 'brand' | 'success' | 'error' | 'warning' | 'info' | 'neutral';
  type Size = 'sm' | 'md';
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  type IconType = any;

  interface Props {
    variant?: Variant;
    size?: Size;
    /** Optional Lucide icon component to render at the start. */
    icon?: IconType;
    class?: string;
    children?: Snippet;
  }

  let {
    variant = 'neutral',
    size = 'sm',
    icon,
    class: className = '',
    children,
  }: Props = $props();

  const variantClasses: Record<Variant, string> = {
    brand:   'bg-brand-soft text-brand ring-1 ring-brand-200',
    success: 'bg-kz-success-soft text-kz-success-dark ring-1 ring-green-200',
    error:   'bg-kz-error-soft text-kz-error-dark ring-1 ring-red-200',
    warning: 'bg-kz-warning-soft text-kz-warning-dark ring-1 ring-amber-200',
    info:    'bg-kz-info-soft text-kz-info-dark ring-1 ring-blue-200',
    neutral: 'bg-slate-50 text-slate-700 ring-1 ring-slate-200',
  };

  const sizeClasses: Record<Size, string> = {
    sm: 'px-2.5 py-1 text-[10px] gap-1',
    md: 'px-3 py-1.5 text-xs gap-1.5',
  };

  const iconSizes: Record<Size, number> = { sm: 12, md: 14 };
</script>

<span
  class={`inline-flex items-center font-semibold rounded-full ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
>
  {#if icon}
    {@const IconComp = icon}
    <IconComp size={iconSizes[size]} />
  {/if}
  {#if children}{@render children()}{/if}
</span>
