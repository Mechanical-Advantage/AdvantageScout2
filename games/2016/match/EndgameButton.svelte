<script lang="ts">
  import { gameData, pushUndoSnapshot } from "./store.svelte";

  let { field, label }: { field: string; label: string } = $props();

  const achieved = $derived(Number(gameData.values[field] ?? 0) > 0);

  function toggle(): void {
    pushUndoSnapshot();
    gameData.values[field] = achieved ? 0 : 1;
  }
</script>

<button class="btn {achieved ? 'btn-success' : 'btn-outline'}" onclick={toggle}>
  {label}?
</button>
