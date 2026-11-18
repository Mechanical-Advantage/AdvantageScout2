<script lang="ts">
  import { gameData, pushUndoSnapshot } from "./store.svelte";

  type GameMode = "Auto" | "Tele";

  let { gameMode }: { gameMode: GameMode } = $props();

  const dropField = $derived(`${gameMode}BoulderDrop`);
  const count = $derived(Number(gameData.values[dropField] ?? 0));

  function score(delta: number): void {
    const collect = `${gameMode}${gameData.liveLocation}BoulderCollect`;
    gameData.values[dropField] = Math.max(
      0,
      Number(gameData.values[dropField] ?? 0) + delta,
    );
    gameData.values[collect] = Math.max(
      0,
      Number(gameData.values[collect] ?? 0) + delta,
    );
  }

  function bump(): void {
    pushUndoSnapshot();
    score(1);
  }
</script>

<div class="indicator">
  <button
    class="btn btn-square btn-outline rounded-md relative h-20 w-20"
    onclick={bump}
    title="Drop"
  >
    <span class="indicator-item badge badge-secondary text-2xl py-3">
      {count}
    </span>
    <span
      class="indicator-item badge badge-primary text-base indicator-left indicator-start"
      >Drop</span
    >
    <span>
      <svg
        width="40"
        height="40"
        viewBox="0 0 1024 1024"
        fill="currentColor"
        stroke="currentColor"
        stroke-width="12"
      >
        <path
          d="M692.2 182.2V72.9H327.8v109.3H145.6v72.9h728.8v-72.9H692.2z m-291.5 0v-36.4h218.6v36.4H400.7zM730.8 874.5H289.2l-34.3-548.8-72.8 4.5 38.6 618.5h622.6l38.6-618.5-72.8-4.5-34.3 548.8z"
        />
        <path
          d="M400.7 400.8h72.9v437.3h-72.9zM546.4 400.8h72.9v437.3h-72.9z"
        />
      </svg>
    </span>
  </button>
</div>
