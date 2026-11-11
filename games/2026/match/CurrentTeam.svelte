<script lang="ts">
  import { scoutingSession } from "@lib/scouting-store.svelte";

  const isBlue = $derived(scoutingSession.alliance === "Blue");
</script>

<div class="badge {isBlue ? 'badge-primary' : 'badge-error'} badge-lg pointer-events-none">
  {scoutingSession.team || "-"}
</div>
