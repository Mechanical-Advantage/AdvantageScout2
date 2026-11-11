<script lang="ts">
  let { class: className = "h-4 w-4" }: { class?: string } = $props();
</script>

<svg class={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg">
  <path d="M18 6L6 18" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path>
  <path d="M6 6L18 18" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path>
</svg>
