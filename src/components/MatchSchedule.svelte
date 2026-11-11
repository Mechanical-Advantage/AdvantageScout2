<script lang="ts">
  import {
    fetchCurrentMatchSchedule,
    fetchCurrentSuperSchedule,
    fetchCurrentMatchScheduleStatus,
    fetchCurrentSuperScheduleStatus,
    type MatchScheduleRow,
    type SuperScheduleRow,
    type MatchScheduleStatus,
    type SuperScheduleStatus,
    type ScheduleSlotStatus,
    type ScheduleSelection,
  } from "@lib/scouts";
  import { untrack } from "svelte";
  import { SCHEDULE_POLL_INTERVAL } from "@lib/config";

  let {
    kind = "match",
    showToggle = true,
    selectable = false,
    onSelect,
  }: {
    kind?: "match" | "super";
    showToggle?: boolean;
    selectable?: boolean;
    onSelect?: (selection: ScheduleSelection) => void;
  } = $props();

  let activeKind: "match" | "super" = $state("match");
  let loading = $state(true);
  let error: string | null = $state(null);
  let row: MatchScheduleRow | SuperScheduleRow | null = $state(null);
  let status: MatchScheduleStatus | SuperScheduleStatus | null = $state(null);
  let pollTimer: ReturnType<typeof setInterval> | null = null;

  $effect(() => {
    activeKind = kind;
  });

  async function load() {
    loading = untrack(() => row === null);
    error = null;
    try {
      const [r, s] =
        activeKind === "match"
          ? await Promise.all([fetchCurrentMatchSchedule(), fetchCurrentMatchScheduleStatus().catch(() => null)])
          : await Promise.all([fetchCurrentSuperSchedule(), fetchCurrentSuperScheduleStatus().catch(() => null)]);
      row = r;
      status = s;
    } catch (e) {
      if (row === null) {
        error = e instanceof Error ? e.message : String(e);
      }
    } finally {
      loading = false;
    }
  }

  $effect(() => {
    activeKind;
    load();
    pollTimer = setInterval(load, SCHEDULE_POLL_INTERVAL);
    return () => {
      if (pollTimer) clearInterval(pollTimer);
      pollTimer = null;
    };
  });

  function slotStatus(key: string): ScheduleSlotStatus | undefined {
    return (status?.slots as Record<string, ScheduleSlotStatus> | undefined)?.[key];
  }

  function scoutCellClass(key: string): string {
    const s = slotStatus(key);
    if (s?.active) return "bg-success/40 font-semibold text-fg";
    if (s?.uploaded) return "bg-info/30 text-fg";
    if (s && !s.available) return "bg-danger/30 font-semibold text-danger";
    return "text-fg-muted";
  }

  function selectAlliance(alliance: "Red" | "Blue", teamIndex: number) {
    if (!selectable || !onSelect || !row) return;
    if (activeKind === "match") {
      const r = row as MatchScheduleRow;
      const key = `${alliance}${teamIndex}` as keyof MatchScheduleRow;
      const scoutKey = `Scout${alliance}${teamIndex}` as keyof MatchScheduleRow;
      onSelect({ match: r.Match, alliance, team: Number(r[key]), scout: String(r[scoutKey] ?? "") });
    } else {
      const r = row as SuperScheduleRow;
      const teams = [1, 2, 3].map((i) => Number(r[`${alliance}${i}` as keyof SuperScheduleRow]));
      const scoutKey = `Scout${alliance}` as keyof SuperScheduleRow;
      onSelect({ match: r.Match, alliance, teams, scout: String(r[scoutKey] ?? "") });
    }
  }

  const cellBase = "border border-[rgba(150,150,150,0.3)] px-2 py-1.5 text-center";
  const blueHeaderCell = `${cellBase} bg-blue-700 text-white font-bold`;
  const redHeaderCell = `${cellBase} bg-red-700 text-white font-bold`;
</script>

<div class="rounded-lg border border-border bg-surface p-3">
  <div class="mb-2 flex items-center justify-between">
    <h3 class="font-semibold text-fg">
      {loading || !row ? "Match" : `Match ${row.Match}`}
    </h3>
    {#if showToggle}
      <div class="join">
        <button
          class="btn join-item btn-xs {activeKind === 'match' ? 'btn-primary' : 'btn-outline'}"
          onclick={() => (activeKind = "match")}
        >
          Match
        </button>
        <button
          class="btn join-item btn-xs {activeKind === 'super' ? 'btn-primary' : 'btn-outline'}"
          onclick={() => (activeKind = "super")}
        >
          Super
        </button>
      </div>
    {/if}
  </div>

  {#if loading}
    <p class="text-sm text-fg-muted">Loading...</p>
  {:else if error}
    <p class="text-sm text-danger">{error}</p>
  {:else if row}
    <div class="overflow-x-auto">
      <table class="table-auto w-full border-separate border-spacing-1 text-sm">
        <thead>
          <tr>
            {#if activeKind === "match"}
              <th class={blueHeaderCell}>Blue 1</th>
              <th class={blueHeaderCell}>Blue 2</th>
              <th class={blueHeaderCell}>Blue 3</th>
              <th class={redHeaderCell}>Red 1</th>
              <th class={redHeaderCell}>Red 2</th>
              <th class={redHeaderCell}>Red 3</th>
            {:else}
              <th class={blueHeaderCell}>Blue Alliance</th>
              <th class={redHeaderCell}>Red Alliance</th>
            {/if}
          </tr>
        </thead>
        <tbody>
          <tr>
            {#if activeKind === "match"}
              {@const r = row as MatchScheduleRow}
              {#each [1, 2, 3] as i}
                <td
                  class="{cellBase} bg-blue-500/10 {selectable ? 'cursor-pointer hover:bg-blue-500/20' : ''}"
                  onclick={() => selectAlliance("Blue", i)}
                >
                  {r[`Blue${i}` as keyof MatchScheduleRow]}
                </td>
              {/each}
              {#each [1, 2, 3] as i}
                <td
                  class="{cellBase} bg-red-500/10 {selectable ? 'cursor-pointer hover:bg-red-500/20' : ''}"
                  onclick={() => selectAlliance("Red", i)}
                >
                  {r[`Red${i}` as keyof MatchScheduleRow]}
                </td>
              {/each}
            {:else}
              {@const r = row as SuperScheduleRow}
              <td
                class="{cellBase} bg-blue-500/10 {selectable ? 'cursor-pointer hover:bg-blue-500/20' : ''}"
                onclick={() => selectAlliance("Blue", 0)}
              >
                {r.Blue1} / {r.Blue2} / {r.Blue3}
              </td>
              <td
                class="{cellBase} bg-red-500/10 {selectable ? 'cursor-pointer hover:bg-red-500/20' : ''}"
                onclick={() => selectAlliance("Red", 0)}
              >
                {r.Red1} / {r.Red2} / {r.Red3}
              </td>
            {/if}
          </tr>
          <tr>
            {#if activeKind === "match"}
              {@const r = row as MatchScheduleRow}
              {#each [1, 2, 3] as i}
                <td
                  class="{cellBase} text-xs {scoutCellClass(`Blue${i}`)} {selectable ? 'cursor-pointer' : ''}"
                  onclick={() => selectAlliance("Blue", i)}
                  >{r[`ScoutBlue${i}` as keyof MatchScheduleRow]}</td
                >
              {/each}
              {#each [1, 2, 3] as i}
                <td
                  class="{cellBase} text-xs {scoutCellClass(`Red${i}`)} {selectable ? 'cursor-pointer' : ''}"
                  onclick={() => selectAlliance("Red", i)}
                  >{r[`ScoutRed${i}` as keyof MatchScheduleRow]}</td
                >
              {/each}
            {:else}
              {@const r = row as SuperScheduleRow}
              <td
                class="{cellBase} text-xs {scoutCellClass('Blue')} {selectable ? 'cursor-pointer' : ''}"
                onclick={() => selectAlliance("Blue", 0)}
              >
                {r.ScoutBlue}
              </td>
              <td
                class="{cellBase} text-xs {scoutCellClass('Red')} {selectable ? 'cursor-pointer' : ''}"
                onclick={() => selectAlliance("Red", 0)}
              >
                {r.ScoutRed}
              </td>
            {/if}
          </tr>
        </tbody>
      </table>
    </div>
  {/if}
</div>
