<script lang="ts">
  import { gameData } from "./store.svelte";
  import GameSlider from "@components/GameSlider.svelte";

  const bps = $derived(Number((1000 / gameData.fuelButtonSpeedMs).toFixed(1)));
</script>

<div class="flex flex-col items-center gap-2">
  <button class="btn btn-accent" onclick={() => (gameData.fuelButtonTap = !gameData.fuelButtonTap)}>
    {gameData.fuelButtonTap ? "Switch to BPS" : "Switch to BPT"}
  </button>

  <div class="w-[210px]">
    {#if gameData.fuelButtonTap}
      <p class="mb-1 text-center text-xs text-fg-muted">BPT: {gameData.fuelButtonAmount}</p>
      <GameSlider
        min={2}
        max={10}
        step={2}
        tickLabels={["2", "4", "6", "8", "10"]}
        bind:value={gameData.fuelButtonAmount}
      />
    {:else}
      <p class="mb-1 text-center text-xs text-fg-muted">BPS: {bps}</p>
      <GameSlider
        value={bps}
        min={1}
        max={5}
        step={0.5}
        tickLabels={["1", "1.5", "2", "2.5", "3", "3.5", "4", "4.5", "5"]}
        onChange={(v) => (gameData.fuelButtonSpeedMs = Math.round(1000 / v))}
      />
    {/if}
  </div>
</div>
