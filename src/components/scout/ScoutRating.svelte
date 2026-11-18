<script lang="ts">
  import GameSlider from "@components/GameSlider.svelte";

  let {
    values,
    field,
    label,
    color = "range-primary",
  }: {
    values: Record<string, number | string | boolean>;
    field: string;
    label: string;
    color?: string;
  } = $props();
</script>

<label class="flex flex-col gap-1 text-sm text-fg">
  {label}
  <GameSlider
    value={Number(values[field] ?? 0)}
    min={0}
    max={5}
    step={0.5}
    tickCount={6}
    rangeType={color}
    onChange={(v: number) => (values[field] = v)}
  />
</label>
