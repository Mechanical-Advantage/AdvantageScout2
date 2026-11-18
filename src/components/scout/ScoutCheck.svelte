<script lang="ts">
  let {
    values,
    field,
    label,
  }: { values: Record<string, number | string | boolean>; field: string; label: string } = $props();
</script>

<label class="label cursor-pointer justify-start gap-2 p-0 text-sm text-fg">
  <input
    type="checkbox"
    class="checkbox checkbox-accent"
    checked={Boolean(values[field])}
    onchange={(e) => (values[field] = e.currentTarget.checked)}
  />
  {label}
</label>
