<!--
  Knowledge Zakat — Guest Exit Link.

  Small reusable link that says "تصفح كزائر بدون تسجيل". Used at the
  bottom of both the login and the register face of the flip card,
  plus inside the marketing aside.

  Variants:
   - `divider`: when true, renders a dashed-top divider above the
     link (used inside form cards). Default false (used in the
     marketing aside).
-->

<script lang="ts">
  import { Eye } from 'lucide-svelte';

  interface Props {
    onClick: () => void;
    divider?: boolean;
  }

  let { onClick, divider = true }: Props = $props();
</script>

<div
  class="text-center {divider ? 'mt-5 pt-4 border-t border-brand-200' : ''}"
>
  <button
    type="button"
    onclick={onClick}
    class="text-sm font-semibold text-brand hover:text-brand-dark transition-colors inline-flex items-center gap-1.5"
  >
    <Eye size={14} />
    تصفح كزائر بدون تسجيل
  </button>
</div>
