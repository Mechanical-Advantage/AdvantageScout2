<script lang="ts">
  import type { SuperScout } from "@lib/scouts";
  import PencilIcon from "@components/icons/PencilIcon.svelte";
  import CloseIcon from "@components/icons/CloseIcon.svelte";

  let {
    scouts,
    loading,
    onAdd,
    onEdit,
    onToggle,
    onDelete,
  }: {
    scouts: SuperScout[];
    loading: boolean;
    onAdd: () => void;
    onEdit: (scout: SuperScout) => void;
    onToggle: (scout: SuperScout) => void;
    onDelete: (name: string) => void;
  } = $props();

  const SCOUT_COLLAPSE_THRESHOLD = 12;
  const gridClass = "flex flex-wrap content-start gap-2";
  const chipBase = "flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm transition-[filter] hover:brightness-125";

  let expanded = $state(false);
</script>

<div class="border-t border-border p-4">
  <div class="mb-3 flex items-center justify-between">
    <h2 class="font-semibold text-fg">Super Scouts</h2>
    <button class="btn btn-success btn-sm" onclick={onAdd}>+ Add Super Scout</button>
  </div>
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
        <p class="text-sm text-fg-muted">No super scouts yet.</p>
      {/each}
    </div>
    {#if scouts.length > SCOUT_COLLAPSE_THRESHOLD}
      <button class="btn btn-link btn-sm mt-2 no-underline" onclick={() => (expanded = !expanded)}>
        {expanded ? "Collapse ▲" : `Expand (${scouts.length} total) ▼`}
      </button>
    {/if}
  {/if}
</div>
