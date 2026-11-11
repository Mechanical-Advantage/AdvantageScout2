<script lang="ts">
  import { onMount } from "svelte";
  import { push } from "svelte-spa-router";
  import { scoutingSession, gameFieldsCache } from "@lib/scouting-store.svelte";
  import { fetchGameFields } from "@lib/scouts";
  import { getCachedGameFields, setCachedGameFields } from "@lib/game-fields-cache";

  let error: string | null = $state(null);

  onMount(async () => {
    const mode = scoutingSession.mode;
    if (gameFieldsCache.mode === mode && gameFieldsCache.data) {
      push(`/scouting/${mode}`);
      return;
    }
    const cached = getCachedGameFields(mode);
    if (cached) {
      gameFieldsCache.mode = mode;
      gameFieldsCache.data = cached;
      push(`/scouting/${mode}`);
      return;
    }
    try {
      const data = await fetchGameFields(mode);
      setCachedGameFields(mode, data);
      gameFieldsCache.mode = mode;
      gameFieldsCache.data = data;
      push(`/scouting/${mode}`);
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    }
  });
</script>

<div class="mx-auto max-w-lg">
  <h1 class="mb-4 text-2xl font-bold text-fg">Loading...</h1>
  {#if error}
    <p class="mb-4 text-danger">Failed to load game fields: {error}</p>
    <button class="rounded-md bg-surface px-3 py-1.5 text-sm font-medium text-fg hover:bg-border" onclick={() => push("/")}>
      Back to Home
    </button>
  {/if}
</div>
