<script lang="ts">
  import { gameData } from "./store.svelte";
  import { push } from "svelte-spa-router";
  import { getDeviceName } from "@lib/device";
  import { scoutingSession } from "@lib/scouting-store.svelte";
  import { queueSubmission } from "@lib/upload-queue.svelte";
  import Rating from "./Rating.svelte";

  function sanitizeComment(value: unknown): string {
    const raw = typeof value === "string" ? value : "";
    const stripped = raw.replace(/[^\x00-\x7F]/g, "");
    return stripped.trim() === "" ? "" : stripped;
  }

  function buildPayloadRow(): Record<string, unknown> {
    return {
      ...gameData.values,
      PostgameComment: sanitizeComment(gameData.values["PostgameComment"]),
      Mode: "match",
      Device: getDeviceName(),
      Scout: scoutingSession.scout,
      Team: Number(scoutingSession.team),
      Match: Number(scoutingSession.match),
      Alliance: scoutingSession.alliance,
    };
  }

  function submitMatch(): void {
    queueSubmission(buildPayloadRow());
    gameData.values = {};
    gameData.activeTab = 0;
    gameData.preMatchDone = false;
    gameData.liveLocation = "PreLoaded";
  }

  const botStateOptions = [
    { value: 1, label: "No Issues", radioClass: "radio-success" },
    { value: 2, label: "Comms Issue", radioClass: "radio-warning" },
    { value: 3, label: "Power Issues", radioClass: "radio-warning" },
    { value: 4, label: "Major Malfunction", radioClass: "radio-warning" },
    { value: 5, label: "Fell Over", radioClass: "radio-error" },
    { value: 6, label: "Did Not Show", radioClass: "radio-error" },
  ];

  const botState = $derived(Number(gameData.values["PostgameBotState"] ?? 1));
  const comment = $derived(String(gameData.values["PostgameComment"] ?? ""));
  const canUpload = $derived(comment.trim().length >= 14);

  let uploading = $state(false);

  function upload() {
    if (!canUpload || uploading) return;
    uploading = true;
    submitMatch();
    push("/");
  }
</script>

<div class="absolute left-[20px] top-[20px] flex w-[260px] flex-col gap-2.5">
  <p class="text-xs font-semibold text-fg-muted">Ratings</p>
  <Rating field="PostgameDriverRating" label="Driver" color="range-primary" />
  <Rating
    field="PostgameBoulderIntakeRating"
    label="Boulder Intake"
    color="range-primary"
  />
  <Rating field="PostgameDefenseRating" label="Defense" color="range-success" />
  <Rating
    field="PostgameUnderDefenseRating"
    label="Under Defense"
    color="range-error"
  />
  <Rating
    field="PostgamePlayingDefenseDuration"
    label="Playing Defense"
    color="range-success"
    isDuration
  />
  <Rating
    field="PostgameUnderDefenseDuration"
    label="Under Defense"
    color="range-error"
    isDuration
  />
</div>

<div class="absolute left-[310px] top-[20px] flex w-[340px] flex-col gap-1">
  <p class="text-xs font-semibold text-fg-muted">Defense Crossing</p>
  <div class="grid grid-cols-2 gap-x-4 gap-y-2.5">
    <Rating field="PostgameLowbarCrossRating" label="Low Bar" color="range-secondary" />
    <Rating field="PostgamePortCrossRating" label="Portcullis" color="range-secondary" />
    <Rating field="PostgameChevalCrossRating" label="Cheval" color="range-secondary" />
    <Rating field="PostgameMoatCrossRating" label="Moat" color="range-secondary" />
    <Rating field="PostgameRampartsCrossRating" label="Ramparts" color="range-secondary" />
    <Rating field="PostgameDrawCrossRating" label="Drawbridge" color="range-secondary" />
    <Rating field="PostgameSallyCrossRating" label="Sally" color="range-secondary" />
    <Rating field="PostgameWallCrossRating" label="Wall" color="range-secondary" />
    <Rating field="PostgameTerrainCrossRating" label="Terrain" color="range-secondary" />
  </div>
</div>

<div class="absolute left-[700px] top-[20px] flex w-[300px] flex-col gap-2">
  <p class="text-xs font-semibold text-fg-muted">Notes</p>
  <textarea
    class="textarea textarea-bordered min-h-20"
    placeholder="15 characters or more..."
    value={comment}
    oninput={(e) =>
      (gameData.values["PostgameComment"] = e.currentTarget.value)}
  ></textarea>

  <p class="text-sm text-fg">Bot State</p>
  <div class="flex flex-wrap gap-x-3 gap-y-1">
    {#each botStateOptions as opt}
      <label class="label cursor-pointer justify-start gap-1.5 p-0">
        <input
          type="radio"
          name="botstate"
          class="radio radio-sm {opt.radioClass}"
          checked={botState === opt.value}
          onchange={() => (gameData.values["PostgameBotState"] = opt.value)}
        />
        <span class="label-text text-xs text-fg">{opt.label}</span>
      </label>
    {/each}
  </div>

  <label class="flex items-center gap-2 text-sm text-fg">
    Penalties
    <input
      type="number"
      min="0"
      class="input input-bordered input-sm w-20"
      value={Number(gameData.values["PostgamePenalties"] ?? 0)}
      oninput={(e) =>
        (gameData.values["PostgamePenalties"] =
          Number(e.currentTarget.value) || 0)}
    />
  </label>

  <button
    class="btn {canUpload ? 'btn-accent' : 'btn-disabled'} mt-1 w-full"
    disabled={uploading}
    onclick={upload}
  >
    {uploading ? "Uploading..." : "Upload"}
  </button>
  {#if !canUpload}
    <p class="text-center text-xs text-fg-muted">
      {14 - comment.trim().length} more chars needed
    </p>
  {/if}
</div>
