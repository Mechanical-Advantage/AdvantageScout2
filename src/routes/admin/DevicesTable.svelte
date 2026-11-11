<script lang="ts">
  import type { DeviceInfo } from "@lib/scouts";
  import PencilIcon from "@components/icons/PencilIcon.svelte";
  import MessageIcon from "@components/icons/MessageIcon.svelte";

  let {
    devices,
    devicesError,
    showInitialSpinner,
    now,
    clockOffset,
    onRemoveDevice,
    onEditDevice,
    onMessageDevices,
  }: {
    devices: DeviceInfo[];
    devicesError: string | null;
    showInitialSpinner: boolean;
    now: number;
    clockOffset: number;
    onRemoveDevice: (name: string) => Promise<void>;
    onEditDevice: (name: string) => void;
    onMessageDevices: (names: string[]) => void;
  } = $props();

  const FILTER_OPTIONS = [
    { label: "All Modes", value: "all" },
    { label: "Match Scouting", value: "match" },
    { label: "Super Scouting", value: "super" },
    { label: "Pit Scouting", value: "pit" },
    { label: "Idle", value: "idle" },
  ];

  let filterMode = $state("all");
  let selectionMode = $state(false);
  let selectedDevices: string[] = $state([]);
  let deletingDevices: string[] = $state([]);

  const filteredDevices = $derived(
    devices.filter((d) => filterMode === "all" || (d.LastHeartbeat?.mode || "idle") === filterMode),
  );

  function lastSeen(device: DeviceInfo): { text: string; stale: boolean } {
    const ts = device.LastHeartbeat?.timestamp;
    if (!ts) return { text: "N/A", stale: false };
    const seconds = Math.floor((now + clockOffset - ts) / 1000);
    return { text: `${Math.max(0, seconds)}s`, stale: seconds > 10 };
  }

  function cap(s: string | undefined): string {
    if (!s) return "N/A";
    return s.charAt(0).toUpperCase() + s.slice(1);
  }

  function toggleSelectionMode() {
    selectionMode = !selectionMode;
    if (!selectionMode) selectedDevices = [];
  }

  function toggleDeviceSelected(name: string) {
    selectedDevices = selectedDevices.includes(name)
      ? selectedDevices.filter((n) => n !== name)
      : [...selectedDevices, name];
  }

  async function handleRemoveDevice(name: string) {
    deletingDevices = [...deletingDevices, name];
    try {
      await onRemoveDevice(name);
    } finally {
      deletingDevices = deletingDevices.filter((n) => n !== name);
    }
  }

  function handleBulkMessage() {
    onMessageDevices(selectedDevices);
  }

  // Called by Admin.svelte (via bind:this) once a bulk message actually
  // sends -- selection state lives here, not in the parent, but exiting
  // selection mode after a successful bulk send is still this table's own
  // business to finish.
  export function clearSelection(): void {
    selectionMode = false;
    selectedDevices = [];
  }
</script>

<div class="flex items-center justify-between px-1 py-3">
  <div class="flex items-center gap-3">
    <span class="text-sm font-semibold text-fg">Filter Devices:</span>
    <select class="select select-bordered select-sm max-w-[200px]" bind:value={filterMode}>
      {#each FILTER_OPTIONS as opt}
        <option value={opt.value}>{opt.label}</option>
      {/each}
    </select>
  </div>
  <div class="flex items-center gap-2">
    {#if selectionMode && selectedDevices.length > 0}
      <button class="btn btn-primary btn-sm" onclick={handleBulkMessage}>
        Message ({selectedDevices.length})
      </button>
    {/if}
    <button class="btn btn-outline btn-sm" onclick={toggleSelectionMode}>
      {selectionMode ? "Cancel" : "Select"}
    </button>
  </div>
</div>

<div class="overflow-x-auto">
  <table class="table-auto w-full min-w-[900px] border-separate border-spacing-2 text-sm">
    <thead>
      <tr class="border-b-2 border-accent bg-surface text-left">
        {#if selectionMode}<th class="w-8 px-2 py-2"></th>{/if}
        <th class="px-2 py-2 font-semibold text-fg">Device</th>
        <th class="px-2 py-2 font-semibold text-fg">Platform</th>
        <th class="px-2 py-2 font-semibold text-fg">Version</th>
        <th class="px-2 py-2 text-center font-semibold text-fg">Last Seen</th>
        <th class="px-2 py-2 font-semibold text-fg">Scout</th>
        <th class="px-2 py-2 font-semibold text-fg">Team</th>
        <th class="px-2 py-2 font-semibold text-fg">Alliance</th>
        <th class="px-2 py-2 font-semibold text-fg">Match</th>
        <th class="px-2 py-2 font-semibold text-fg">Mode</th>
        <th class="px-2 py-2"></th>
        <th class="w-10 px-2 py-2"></th>
      </tr>
    </thead>
    <tbody>
      {#each filteredDevices as device}
        {@const hb = device.LastHeartbeat}
        {@const seen = lastSeen(device)}
        {@const isSelected = selectedDevices.includes(device.Name)}
        {@const isDeleting = deletingDevices.includes(device.Name)}
        <tr
          class="border-b border-border {isDeleting ? 'opacity-50' : ''} {isSelected ? 'bg-[rgba(92,107,192,0.15)]' : ''} {selectionMode
            ? 'cursor-pointer'
            : ''}"
          onclick={() => selectionMode && toggleDeviceSelected(device.Name)}
        >
          {#if selectionMode}
            <td class="px-2 py-2 text-center">
              <input
                type="checkbox"
                class="checkbox checkbox-accent checkbox-sm"
                checked={isSelected}
                onclick={(e) => e.stopPropagation()}
                onchange={() => toggleDeviceSelected(device.Name)}
              />
            </td>
          {/if}
          <td class="px-2 py-2 text-fg">
            <span class="inline-flex items-center gap-1.5">
              {device.Name}
              {#if !selectionMode}
                <button
                  class="btn btn-ghost btn-xs text-accent"
                  onclick={(e) => {
                    e.stopPropagation();
                    onEditDevice(device.Name);
                  }}
                  title="Edit"
                >
                  <PencilIcon class="h-3.5 w-3.5" />
                </button>
              {/if}
            </span>
          </td>
          <td class="px-2 py-2 text-fg-muted">{cap(hb?.platform)}</td>
          <td class="px-2 py-2 text-fg-muted">{hb?.version ?? "N/A"}</td>
          <td class="px-2 py-2 text-center {seen.stale ? 'font-bold text-danger' : 'text-fg-muted'}">{seen.text}</td>
          <td class="px-2 py-2 text-fg-muted">{hb?.scout ?? "N/A"}</td>
          <td class="px-2 py-2 text-fg-muted">{hb?.team ?? "N/A"}</td>
          <td class="px-2 py-2 text-fg-muted">{cap(hb?.alliance)}</td>
          <td class="px-2 py-2 text-fg-muted">{hb?.match ?? "N/A"}</td>
          <td class="px-2 py-2 text-fg-muted">{cap(hb?.mode ?? "idle")}</td>
          <td class="px-2 py-2 text-center">
            {#if isDeleting}
              <span class="text-xs text-fg-muted">...</span>
            {:else}
              <button
                class="btn btn-ghost btn-xs text-danger"
                onclick={(e) => {
                  e.stopPropagation();
                  handleRemoveDevice(device.Name);
                }}
              >
                Remove
              </button>
            {/if}
          </td>
          <td class="px-2 py-2 text-center">
            {#if !selectionMode}
              <button
                class="btn btn-ghost btn-xs text-accent"
                onclick={(e) => {
                  e.stopPropagation();
                  onMessageDevices([device.Name]);
                }}
                title="Message"
              >
                <MessageIcon class="h-3.5 w-3.5" />
              </button>
            {/if}
          </td>
        </tr>
      {:else}
        <tr>
          <td colspan="12" class="p-8 text-center text-sm text-fg-muted">
            {#if showInitialSpinner}
              Loading...
            {:else if devices.length === 0}
              No devices connected yet.
            {:else}
              No devices match this filter.
            {/if}
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>
{#if devicesError}
  <p class="mt-2 text-sm text-danger">{devicesError}</p>
{/if}
