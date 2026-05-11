<!--
  Knowledge Zakat — Auth Background.

  Decorative-only: the three soft blurred blobs that float in the
  background of the Auth page. Pulled out of Auth.svelte so the
  parent stays focused on logic, and so the blobs can be reused
  in any future "auth-feeling" screen (e.g. a password reset
  page) without copy/paste.
-->

<style>
  /* `will-change` hints the GPU so the float keyframes don't
     repaint the whole viewport on each frame. */
  :global(.kz-blob-1),
  :global(.kz-blob-2) {
    will-change: transform;
  }
</style>

<div
  class="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-brand-200/40 blur-3xl kz-blob-1 pointer-events-none"
></div>
<div
  class="absolute -bottom-32 -right-32 w-[28rem] h-[28rem] rounded-full bg-brand-300/30 blur-3xl kz-blob-2 pointer-events-none"
></div>
<div
  class="absolute top-1/2 left-1/3 w-72 h-72 rounded-full bg-brand-400/15 blur-3xl kz-blob-1 pointer-events-none"
  style="animation-delay: -7s;"
></div>
