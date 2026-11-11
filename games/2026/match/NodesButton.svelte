<script lang="ts">
  import { gameData, pushUndoSnapshot } from "./store.svelte";

  type GameMode = "Auto" | "Tele";
  type Level = 1 | 2 | 3;
  type ScoreType = "Success" | "Fail";

  let { gameMode, level, type }: { gameMode: GameMode; level: Level; type: ScoreType } = $props();

  const SHIFT_NAMES = ["ST", "S1", "S2", "S3", "S4", "SE"] as const;
  const LEVEL_MAP: Record<Level, string> = { 1: "Hub", 2: "Pass", 3: "Ferry" };
  const LEVEL_DISPLAY: Record<Level, string> = { 1: "Hub", 2: "Pass", 3: "Plow" };

  function shiftName(): string {
    return gameMode === "Auto" ? "" : SHIFT_NAMES[gameData.gameShift];
  }

  function scoreFieldName(): string {
    return `${gameMode}${shiftName()}${LEVEL_MAP[level]}Fuel${type}`;
  }

  function collectFieldName(): string {
    return `${gameMode}${shiftName()}${gameData.liveLocation}FuelCollect`;
  }

  const isSuccess = $derived(type === "Success");
  const fieldName = $derived(scoreFieldName());
  const count = $derived(Number(gameData.values[fieldName] ?? 0));
  const cycleCount = $derived(isSuccess ? gameData.fuelCycleCountSuccess : gameData.fuelCycleCountFail);
  const countBadge = $derived(isSuccess ? "badge-success" : "badge-error");
  let mainPressed = $state(false);
  let undoPressed = $state(false);
  let repeatTimer: ReturnType<typeof setInterval> | null = null;
  let undoRepeatTimer: ReturnType<typeof setInterval> | null = null;

  function score(delta: number): void {
    const field = scoreFieldName();
    const location = collectFieldName();
    gameData.values[field] = Math.max(0, Number(gameData.values[field] ?? 0) + delta);
    gameData.values[location] = Math.max(0, Number(gameData.values[location] ?? 0) + delta);
    if (level === 1) {
      const key = type === "Success" ? "fuelCycleCountSuccess" : "fuelCycleCountFail";
      gameData[key] = Math.max(0, gameData[key] + delta);
    }
  }

  function start() {
    mainPressed = true;
    pushUndoSnapshot();
    if (gameData.fuelButtonTap) {
      score(gameData.fuelButtonAmount);
    } else {
      score(1);
      repeatTimer = setInterval(() => score(1), gameData.fuelButtonSpeedMs);
    }
  }

  function stop() {
    mainPressed = false;
    if (repeatTimer) {
      clearInterval(repeatTimer);
      repeatTimer = null;
    }
  }

  function undoStart() {
    undoPressed = true;
    pushUndoSnapshot();
    score(-1);
    if (!gameData.fuelButtonTap) {
      undoRepeatTimer = setInterval(() => score(-1), gameData.fuelButtonSpeedMs);
    }
  }

  function undoStop() {
    undoPressed = false;
    if (undoRepeatTimer) {
      clearInterval(undoRepeatTimer);
      undoRepeatTimer = null;
    }
  }

</script>

<div class="indicator flex items-center gap-1.5 {isSuccess ? '' : 'flex-row-reverse'}">
  <button
    class="btn btn-square btn-outline rounded-md relative h-20 w-20"
    onpointerdown={start}
    onpointerup={stop}
    onpointerleave={stop}
  >
    {#if level === 1}
      <span class="indicator-item badge badge-accent text-2xl py-3 {isSuccess ? '' : 'indicator-left indicator-start'}">
        {cycleCount}
      </span>
    {/if}
    {#if level === 2 || level === 3}
      <span class="indicator-item badge {countBadge} text-2xl py-3 {isSuccess ? '' : 'indicator-left indicator-start'}">
        {count}
      </span>
    {/if}
    <span
      class="indicator-item badge badge-primary text-base {isSuccess
        ? 'indicator-left indicator-start'
        : 'indicator-right indicator-end'}"
    >
      {LEVEL_DISPLAY[level]}
    </span>
    {#if isSuccess || level === 1 || level === 2}
      <span class="badge {countBadge} p-3 text-2xl">
        {count}
      </span>
    {/if}
  </button>
  <button
    class="btn btn-primary w-10 relative text-2xl"
    onpointerdown={undoStart}
    onpointerup={undoStop}
    onpointerleave={undoStop}
  >
    -
  </button>
</div>
