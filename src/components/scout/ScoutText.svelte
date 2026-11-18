<script lang="ts">
  let {
    values,
    field,
    label,
    multiline = false,
    placeholder = "",
  }: {
    values: Record<string, number | string | boolean>;
    field: string;
    label: string;
    multiline?: boolean;
    placeholder?: string;
  } = $props();
</script>

<label class="flex flex-col gap-1 text-sm text-fg">
  {label}
  {#if multiline}
    <textarea
      class="textarea textarea-bordered min-h-24"
      {placeholder}
      value={String(values[field] ?? "")}
      oninput={(e) => (values[field] = e.currentTarget.value)}
    ></textarea>
  {:else}
    <input
      type="text"
      class="input input-bordered"
      {placeholder}
      value={String(values[field] ?? "")}
      oninput={(e) => (values[field] = e.currentTarget.value)}
    />
  {/if}
</label>
