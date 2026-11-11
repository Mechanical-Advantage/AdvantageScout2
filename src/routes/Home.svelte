<script lang="ts">
  import { onMount } from "svelte";
  import { push } from "svelte-spa-router";
  import { Capacitor } from "@capacitor/core";
  import { api } from "@lib/api.svelte";
  import { hasDeviceName } from "@lib/device";
  import { scoutingSession, gameFieldsCache, type ScoutingMode } from "@lib/scouting-store.svelte";
  import {
    fetchMatchScouts,
    fetchSuperScouts,
    fetchCurrentMatchSchedule,
    fetchCurrentSuperSchedule,
    fetchGameFields,
    type ScheduleSelection,
    type MatchScheduleRow,
    type SuperScheduleRow,
  } from "@lib/scouts";
  import { getCachedGameFields, setCachedGameFields } from "@lib/game-fields-cache";
  import { checkForFrontendUpdate, frontendUpdateState } from "@lib/frontend-update.svelte";
  import { flushQueue } from "@lib/upload-queue.svelte";
  import { getPreferWifi, setPreferWifi } from "@lib/wifi-preference";
  import { getServerAddress, setServerAddress } from "@lib/server-address";
  import { devTools, setShowChunkProgress } from "@lib/dev-tools.svelte";
  import { SCHEDULE_POLL_INTERVAL } from "@lib/config";
  import MatchSchedule from "@components/MatchSchedule.svelte";

  const isNative = Capacitor.isNativePlatform();

  let error: string | null = $state(null);
  let scoutOptions: { upcoming: string[]; all: string[] } = $state({ upcoming: [], all: [] });
  let currentScheduleRow: MatchScheduleRow | SuperScheduleRow | null = $state(null);
  let optionsOpen = $state(false);
  let advancedOptions = $state(false);
  let updateStatus: string | null = $state(null);
  let preferWifi = $state(getPreferWifi());
  let serverAddress = $state(getServerAddress());

  function togglePreferWifi() {
    preferWifi = !preferWifi;
    setPreferWifi(preferWifi);
  }

  function updateServerAddress(e: Event) {
    serverAddress = (e.currentTarget as HTMLInputElement).value;
    setServerAddress(serverAddress);
  }

  let scoutOptionsRetryTimer: ReturnType<typeof setTimeout> | null = null;

  async function loadScoutOptions() {
    const mode = scoutingSession.mode;
    if (mode !== "match" && mode !== "super") return;
    let scheduleFailed = false;
    const onScheduleError = () => {
      scheduleFailed = true;
      return null;
    };
    try {
      const [scouts, schedule] =
        mode === "match"
          ? await Promise.all([fetchMatchScouts(), fetchCurrentMatchSchedule().catch(onScheduleError)])
          : await Promise.all([fetchSuperScouts(), fetchCurrentSuperSchedule().catch(onScheduleError)]);

      const assigned = new Set<string>();
      if (schedule) {
        const scoutKeys =
          mode === "match"
            ? (["ScoutBlue1", "ScoutBlue2", "ScoutBlue3", "ScoutRed1", "ScoutRed2", "ScoutRed3"] as const)
            : (["ScoutBlue", "ScoutRed"] as const);
        for (const key of scoutKeys) {
          const name = (schedule as unknown as Record<string, unknown>)[key];
          if (typeof name === "string" && name) assigned.add(name);
        }
      }

      currentScheduleRow = schedule ?? null;
      const names = scouts.map((s) => s.name);
      scoutOptions = {
        upcoming: names.filter((n) => assigned.has(n)),
        all: names.filter((n) => !assigned.has(n)).sort(),
      };
    } catch {
      scoutOptions = { upcoming: [], all: [] };
      currentScheduleRow = null;
      scheduleFailed = true;
    } finally {
      if (scheduleFailed) {
        scoutOptionsRetryTimer = setTimeout(loadScoutOptions, SCHEDULE_POLL_INTERVAL);
      }
    }
  }

  async function loadGameFields(mode: ScoutingMode) {
    const cached = getCachedGameFields(mode);
    if (cached) {
      gameFieldsCache.mode = mode;
      gameFieldsCache.data = cached;
    }
    try {
      const fresh = await fetchGameFields(mode);
      if (scoutingSession.mode !== mode) return;
      setCachedGameFields(mode, fresh);
      gameFieldsCache.mode = mode;
      gameFieldsCache.data = fresh;
    } catch {
      // Offline or server unreachable
    }
  }

  $effect(() => {
    loadGameFields(scoutingSession.mode);
  });

  function handleScheduleSelect(sel: ScheduleSelection) {
    scoutingSession.match = String(sel.match);
    scoutingSession.alliance = sel.alliance;
    scoutingSession.scout = sel.scout;
    if (sel.team !== undefined) scoutingSession.team = String(sel.team);
    if (sel.teams) {
      scoutingSession.team1 = String(sel.teams[0] ?? "");
      scoutingSession.team2 = String(sel.teams[1] ?? "");
      scoutingSession.team3 = String(sel.teams[2] ?? "");
    }
  }

  function findScheduleAssignment(name: string): ScheduleSelection | null {
    const mode = scoutingSession.mode;
    if (!currentScheduleRow || (mode !== "match" && mode !== "super")) return null;
    if (mode === "match") {
      const r = currentScheduleRow as MatchScheduleRow;
      for (const alliance of ["Blue", "Red"] as const) {
        for (const i of [1, 2, 3]) {
          const scoutKey = `Scout${alliance}${i}` as keyof MatchScheduleRow;
          if (r[scoutKey] === name) {
            const teamKey = `${alliance}${i}` as keyof MatchScheduleRow;
            return { match: r.Match, alliance, team: Number(r[teamKey]), scout: name };
          }
        }
      }
    } else {
      const r = currentScheduleRow as SuperScheduleRow;
      for (const alliance of ["Blue", "Red"] as const) {
        const scoutKey = `Scout${alliance}` as keyof SuperScheduleRow;
        if (r[scoutKey] === name) {
          const teams = [1, 2, 3].map((i) => Number(r[`${alliance}${i}` as keyof SuperScheduleRow]));
          return { match: r.Match, alliance, teams, scout: name };
        }
      }
    }
    return null;
  }

  $effect(() => {
    const name = scoutingSession.scout;
    if (!name) return;
    const sel = findScheduleAssignment(name);
    if (sel) handleScheduleSelect(sel);
  });

  function startScouting() {
    if (frontendUpdateState.phase) {
      error = "Can't start a match while the app is updating. Please wait for it to finish.";
      return;
    }
    if (scoutingSession.mode !== "pit" && !scoutingSession.scout.trim()) {
      error = "Select a valid scout before starting.";
      return;
    }
    error = null;
    push("/game");
  }

  async function connectBluetooth() {
    try {
      await api.connect();
      flushQueue();
      updateStatus = await checkForFrontendUpdate();
    } catch {
      // api status reflects this
    }
  }

  function clearLocalStorage() {
    localStorage.clear();
    scoutingSession.scout = "";
    scoutingSession.team = "";
    scoutingSession.match = "";
    scoutingSession.alliance = "Red";
    scoutingSession.team1 = "";
    scoutingSession.team2 = "";
    scoutingSession.team3 = "";
    gameFieldsCache.mode = null;
    gameFieldsCache.data = null;
    advancedOptions = false;
    push("/setupmodal");
  }

  $effect(() => {
    scoutingSession.mode;
    loadScoutOptions();
    return () => {
      if (scoutOptionsRetryTimer) clearTimeout(scoutOptionsRetryTimer);
      scoutOptionsRetryTimer = null;
    };
  });

  onMount(() => {
    if (!hasDeviceName()) {
      push("/setupmodal");
    }
  });

  const inputClass = "input input-bordered w-full";
  const selectClass = "select select-bordered w-full";
</script>

{#if frontendUpdateState.phase}
  <div class="mx-auto mb-4 w-full max-w-[300px]">
    <p class="mb-1 text-center text-xs text-fg-muted">
      {frontendUpdateState.phase === "downloading" ? "Downloading update..." : "Installing update..."}
    </p>
    {#if frontendUpdateState.phase === "downloading" && frontendUpdateState.downloadProgress}
      <progress
        class="progress progress-primary w-full"
        value={frontendUpdateState.downloadProgress.current}
        max={frontendUpdateState.downloadProgress.max}
      ></progress>
    {:else}
      <progress class="progress progress-primary w-full"></progress>
    {/if}
  </div>
{/if}

{#if advancedOptions}
  <button class="btn btn-outline btn-sm mb-4" onclick={() => (advancedOptions = false)}>Back</button>
  <div class="mx-auto flex max-w-[200px] flex-col items-center gap-5">
    <button class="btn btn-primary w-full" onclick={connectBluetooth}>BT Connect</button>
    <p class="text-sm text-fg-muted">
      {api.connected ? "Connected" : "Not Connected"}
    </p>
    {#if updateStatus}
      <p class="text-center text-xs text-fg-muted">{updateStatus}</p>
    {/if}
    <label class="flex w-full items-center justify-between gap-3">
      <span class="text-sm text-fg">Prefer Wi-Fi</span>
      <input type="checkbox" class="toggle toggle-primary" checked={preferWifi} onchange={togglePreferWifi} />
    </label>
    <label class="flex w-full items-center justify-between gap-3">
      <span class="text-sm text-fg">Dev Tools: Chunk Progress</span>
      <input
        type="checkbox"
        class="toggle toggle-primary"
        checked={devTools.showChunkProgress}
        onchange={(e) => setShowChunkProgress((e.currentTarget as HTMLInputElement).checked)}
      />
    </label>
    {#if isNative}
      <label class="flex w-full flex-col gap-1">
        <span class="text-sm text-fg">Server Address</span>
        <input
          class="input input-bordered w-full"
          type="text"
          placeholder="127.0.0.1:6328"
          value={serverAddress}
          oninput={updateServerAddress}
        />
      </label>
    {/if}
    <button class="btn btn-outline btn-error w-full" onclick={clearLocalStorage}>Clear local storage</button>
  </div>
{:else}
  <h1 class="mb-2 text-center font-heading text-3xl font-bold text-fg">Advantage Scout</h1>

  <div class="mx-auto flex max-w-[200px] flex-col items-center gap-5">
    <div class="w-full">
      <button class="btn btn-ghost btn-sm" onclick={() => (optionsOpen = !optionsOpen)}>
        <span class="inline-block transition-transform {optionsOpen ? 'rotate-90' : ''}">&#9656;</span>
        Options
      </button>
      {#if optionsOpen}
        <div class="ml-6 mt-1.5 flex flex-col gap-3">
          <button class="btn btn-outline btn-sm w-full" onclick={() => (advancedOptions = true)}>
            Advanced Options
          </button>
          <p class="text-sm font-semibold text-fg">Scouting Mode</p>
          <div class="join w-full">
            {#each ["match", "pit", "super"] as m}
              <button
                class="btn join-item flex-1 capitalize {scoutingSession.mode === m ? 'btn-primary' : 'btn-outline'}"
                onclick={() => (scoutingSession.mode = m as ScoutingMode)}
              >
                {m}
              </button>
            {/each}
          </div>
        </div>
      {/if}
    </div>

    {#if scoutingSession.mode === "match"}
      <select class={selectClass} bind:value={scoutingSession.scout}>
        <option value="" disabled>Choose Scout...</option>
        {#if scoutOptions.upcoming.length}
          <optgroup label="Upcoming Match">
            {#each scoutOptions.upcoming as name}
              <option value={name}>{name}</option>
            {/each}
          </optgroup>
        {/if}
        {#if scoutOptions.all.length}
          <optgroup label="All Scouts">
            {#each scoutOptions.all as name}
              <option value={name}>{name}</option>
            {/each}
          </optgroup>
        {/if}
      </select>
      <input class={inputClass} type="number" placeholder="Set Team" bind:value={scoutingSession.team} />
      <input class={inputClass} type="number" placeholder="Set Match Number" bind:value={scoutingSession.match} />
    {:else if scoutingSession.mode === "super"}
      <select class={selectClass} bind:value={scoutingSession.scout}>
        <option value="" disabled>Choose Scout...</option>
        {#if scoutOptions.upcoming.length}
          <optgroup label="Upcoming Match">
            {#each scoutOptions.upcoming as name}
              <option value={name}>{name}</option>
            {/each}
          </optgroup>
        {/if}
        {#if scoutOptions.all.length}
          <optgroup label="All Scouts">
            {#each scoutOptions.all as name}
              <option value={name}>{name}</option>
            {/each}
          </optgroup>
        {/if}
      </select>
      <input class={inputClass} type="number" placeholder="Set Match Number" bind:value={scoutingSession.match} />
    {/if}

    {#if error}
      <p class="text-danger">{error}</p>
    {/if}

    <button
      class="btn btn-primary w-full {frontendUpdateState.phase ? 'btn-disabled' : ''}"
      onclick={startScouting}
    >
      Start
    </button>
  </div>

  {#if scoutingSession.mode !== "pit"}
    <div class="mx-auto mt-8 w-full max-w-[800px] px-4">
      <MatchSchedule
        kind={scoutingSession.mode}
        showToggle={false}
        selectable={true}
        onSelect={handleScheduleSelect}
      />
    </div>
  {/if}
{/if}
