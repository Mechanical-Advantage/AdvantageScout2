<script lang="ts">
  import { gameData, pushUndoSnapshot } from "./store.svelte";
  import FloorIcon from "./icons/FloorIcon.svelte";
  import TunnelIcon from "./icons/TunnelIcon.svelte";

  type Location = "Floor" | "Tunnel";

  const LOCATIONS: Location[] = ["Floor", "Tunnel"];

  function collect(loc: Location): void {
    pushUndoSnapshot();
    gameData.liveLocation = loc;
  }
</script>

<div class="flex flex-col justify-evenly gap-[100px]">
  {#each LOCATIONS as loc}
    <div class="indicator relative h-[62px] w-[62px]">
      <span
        class="indicator-item badge badge-primary text-base indicator-left indicator-start"
      >
        {loc}
      </span>
      <button
        class="btn btn-square btn-outline btn-accent h-[62px] w-[62px] items-center justify-center {gameData.liveLocation ===
        loc
          ? 'btn-active'
          : ''}"
        onclick={() => collect(loc)}
      >
        {#if loc === "Floor"}
          <FloorIcon />
        {:else if loc === "Tunnel"}
          <TunnelIcon />
        {/if}
      </button>
    </div>
  {/each}
</div>
