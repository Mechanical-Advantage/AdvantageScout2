<script lang="ts">
  // Settings themselves (the "Current Match" row especially) are written by
  // more than just this panel's own Save button -- the schedule actions in
  // MatchSchedulePanel can change "Current Match" server-side too -- so the
  // draft and its load/save are owned by Admin.svelte and just handed down
  // here, rather than this panel re-fetching its own private copy that
  // those other actions would have no way to invalidate.
  let {
    draft,
    loading,
    saving,
    error,
    onSave,
  }: {
    draft: Record<string, string>;
    loading: boolean;
    saving: boolean;
    error: string | null;
    onSave: () => void;
  } = $props();
</script>

<div class="flex-1 p-4">
  <h2 class="mb-3 font-semibold text-fg">Settings</h2>
  {#if loading}
    <p class="text-sm text-fg-muted">Loading...</p>
  {:else}
    {#if Object.keys(draft).length === 0}
      <p class="mb-3 text-sm text-fg-muted">No settings found.</p>
    {:else}
      <div class="mb-4 flex flex-col gap-3">
        {#each Object.keys(draft) as key}
          <div class="flex items-start gap-2">
            <span class="mt-2.5 w-28 shrink-0 text-sm text-fg-muted">{key}</span>
            <input class="input input-bordered input-sm max-w-[400px] flex-1" bind:value={draft[key]} />
          </div>
        {/each}
      </div>
    {/if}
    {#if error}
      <p class="mb-2 text-sm text-danger">{error}</p>
    {/if}
    <button class="btn btn-primary btn-sm" onclick={onSave} disabled={saving || Object.keys(draft).length === 0}>
      {saving ? "Saving..." : "Save Settings"}
    </button>
  {/if}
</div>
