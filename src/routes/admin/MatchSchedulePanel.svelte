<script lang="ts">
  import MatchSchedule from "@components/MatchSchedule.svelte";

  let {
    forceMatchInput = $bindable(),
    busy,
    message,
    error,
    onRefreshFromTba,
    onGenerateSchedule,
    onAdvanceSchedule,
    onForceMatch,
  }: {
    forceMatchInput: number | string | null;
    busy: "advance" | "force" | "tba" | "generate" | null;
    message: string | null;
    error: string | null;
    onRefreshFromTba: () => void;
    onGenerateSchedule: () => void;
    onAdvanceSchedule: () => void;
    onForceMatch: () => void;
  } = $props();
</script>

<div class="border-t border-border p-4">
  <h2 class="mb-3 font-semibold text-fg">Match Schedule</h2>
  <div class="mb-3 flex flex-wrap items-center gap-2">
    <button class="btn btn-outline btn-sm" onclick={onRefreshFromTba} disabled={busy !== null}>
      {busy === "tba" ? "Refreshing..." : "Refresh From TBA"}
    </button>
    <button class="btn btn-outline btn-sm" onclick={onGenerateSchedule} disabled={busy !== null}>
      {busy === "generate" ? "Generating..." : "Generate Schedule"}
    </button>
    <button class="btn btn-outline btn-sm" onclick={onAdvanceSchedule} disabled={busy !== null}>
      {busy === "advance" ? "Checking..." : "Auto Advance Schedule"}
    </button>
  </div>
  <div class="mb-3 flex items-center gap-2">
    <span class="text-sm text-fg-muted">Force Current Match</span>
    <input type="number" min="1" class="input input-bordered input-sm w-24" bind:value={forceMatchInput} placeholder="#" />
    <button class="btn btn-primary btn-sm" onclick={onForceMatch} disabled={busy !== null}>
      {busy === "force" ? "Forcing..." : "Force Schedule"}
    </button>
  </div>
  {#if message}
    <p class="mb-2 text-sm text-success">{message}</p>
  {/if}
  {#if error}
    <p class="mb-2 text-sm text-danger">{error}</p>
  {/if}
  <MatchSchedule kind="match" showToggle={true} selectable={false} />
</div>
