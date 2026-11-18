<script lang="ts">
  let {
    values,
    field,
    label,
  }: { values: Record<string, number | string | boolean>; field: string; label: string } = $props();
</script>

<label class="flex flex-col gap-1 text-sm text-fg">
  {label}
  <input
    type="number"
    min="0"
    class="input input-bordered"
    value={Number(values[field] ?? 0)}
    oninput={(e) => (values[field] = Number(e.currentTarget.value) || 0)}
  />
</label>
