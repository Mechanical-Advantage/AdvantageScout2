<script lang="ts">
  import { gameData, pushUndoSnapshot } from "./store.svelte";
  import FloorIcon from "./icons/FloorIcon.svelte";
  import NeutralIcon from "./icons/NeutralIcon.svelte";
  import OutpostIcon from "./icons/OutpostIcon.svelte";

  type GameMode = "Auto" | "Tele";
  type Location = "Outpost" | "Floor" | "Neutral" | "PreLoaded";

  let { gameMode }: { gameMode: GameMode } = $props();

  const locations = $derived(
    gameMode === "Auto" ? (["Outpost", "Floor", "Neutral"] as Location[]) : (["Outpost", "Floor"] as Location[]),
  );

  function collect(loc: Location): void {
    pushUndoSnapshot();
    gameData.liveLocation = loc;
    gameData.fuelCycleCountSuccess = 0;
    gameData.fuelCycleCountFail = 0;
  }
</script>

<div class="flex flex-col justify-evenly gap-[100px]">
  {#each locations as loc}
    <div class="indicator relative h-[62px] w-[62px]">
      <span class="indicator-item badge badge-primary text-base indicator-left indicator-start">
        {loc}
      </span>
      <button
        class="btn btn-square btn-outline btn-accent h-[62px] w-[62px] items-center justify-center"
        onclick={() => collect(loc)}
      >
        {#if loc === "Floor"}
          <FloorIcon />
        {:else if loc === "Neutral"}
          <NeutralIcon />
        {:else if loc === "Outpost"}
          <OutpostIcon />
        {/if}
      </button>
    </div>
  {/each}
</div>
