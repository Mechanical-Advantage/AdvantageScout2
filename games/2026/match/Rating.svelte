<script lang="ts">
  import { gameData } from "./store.svelte";
  import GameSlider from "@components/GameSlider.svelte";

  let {
    field,
    label,
    isDuration = false,
    color = "range-primary",
  }: { field: string; label: string; isDuration?: boolean; color?: string } = $props();

  const durationTicks = ["N/A", "15s", "30s", "60s", "90s", "All"];
  const value = $derived(Number(gameData.values[field] ?? 0));

  function onChange(v: number) {
    gameData.values[field] = v;
  }
</script>

<label class="flex flex-col gap-1 text-sm text-fg">
  {label}
  {#if isDuration}
    <GameSlider {value} min={0} max={5} step={1} tickLabels={durationTicks} rangeType={color} {onChange} />
  {:else}
    <GameSlider {value} min={0} max={5} step={0.5} tickCount={6} rangeType={color} {onChange} />
  {/if}
</label>
