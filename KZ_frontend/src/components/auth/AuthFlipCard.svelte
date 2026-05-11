<!--
  Knowledge Zakat — Auth Flip Card.

  Pure 3D presentation primitive. Takes two snippet slots (`front`
  and `back`) and rotates between them around the Y axis when
  `isFlipped` is true.

  HEIGHT STRATEGY:
   Whichever face is currently showing stays in normal flow and
   drives the stage's height. The hidden face is absolutely
   positioned on top so it doesn't push the layout. This lets
   both faces be any height — important because the register form
   is much taller than the login form.
-->

<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Props {
    isFlipped: boolean;
    front: Snippet;
    back: Snippet;
  }

  let { isFlipped, front, back }: Props = $props();
</script>

<div class="flip-stage" style="perspective: 2400px;">
  <div class="flip-card {isFlipped ? 'is-flipped' : ''}">
    <!-- FRONT FACE — sized when !isFlipped -->
    <div
      class="flip-face flip-face--front {isFlipped ? 'is-hidden' : ''}"
      aria-hidden={isFlipped}
    >
      {@render front()}
    </div>

    <!-- BACK FACE — sized when isFlipped -->
    <div
      class="flip-face flip-face--back {isFlipped ? '' : 'is-hidden'}"
      aria-hidden={!isFlipped}
    >
      {@render back()}
    </div>
  </div>
</div>

<style>
  /* ─── 3D flip card mechanics ──────────────────────────────────────
     • .flip-stage gives the perspective context.
     • .flip-card rotates 180° around Y to reveal the back face.
     • Whichever face is visible stays in normal flow (so its
       content drives the stage height); the hidden face is
       absolutely positioned on top so it doesn't take up space.
     ────────────────────────────────────────────────────────── */
  .flip-stage {
    position: relative;
    width: 100%;
  }

  .flip-card {
    position: relative;
    width: 100%;
    transition: transform 0.75s cubic-bezier(0.65, 0.05, 0.36, 1);
    transform-style: preserve-3d;
  }

  .flip-card.is-flipped {
    transform: rotateY(180deg);
  }

  .flip-face {
    width: 100%;
    backface-visibility: hidden;
    -webkit-backface-visibility: hidden;
  }

  /* Visible face → in normal flow → drives the stage height. */
  .flip-face--front,
  .flip-face--back {
    position: relative;
  }

  /* Back face is pre-rotated so it reads correctly once the card flips. */
  .flip-face--back {
    transform: rotateY(180deg);
  }

  /* Hidden face → absolutely positioned so it doesn't take space. */
  .flip-face.is-hidden {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    pointer-events: none;
  }

  .flip-face--back.is-hidden {
    transform: rotateY(180deg);
  }
</style>