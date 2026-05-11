<!--
  Knowledge Zakat — Card component.

  The signature surface of the app: white panel on the blue page,
  with the navy "side bar" hover effect for interactive cards.

  Variants:
   - default:    static card, no hover treatment
   - interactive: clickable, lifts + side bar appears on hover
   - hero:       larger radius, more padding, for top-of-page heros
   - flat:       no border, used inside another card

  The interactivity is purely visual; the actual onclick lives at the
  call site (you pass a real <button>/<a> as the children OR set
  `onclick` directly on this card).
-->

<script lang="ts">
  import type { Snippet } from 'svelte';

  type Variant = 'default' | 'interactive' | 'hero' | 'flat';

  interface Props {
    variant?: Variant;
    /** Outer padding scale. Use 'none' if children manage their own padding. */
    padding?: 'none' | 'sm' | 'md' | 'lg';
    onclick?: (e: MouseEvent) => void;
    class?: string;
    children?: Snippet;
  }

  let {
    variant = 'default',
    padding = 'md',
    onclick,
    class: className = '',
    children,
  }: Props = $props();

  const paddingClasses: Record<NonNullable<Props['padding']>, string> = {
    none: '',
    sm:   'p-4 md:p-5',
    md:   'p-5 md:p-7',
    lg:   'p-7 md:p-10',
  };

  const variantClasses: Record<Variant, string> = {
    default:     'bg-surface-elevated border-kz border-brand-200 rounded-card shadow-kz-sm',
    interactive: 'bg-surface-elevated border-kz border-brand-200 rounded-card shadow-kz-sm cursor-pointer kz-card is-interactive',
    hero:        'bg-surface-elevated border-kz border-brand-200 rounded-modal shadow-kz-md',
    flat:        'bg-surface-muted rounded-card',
  };

  let computedClass = $derived(
    [variantClasses[variant], paddingClasses[padding], className].join(' '),
  );
</script>

{#if onclick}
  <button
    type="button"
    {onclick}
    class={`${computedClass} text-right w-full`}
  >
    {#if children}{@render children()}{/if}
  </button>
{:else}
  <div class={computedClass}>
    {#if children}{@render children()}{/if}
  </div>
{/if}
