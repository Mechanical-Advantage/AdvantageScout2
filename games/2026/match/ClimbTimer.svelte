<script lang="ts">
  import { gameData, pushUndoSnapshot } from "./store.svelte";

  let running = $state(false);
  let startedAt = $state<number | null>(null);
  let elapsedMs = $state(0);
  let interval: ReturnType<typeof setInterval> | null = null;

  const committed = $derived(Number(gameData.values["TeleClimbTime"] ?? 0));
  const displayMs = $derived(running ? elapsedMs : committed);

  function tick() {
    if (startedAt !== null) elapsedMs = performance.now() - startedAt;
  }

  function press() {
    if (running) {
      running = false;
      if (interval) clearInterval(interval);
      pushUndoSnapshot();
      gameData.values["TeleClimbTime"] = Math.round(elapsedMs);
    } else {
      pushUndoSnapshot();
      elapsedMs = 0;
      gameData.values["TeleClimbTime"] = 0;
      running = true;
      startedAt = performance.now();
      interval = setInterval(tick, 100);
    }
  }
</script>

<button class="btn w-40 {running ? 'btn-success' : 'btn-accent'}" onclick={press}>
  Climb time: <strong>{Math.round(displayMs) / 1000}s</strong>
</button>
