<script lang="ts">
  import type { Component } from "svelte";
  import { gameData, pushUndoSnapshot } from "./store.svelte";

  type GameMode = "Auto" | "Tele";
  type ScoreType = "Success" | "Fail";

  let {
    gameMode,
    node,
    type,
    label,
    icon,
    trackCollect = false,
  }: {
    gameMode: GameMode;
    node: string;
    type: ScoreType;
    label: string;
    icon: Component;
    trackCollect?: boolean;
  } = $props();

  function fieldName(): string {
    return `${gameMode}${node}${type}`;
  }

  function collectFieldName(): string {
    return `${gameMode}${gameData.liveLocation}BoulderCollect`;
  }

  const isSuccess = $derived(type === "Success");
  const count = $derived(Number(gameData.values[fieldName()] ?? 0));
  const countBadge = $derived(isSuccess ? "badge-success" : "badge-error");
  const Icon = $derived(icon);

  function score(delta: number): void {
    const field = fieldName();
    gameData.values[field] = Math.max(0, Number(gameData.values[field] ?? 0) + delta);
    if (trackCollect) {
      const location = collectFieldName();
      gameData.values[location] = Math.max(0, Number(gameData.values[location] ?? 0) + delta);
    }
  }

  function bump(): void {
    pushUndoSnapshot();
    score(1);
  }

</script>

<div class="indicator">
  <button class="btn btn-square btn-outline rounded-md relative h-20 w-20" onclick={bump} title="{label} {type}">
    <span class="indicator-item badge {countBadge} text-2xl py-3 {isSuccess ? '' : 'indicator-left indicator-start'}">
      {count}
    </span>
      <span
        class="indicator-item badge badge-primary text-base {isSuccess
          ? 'indicator-left indicator-start'
          : 'indicator-right indicator-end'}"
      >
        {label}
      </span>
    <span class={isSuccess ? "text-success" : "text-error"}>
      <Icon />
    </span>
  </button>
</div>
