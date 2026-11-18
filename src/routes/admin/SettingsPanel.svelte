<script lang="ts">
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
            <span class="mt-2.5 w-28 shrink-0 text-sm text-fg-muted">{key}</span
            >
            <input
              class="input input-bordered input-sm max-w-[400px] flex-1"
              bind:value={draft[key]}
            />
          </div>
        {/each}
      </div>
    {/if}
    {#if error}
      <p class="mb-2 text-sm text-danger">{error}</p>
    {/if}
    <button
      class="btn btn-primary btn-sm"
      onclick={onSave}
      disabled={saving || Object.keys(draft).length === 0}
    >
      {saving ? "Saving..." : "Save Settings"}
    </button>
  {/if}
</div>
