<script lang="ts">
  import { Capacitor } from "@capacitor/core";
  import { push, location } from "svelte-spa-router";
  import { api } from "@lib/api.svelte";
  import { uploadQueue } from "@lib/upload-queue.svelte";
  import { devTools } from "@lib/dev-tools.svelte";
  import { confirmLeaveScouting } from "@lib/scouting-route";
  import HomeIcon from "./icons/HomeIcon.svelte";

  const isNative = Capacitor.isNativePlatform();

  function goHome(): void {
    if (!confirmLeaveScouting()) return;
    push("/");
  }

  const dotColor: Record<string, string> = {
    connected: "bg-success",
    connecting: "bg-warning",
    disconnected: "bg-danger",
    error: "bg-danger",
  };

  const statusLabel: Record<string, string> = {
    connected: "Connected",
    connecting: "Connecting...",
    disconnected: "Not Connected",
    error: "Error",
  };

  const dot = $derived(isNative ? dotColor[api.status] : "bg-info");
  const label = $derived(isNative ? statusLabel[api.status] : "Web");
</script>

<header class="mb-0 flex items-center justify-between border-b border-border pb-1">
  <div class="flex items-center gap-1.5 text-xs text-fg-muted">
    <span class="h-2 w-2 shrink-0 rounded-full {dot}"></span>
    <span class="font-bold text-fg">Stored: {uploadQueue.items.length}</span>
    <span>{label}</span>
    {#if devTools.showChunkProgress && api.chunkProgress}
      <span>Chunk: {api.chunkProgress.current}/{api.chunkProgress.max}</span>
    {/if}
  </div>
  {#if $location !== "/"}
    <button class="btn btn-ghost btn-s" aria-label="Home" onclick={goHome}>
      <HomeIcon class="h-8 w-8" />
    </button>
  {/if}
</header>
