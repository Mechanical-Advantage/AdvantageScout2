<script lang="ts">
  import { push } from "svelte-spa-router";
  import { getDeviceName, setDeviceName } from "@lib/device";

  let name = $state(getDeviceName());

  function save() {
    if (!name.trim()) return;
    setDeviceName(name.trim());
    push("/");
  }
</script>

<div class="mx-auto max-w-lg">
  <h1 class="mb-2 font-heading text-2xl font-bold text-fg">Device Setup</h1>
  <p class="mb-6 text-sm text-fg-muted">
    Name this device
  </p>

  <form
    class="flex flex-col gap-4"
    onsubmit={(e) => {
      e.preventDefault();
      save();
    }}
  >
    <input
      class="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-fg focus:outline-none"
      type="text"
      bind:value={name}
      placeholder="Device name"
    />
    <button type="submit" class="w-full rounded-md bg-accent py-2.5 font-semibold text-white hover:opacity-90">
      Save
    </button>
  </form>
</div>
