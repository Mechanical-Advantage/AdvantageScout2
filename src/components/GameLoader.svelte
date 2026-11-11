<script lang="ts">
  import type { Component } from "svelte";
  import { api } from "@lib/api.svelte";
  import { loadGameModule } from "@lib/games-registry";
  import type { ScoutingMode } from "@lib/scouting-store.svelte";

  let { mode }: { mode: ScoutingMode } = $props();

  let loading = $state(true);
  let error: string | null = $state(null);
  let ResolvedComponent: Component | null = $state(null);

  async function resolve() {
    loading = true;
    error = null;
    try {
      const res = await api.fetch("/api/global_settings");
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const settings = (await res.json()) as Record<string, unknown>;
      const year = String(settings.Game ?? "");

      const gameModule = await loadGameModule(year);
      if (!gameModule) throw new Error(`No games/${year}/ module found for the active game year`);

      const key = mode.charAt(0).toUpperCase() + mode.slice(1);
      ResolvedComponent = (gameModule as unknown as Record<string, Component>)[key] ?? null;
      if (!ResolvedComponent) throw new Error(`games/${year}/ has no ${key} component`);
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      loading = false;
    }
  }

  resolve();
</script>

{#if loading}
  <p class="text-fg-muted">Loading game module...</p>
{:else if error}
  <p class="text-danger">{error}</p>
{:else if ResolvedComponent}
  <ResolvedComponent />
{/if}
