<script lang="ts">
  let { class: className = "h-4 w-4" }: { class?: string } = $props();
</script>

<svg class={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg">
  <path d="M3 11L12 4L21 11" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path>
  <path d="M5 9.5V20H19V9.5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path>
  <path d="M9.5 20V14H14.5V20" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path>
</svg>
