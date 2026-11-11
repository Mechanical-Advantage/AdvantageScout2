<script lang="ts">
  import { fade } from "svelte/transition";
  import { toastState } from "@lib/messages.svelte";
</script>

{#if toastState.visible}
  <div
    class="pointer-events-none fixed inset-x-0 z-[10000] flex justify-center {toastState.centered
      ? 'top-1/2 -translate-y-1/2'
      : 'top-4'}"
    transition:fade={{ duration: 250 }}
  >
    <div
      class="max-w-[85%] rounded-lg border border-[rgba(150,150,150,0.2)] bg-surface px-6 py-3.5 text-center text-sm font-semibold text-fg shadow-lg"
    >
      {toastState.message}
    </div>
  </div>
{/if}
