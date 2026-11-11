<script lang="ts">
  import type { MatchScout } from "@lib/scouts";
  import PencilIcon from "@components/icons/PencilIcon.svelte";
  import CloseIcon from "@components/icons/CloseIcon.svelte";

  let {
    scouts,
    loading,
    liveSchedule = $bindable(),
    liveScheduleBusy,
    liveScheduleError,
    onAdd,
    onEdit,
    onToggle,
    onDelete,
    onPodChange,
  }: {
    scouts: MatchScout[];
    loading: boolean;
    liveSchedule: boolean;
    liveScheduleBusy: boolean;
    liveScheduleError: string | null;
    onAdd: () => void;
    onEdit: (scout: MatchScout) => void;
    onToggle: (scout: MatchScout) => void;
    onDelete: (name: string) => void;
    onPodChange: (scout: MatchScout, pod: number) => void;
  } = $props();

  const SCOUT_COLLAPSE_THRESHOLD = 12;
  const gridClass = "flex flex-wrap content-start gap-2";
  const chipBase = "flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm transition-[filter] hover:brightness-125";

  let expanded = $state(false);
</script>

<div class="p-4">
  <div class="mb-3 flex items-center justify-between">
    <h2 class="font-semibold text-fg">Match Scouts</h2>
    <button class="btn btn-success btn-sm" onclick={onAdd}>+ Add Scout</button>
  </div>
  <div class="mb-3 flex items-center gap-2">
    <label class="label cursor-pointer gap-2 p-0">
      <input type="checkbox" class="toggle toggle-primary toggle-sm" bind:checked={liveSchedule} />
      <span class="label-text text-sm text-fg">Live Schedule</span>
    </label>
    <span class="text-xs text-fg-muted">
      {#if liveScheduleBusy}
        Regenerating...
      {:else}
        Regenerates the schedule whenever a match scout changes.
      {/if}
    </span>
  </div>
  {#if liveScheduleError}
    <p class="mb-2 text-sm text-danger">{liveScheduleError}</p>
  {/if}
  {#if loading}
    <p class="text-sm text-fg-muted">Loading...</p>
  {:else}
    <div class="{gridClass} {!expanded && scouts.length > SCOUT_COLLAPSE_THRESHOLD ? 'max-h-[104px] overflow-hidden' : ''}">
      {#each scouts as scout}
        <div
          role="button"
          tabindex="0"
          class="tooltip {chipBase} cursor-pointer {scout.active
            ? 'border-success bg-[rgba(46,125,50,0.2)] text-white'
            : 'border-fg-muted bg-[rgba(156,163,175,0.1)] text-fg-muted'}"
          data-tip="Toggle {scout.name}"
          onclick={() => onToggle(scout)}
          onkeydown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              onToggle(scout);
            }
          }}
        >
          <span
            role="button"
            tabindex="0"
            onclick={(e) => {
              e.stopPropagation();
              onEdit(scout);
            }}
            onkeydown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.stopPropagation();
                e.preventDefault();
                onEdit(scout);
              }
            }}
            title="Edit"
            class="opacity-80 hover:opacity-100"
          >
            <PencilIcon class="h-3.5 w-3.5" />
          </span>
          <span class="max-w-[160px] truncate text-left font-medium">{scout.name}</span>
          <span class="flex items-center gap-1 text-xs opacity-80">
            Pod
            <input
              type="number"
              min="1"
              class="w-10 rounded border border-current/30 bg-transparent px-1 py-0.5 text-center text-xs"
              value={scout.pod ?? 1}
              onclick={(e) => e.stopPropagation()}
              onchange={(e) => {
                e.stopPropagation();
                onPodChange(scout, Number(e.currentTarget.value) || 1);
              }}
            />
          </span>
          <span
            role="button"
            tabindex="0"
            class="text-danger hover:opacity-80"
            onclick={(e) => {
              e.stopPropagation();
              onDelete(scout.name);
            }}
            onkeydown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.stopPropagation();
                e.preventDefault();
                onDelete(scout.name);
              }
            }}
            title="Delete"
          >
            <CloseIcon class="h-3.5 w-3.5" />
          </span>
        </div>
      {:else}
        <p class="text-sm text-fg-muted">No match scouts yet.</p>
      {/each}
    </div>
    {#if scouts.length > SCOUT_COLLAPSE_THRESHOLD}
      <button class="btn btn-link btn-sm mt-2 no-underline" onclick={() => (expanded = !expanded)}>
        {expanded ? "Collapse ▲" : `Expand (${scouts.length} total) ▼`}
      </button>
    {/if}
  {/if}
</div>
