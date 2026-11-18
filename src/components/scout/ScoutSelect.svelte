<script lang="ts">
  let {
    values,
    field,
    label,
    options,
  }: {
    values: Record<string, number | string | boolean>;
    field: string;
    label: string;
    options: string[];
  } = $props();
</script>

<label class="flex flex-col gap-1 text-sm text-fg">
  {label}
  <select
    class="select select-bordered"
    value={String(values[field] ?? "")}
    onchange={(e) => (values[field] = e.currentTarget.value)}
  >
    <option value="" disabled>Select...</option>
    {#each options as option}
      <option value={option}>{option}</option>
    {/each}
  </select>
</label>
