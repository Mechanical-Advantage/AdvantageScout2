<script lang="ts">
  import { canUndo, undo } from "./store.svelte";
</script>

<button class="btn btn-accent" disabled={!canUndo()} onclick={undo}>
  Undo
</button>
