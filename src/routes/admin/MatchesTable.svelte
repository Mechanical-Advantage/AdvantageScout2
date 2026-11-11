<script lang="ts">
  import type { AllMatchesStatus, AllSuperMatchesStatus } from "@lib/scouts";

  let {
    mode,
    onModeChange,
    matchesData,
    matchesLoading,
    matchesError,
    superMatchesData,
    superMatchesLoading,
    superMatchesError,
    inactiveMatchScouts,
    inactiveSuperScouts,
  }: {
    mode: "match" | "super";
    onModeChange: (mode: "match" | "super") => void;
    matchesData: AllMatchesStatus;
    matchesLoading: boolean;
    matchesError: string | null;
    superMatchesData: AllSuperMatchesStatus;
    superMatchesLoading: boolean;
    superMatchesError: string | null;
    inactiveMatchScouts: Set<string>;
    inactiveSuperScouts: Set<string>;
  } = $props();

  let showScheduledScouts = $state(false);

  const OUR_TEAM = 6328;

  function matchCellBorder(isCurrent: boolean): string {
    return isCurrent ? "border-2 border-accent" : "border border-[rgba(150,150,150,0.3)]";
  }

  function teamCellClass(uploaded: boolean, index: number, team: number): string {
    const base = uploaded ? "bg-success/40 text-fg" : index < 3 ? "bg-blue-500/10 text-fg-muted" : "bg-red-500/10 text-fg-muted";
    return team === OUR_TEAM ? `${base} font-bold text-yellow-400` : base;
  }

  function superAllianceCellClass(uploaded: boolean, allianceIndex: number, teams: number[]): string {
    const base = uploaded
      ? "bg-success/40 text-fg"
      : allianceIndex === 0
        ? "bg-blue-500/10 text-fg-muted"
        : "bg-red-500/10 text-fg-muted";
    return teams.includes(OUR_TEAM) ? `${base} font-bold text-yellow-400` : base;
  }

  function scoutLabelClass(name: string | null): string {
    const inactive = mode === "match" ? inactiveMatchScouts : inactiveSuperScouts;
    if (name && inactive.has(name)) return "font-semibold text-danger";
    return "font-normal opacity-75";
  }
</script>

<div class="mt-6 px-1">
  <div class="mb-3 flex items-center justify-between">
    <div class="flex items-center gap-3">
      <h2 class="font-semibold text-fg">Matches</h2>
      <div class="join">
        <button
          class="btn join-item btn-xs {mode === 'match' ? 'btn-primary' : 'btn-outline'}"
          onclick={() => onModeChange("match")}
        >
          Match
        </button>
        <button
          class="btn join-item btn-xs {mode === 'super' ? 'btn-primary' : 'btn-outline'}"
          onclick={() => onModeChange("super")}
        >
          Super
        </button>
      </div>
    </div>
    <label class="label cursor-pointer gap-2">
      <span class="label-text text-sm text-fg-muted">Show Scouts</span>
      <input type="checkbox" class="toggle toggle-primary toggle-sm" bind:checked={showScheduledScouts} />
    </label>
  </div>
  {#if mode === "match"}
    {#if matchesLoading}
      <p class="text-sm text-fg-muted">Loading...</p>
    {:else if matchesError}
      <p class="text-sm text-danger">{matchesError}</p>
    {:else if matchesData.matches.length === 0}
      <p class="text-sm text-fg-muted">No matches in the schedule yet.</p>
    {:else}
      <div class="overflow-x-auto">
        <table class="table-auto border-separate border-spacing-1 text-sm">
          <thead>
            <tr>
              <th class="border border-[rgba(150,150,150,0.3)] bg-neutral px-2 py-1.5 text-center font-bold text-white"
                >Match</th
              >
              <th class="border border-[rgba(150,150,150,0.3)] bg-blue-700 px-2 py-1.5 text-center font-bold text-white"
                >B1</th
              >
              <th class="border border-[rgba(150,150,150,0.3)] bg-blue-700 px-2 py-1.5 text-center font-bold text-white"
                >B2</th
              >
              <th class="border border-[rgba(150,150,150,0.3)] bg-blue-700 px-2 py-1.5 text-center font-bold text-white"
                >B3</th
              >
              <th class="border border-[rgba(150,150,150,0.3)] bg-red-700 px-2 py-1.5 text-center font-bold text-white"
                >R1</th
              >
              <th class="border border-[rgba(150,150,150,0.3)] bg-red-700 px-2 py-1.5 text-center font-bold text-white"
                >R2</th
              >
              <th class="border border-[rgba(150,150,150,0.3)] bg-red-700 px-2 py-1.5 text-center font-bold text-white"
                >R3</th
              >
            </tr>
          </thead>
          <tbody>
            {#each matchesData.matches as m}
              {@const isCurrent = m.match === matchesData.current_match}
              {@const isComplete = m.uploaded.every(Boolean)}
              <tr>
                <td
                  class="{matchCellBorder(isCurrent)} px-2 py-1.5 text-center font-bold {isComplete
                    ? 'bg-success/40 text-fg'
                    : 'bg-surface text-fg'} {isCurrent ? 'text-accent' : ''}"
                >
                  {m.match}
                </td>
                {#each m.teams as team, i}
                  <td class="{matchCellBorder(isCurrent)} px-2 py-1.5 text-center {teamCellClass(m.uploaded[i], i, team)}">
                    <div>{team}</div>
                    {#if showScheduledScouts}
                      <div class="text-[10px] {scoutLabelClass(m.scouts[i])}">{m.scouts[i] ?? "—"}</div>
                    {/if}
                  </td>
                {/each}
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  {:else if superMatchesLoading}
    <p class="text-sm text-fg-muted">Loading...</p>
  {:else if superMatchesError}
    <p class="text-sm text-danger">{superMatchesError}</p>
  {:else if superMatchesData.matches.length === 0}
    <p class="text-sm text-fg-muted">No matches in the schedule yet.</p>
  {:else}
    <div class="overflow-x-auto">
      <table class="table-auto border-separate border-spacing-1 text-sm">
        <thead>
          <tr>
            <th class="border border-[rgba(150,150,150,0.3)] bg-neutral px-2 py-1.5 text-center font-bold text-white"
              >Match</th
            >
            <th class="border border-[rgba(150,150,150,0.3)] bg-blue-700 px-2 py-1.5 text-center font-bold text-white"
              >Blue Alliance</th
            >
            <th class="border border-[rgba(150,150,150,0.3)] bg-red-700 px-2 py-1.5 text-center font-bold text-white"
              >Red Alliance</th
            >
          </tr>
        </thead>
        <tbody>
          {#each superMatchesData.matches as m}
            {@const isCurrent = m.match === superMatchesData.current_match}
            {@const isComplete = m.uploaded.every(Boolean)}
            <tr>
              <td
                class="{matchCellBorder(isCurrent)} px-2 py-1.5 text-center font-bold {isComplete
                  ? 'bg-success/40 text-fg'
                  : 'bg-surface text-fg'} {isCurrent ? 'text-accent' : ''}"
              >
                {m.match}
              </td>
              {#each m.teams as teams, i}
                <td
                  class="{matchCellBorder(isCurrent)} px-2 py-1.5 text-center {superAllianceCellClass(
                    m.uploaded[i],
                    i,
                    teams,
                  )}"
                >
                  <div>{teams.join(" / ")}</div>
                  {#if showScheduledScouts}
                    <div class="text-[10px] {scoutLabelClass(m.scouts[i])}">{m.scouts[i] ?? "—"}</div>
                  {/if}
                </td>
              {/each}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
