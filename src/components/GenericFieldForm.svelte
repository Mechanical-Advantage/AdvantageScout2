<script lang="ts">
  import { push } from "svelte-spa-router";
  import { api } from "@lib/api.svelte";
  import { getDeviceName } from "@/lib/device";
  import { queueSubmission, flushQueue } from "@lib/upload-queue.svelte";
  import { scoutingSession, gameFieldsCache, type ScoutingMode, type FieldDef } from "@lib/scouting-store.svelte";

  let { mode }: { mode: ScoutingMode } = $props();

  let loading = $state(true);
  let loadError: string | null = $state(null);
  let submitting = $state(false);
  let submitted = $state(false);

  let tabs: string[] = $state([]);
  let activeTab: string = $state("");
  let values: Record<string, number | string | boolean> = $state({});

  async function ensureFields() {
    loading = true;
    loadError = null;
    try {
      if (gameFieldsCache.mode !== mode || !gameFieldsCache.data) {
        const res = await api.fetch(`/api/game_fields/${mode}`);
        if (!res.ok) throw new Error(`Server returned ${res.status}`);
        gameFieldsCache.data = await res.json();
        gameFieldsCache.mode = mode;
      }
      const data = gameFieldsCache.data!;
      tabs = Object.keys(data.setup);
      activeTab = tabs[0] ?? "";
      values = { ...(data.fields as Record<string, number | string | boolean>) };
    } catch (e) {
      loadError = e instanceof Error ? e.message : String(e);
    } finally {
      loading = false;
    }
  }

  ensureFields();

  function fieldsForTab(tab: string): FieldDef[] {
    return gameFieldsCache.data?.setup[tab]?.fields ?? [];
  }

  function increment(field: FieldDef, delta: number) {
    const current = Number(values[field.name] ?? 0);
    let next = current + delta;
    if (field.min !== undefined) next = Math.max(field.min, next);
    if (field.max !== undefined) next = Math.min(field.max, next);
    values[field.name] = next;
  }

  function buildPayloadRow(): Record<string, unknown> {
    const base: Record<string, unknown> = {
      ...values,
      Mode: mode,
      Device: getDeviceName(),
      Scout: scoutingSession.scout,
    };
    if (mode === "match") {
      base.Team = Number(scoutingSession.team);
      base.Match = Number(scoutingSession.match);
      base.Alliance = scoutingSession.alliance;
    } else if (mode === "pit") {
      base.Team = Number(scoutingSession.team);
    } else if (mode === "super") {
      base.Team1 = Number(scoutingSession.team1);
      base.Team2 = Number(scoutingSession.team2);
      base.Team3 = Number(scoutingSession.team3);
      base.Alliance = scoutingSession.alliance;
    }
    return base;
  }

  async function submit() {
    submitting = true;
    queueSubmission(buildPayloadRow());
    submitted = true;
    flushQueue();
    setTimeout(() => push("/"), 1200);
    submitting = false;
  }
</script>

{#if loading}
  <p class="text-fg-muted">Loading {mode} fields...</p>
{:else if loadError}
  <p class="text-danger">Failed to load fields: {loadError}</p>
{:else if submitted}
  <p class="text-success">Saved. Returning home...</p>
{:else}
  <div role="tablist" class="tabs tabs-bordered mb-4">
    {#each tabs as tab}
      <button
        role="tab"
        class="tab capitalize {tab === activeTab ? 'tab-active' : ''}"
        onclick={() => (activeTab = tab)}
      >
        {tab}
      </button>
    {/each}
  </div>

  <div class="flex flex-col gap-3">
    {#each fieldsForTab(activeTab) as field}
      <div class="flex flex-col gap-1">
        <label class="text-sm font-medium text-fg" for={field.name}>
          {field.display?.name ?? field.name}
        </label>
        {#if field.type === "Integer" || field.type === "Numeric"}
          <div class="flex items-center gap-3">
            <button class="btn btn-square btn-outline btn-sm" onclick={() => increment(field, -1)}>-</button>
            <span class="w-8 text-center tabular-nums text-fg">{values[field.name]}</span>
            <button class="btn btn-square btn-outline btn-sm" onclick={() => increment(field, 1)}>+</button>
          </div>
        {:else if field.type === "Boolean"}
          <input
            id={field.name}
            type="checkbox"
            class="checkbox checkbox-accent"
            checked={Boolean(values[field.name])}
            onchange={(e) => (values[field.name] = e.currentTarget.checked)}
          />
        {:else}
          <textarea
            id={field.name}
            class="textarea textarea-bordered"
            value={String(values[field.name] ?? "")}
            oninput={(e) => (values[field.name] = e.currentTarget.value)}
          ></textarea>
        {/if}
      </div>
    {/each}
  </div>

  <button class="btn btn-primary mt-6 w-full" onclick={submit} disabled={submitting}>
    {submitting ? "Saving..." : "Save"}
  </button>
{/if}
