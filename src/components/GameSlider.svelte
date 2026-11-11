<script lang="ts">
  let {
    value = $bindable(0),
    min,
    max,
    step,
    tickLabels,
    tickCount,
    onChange,
    rangeType = "range-primary",
  }: {
    value: number;
    min: number;
    max: number;
    step: number;
    tickLabels?: string[];
    tickCount?: number;
    onChange?: (value: number) => void;
    rangeType?: string;
  } = $props();

  const marks = $derived(tickLabels?.length ?? tickCount ?? 0);
  const displayIndex = $derived(tickLabels ? Math.round((value - min) / ((max - min) / (tickLabels.length - 1))) : -1);
</script>

<div class="w-full">
  <input
    type="range"
    class="range {rangeType} w-full [--range-thumb:black]"
    {min}
    {max}
    {step}
    {value}
    oninput={(e) => {
      value = Number(e.currentTarget.value);
      onChange?.(value);
    }}
  />
  {#if marks > 0}
    <div class="flex w-full justify-between px-1 text-[8px] leading-none text-fg-muted/50">
      {#each { length: marks }}
        <span>|</span>
      {/each}
    </div>
  {/if}
  {#if tickLabels}
    <div class="flex w-full justify-between px-1 text-[10px] text-fg-muted">
      {#each tickLabels as tick, i}
        <span class={i === displayIndex ? "font-bold text-fg" : ""}>{tick}</span>
      {/each}
    </div>
  {:else}
    <div class="mt-0.5 text-right text-xs tabular-nums text-fg-muted">{value.toFixed(1)}</div>
  {/if}
</div>
