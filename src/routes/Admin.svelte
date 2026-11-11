<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import {
    fetchGlobalSettings,
    saveGlobalSettings,
    fetchMatchScouts,
    upsertMatchScout,
    removeMatchScout,
    fetchSuperScouts,
    upsertSuperScout,
    removeSuperScout,
    fetchDevices,
    removeDevice,
    sendMessagesToDevices,
    advanceScheduleCheck,
    forceCurrentMatch,
    refreshScheduleFromTba,
    generateSchedule,
    fetchAllMatchesStatus,
    fetchAllSuperMatchesStatus,
    type MatchScout,
    type SuperScout,
    type DeviceInfo,
    type AllMatchesStatus,
    type AllSuperMatchesStatus,
  } from "@lib/scouts";
  import { HEARTBEAT_INTERVAL } from "@lib/config";
  import SettingsPanel from "./admin/SettingsPanel.svelte";
  import MatchScoutsPanel from "./admin/MatchScoutsPanel.svelte";
  import SuperScoutsPanel from "./admin/SuperScoutsPanel.svelte";
  import MatchSchedulePanel from "./admin/MatchSchedulePanel.svelte";
  import ScoutModal from "./admin/ScoutModal.svelte";
  import EditDeviceModal from "./admin/EditDeviceModal.svelte";
  import MessageModal from "./admin/MessageModal.svelte";
  import DevicesTable from "./admin/DevicesTable.svelte";
  import MatchesTable from "./admin/MatchesTable.svelte";

  let settingsDraft: Record<string, string> = $state({});
  let settingsLoading = $state(true);
  let settingsSaving = $state(false);
  let settingsError: string | null = $state(null);

  let matchScouts: MatchScout[] = $state([]);
  let matchScoutsLoading = $state(true);
  let superScouts: SuperScout[] = $state([]);
  let superScoutsLoading = $state(true);

  let devices: DeviceInfo[] = $state([]);
  let devicesError: string | null = $state(null);
  let showInitialSpinner = $state(true);

  let now = $state(Date.now());

  let clockOffset = $state(0);

  let forceMatchInput: number | string | null = $state(null);
  let scheduleBusy: "advance" | "force" | "tba" | "generate" | null = $state(null);
  let scheduleMessage: string | null = $state(null);
  let scheduleError: string | null = $state(null);

  async function handleAdvanceSchedule() {
    scheduleBusy = "advance";
    scheduleError = null;
    scheduleMessage = null;
    try {
      const result = await advanceScheduleCheck();
      scheduleMessage = result.advanced
        ? `Advanced to match ${result.current_match}.`
        : `Current match is still ${result.current_match}.`;
      await loadMatchesTable();

      if (result.advanced) await loadSettings();
    } catch (e) {
      scheduleError = e instanceof Error ? e.message : String(e);
    } finally {
      scheduleBusy = null;
    }
  }

  async function handleForceMatch() {
    const match = Number(forceMatchInput);
    if (!Number.isFinite(match) || match < 1) {
      scheduleError = "Enter a valid match number.";
      return;
    }
    scheduleBusy = "force";
    scheduleError = null;
    scheduleMessage = null;
    try {
      const result = await forceCurrentMatch(match);
      scheduleMessage = `Current match forced to ${result.current_match}.`;
      await loadMatchesTable();
      await loadSettings();
    } catch (e) {
      scheduleError = e instanceof Error ? e.message : String(e);
    } finally {
      scheduleBusy = null;
    }
  }

  async function handleRefreshFromTba() {
    scheduleBusy = "tba";
    scheduleError = null;
    scheduleMessage = null;
    try {
      await refreshScheduleFromTba();
      scheduleMessage = "Schedule refreshed from TBA.";
      await loadMatchesTable();
    } catch (e) {
      scheduleError = e instanceof Error ? e.message : String(e);
    } finally {
      scheduleBusy = null;
    }
  }

  async function handleGenerateSchedule() {
    scheduleBusy = "generate";
    scheduleError = null;
    scheduleMessage = null;
    try {
      await generateSchedule();
      scheduleMessage = "Schedule regenerated.";
      await loadMatchesTable();
    } catch (e) {
      scheduleError = e instanceof Error ? e.message : String(e);
    } finally {
      scheduleBusy = null;
    }
  }

  let scoutModal: { kind: "match" | "super"; editing: string | null; name: string; pod: string } | null =
    $state(null);
  let editDeviceModal: { device: string; rename: string; error: string; busy: boolean } | null = $state(null);
  let messageModal: { targets: string[]; text: string; centered: boolean; sending: boolean } | null = $state(null);

  async function loadSettings() {
    try {
      const data = await fetchGlobalSettings();
      settingsDraft = Object.fromEntries(Object.entries(data).map(([k, v]) => [k, String(v)]));
    } catch (e) {
      settingsError = e instanceof Error ? e.message : String(e);
    } finally {
      settingsLoading = false;
    }
  }

  async function saveSettings() {
    settingsSaving = true;
    settingsError = null;
    try {
      await saveGlobalSettings(settingsDraft);
      await loadSettings();
    } catch (e) {
      settingsError = e instanceof Error ? e.message : String(e);
    } finally {
      settingsSaving = false;
    }
  }

  async function loadMatchScouts() {
    try {
      matchScouts = (await fetchMatchScouts()).sort((a, b) => a.name.localeCompare(b.name));
    } finally {
      matchScoutsLoading = false;
    }
  }

  async function loadSuperScouts() {
    try {
      superScouts = (await fetchSuperScouts()).sort((a, b) => a.name.localeCompare(b.name));
    } finally {
      superScoutsLoading = false;
    }
  }

  async function loadDevices() {
    try {
      const before = Date.now();
      const response = await fetchDevices();
      devices = response.devices;

      const roundTrip = Date.now() - before;
      clockOffset = response.serverTime - (before + roundTrip / 2);
      devicesError = null;
    } catch (e) {
      devicesError = e instanceof Error ? e.message : String(e);
    } finally {
      showInitialSpinner = false;
    }
  }

  let allMatchesData: AllMatchesStatus = $state({ current_match: 0, matches: [] });
  let allMatchesLoading = $state(true);
  let allMatchesError: string | null = $state(null);
  let allSuperMatchesData: AllSuperMatchesStatus = $state({ current_match: 0, matches: [] });
  let allSuperMatchesLoading = $state(true);
  let allSuperMatchesError: string | null = $state(null);
  let matchesTableMode: "match" | "super" = $state("match");

  async function loadAllMatches() {
    try {
      allMatchesData = await fetchAllMatchesStatus();
      allMatchesError = null;
    } catch (e) {
      allMatchesError = e instanceof Error ? e.message : String(e);
    } finally {
      allMatchesLoading = false;
    }
  }

  async function loadAllSuperMatches() {
    try {
      allSuperMatchesData = await fetchAllSuperMatchesStatus();
      allSuperMatchesError = null;
    } catch (e) {
      allSuperMatchesError = e instanceof Error ? e.message : String(e);
    } finally {
      allSuperMatchesLoading = false;
    }
  }

  function loadMatchesTable(): Promise<void> {
    return matchesTableMode === "match" ? loadAllMatches() : loadAllSuperMatches();
  }

  function setMatchesTableMode(mode: "match" | "super") {
    if (matchesTableMode === mode) return;
    matchesTableMode = mode;
    loadMatchesTable();
  }

  const inactiveMatchScouts = $derived(new Set(matchScouts.filter((s) => !s.active).map((s) => s.name)));
  const inactiveSuperScouts = $derived(new Set(superScouts.filter((s) => !s.active).map((s) => s.name)));

  function openAddScout(kind: "match" | "super") {
    scoutModal = { kind, editing: null, name: "", pod: "1" };
  }

  function openEditMatchScout(scout: MatchScout) {
    scoutModal = { kind: "match", editing: scout.name, name: scout.name, pod: String(scout.pod ?? 1) };
  }

  function openEditSuperScout(scout: SuperScout) {
    scoutModal = { kind: "super", editing: scout.name, name: scout.name, pod: "1" };
  }

  let liveSchedule = $state(false);
  let liveScheduleBusy = $state(false);
  let liveScheduleError: string | null = $state(null);

  async function regenerateScheduleIfLive() {
    if (!liveSchedule) return;
    liveScheduleBusy = true;
    liveScheduleError = null;
    try {
      await generateSchedule();
      await loadMatchesTable();
    } catch (e) {
      liveScheduleError = e instanceof Error ? e.message : String(e);
    } finally {
      liveScheduleBusy = false;
    }
  }

  async function saveScoutModal() {
    if (!scoutModal) return;
    const { kind, editing, name, pod } = scoutModal;
    const trimmed = name.trim();
    if (!trimmed) return;

    if (kind === "match") {
      const current = editing ? matchScouts.find((s) => s.name === editing) : null;
      if (editing && editing !== trimmed) await removeMatchScout(editing);
      await upsertMatchScout(trimmed, current?.active ?? true, Number(pod) || 1);
      await loadMatchScouts();
      await regenerateScheduleIfLive();
    } else {
      const current = editing ? superScouts.find((s) => s.name === editing) : null;
      if (editing && editing !== trimmed) await removeSuperScout(editing);
      await upsertSuperScout(trimmed, current?.active ?? true);
      await loadSuperScouts();
    }
    scoutModal = null;
  }

  async function toggleMatchScout(scout: MatchScout) {
    await upsertMatchScout(scout.name, !scout.active, scout.pod);
    await loadMatchScouts();
    await regenerateScheduleIfLive();
  }

  async function toggleSuperScout(scout: SuperScout) {
    await upsertSuperScout(scout.name, !scout.active);
    await loadSuperScouts();
  }

  async function deleteMatchScout(name: string) {
    await removeMatchScout(name);
    await loadMatchScouts();
    await regenerateScheduleIfLive();
  }

  async function deleteSuperScout(name: string) {
    await removeSuperScout(name);
    await loadSuperScouts();
  }

  async function handlePodChange(scout: MatchScout, pod: number) {
    await upsertMatchScout(scout.name, scout.active, pod);
    await loadMatchScouts();
    await regenerateScheduleIfLive();
  }

  async function handleRemoveDevice(name: string) {
    await removeDevice(name);
    await loadDevices();
  }

  function openEditDeviceModal(name: string) {
    editDeviceModal = { device: name, rename: name, error: "", busy: false };
  }

  async function handleRename() {
    const modal = editDeviceModal;
    if (!modal) return;
    const trimmed = modal.rename.trim();
    if (!trimmed) {
      modal.error = "Name cannot be empty";
      return;
    }
    modal.busy = true;
    try {
      await sendMessagesToDevices([{ device: modal.device, type: "rename_device", content: trimmed }]);
      await loadDevices();
      editDeviceModal = null;
    } catch (e) {
      modal.error = e instanceof Error ? e.message : String(e);
      modal.busy = false;
    }
  }

  async function handleClearStorage() {
    const modal = editDeviceModal;
    if (!modal) return;
    modal.busy = true;
    try {
      await sendMessagesToDevices([{ device: modal.device, type: "clear_storage", content: "" }]);
      editDeviceModal = null;
    } catch (e) {
      modal.error = e instanceof Error ? e.message : String(e);
      modal.busy = false;
    }
  }

  let devicesTableRef: DevicesTable;

  function openMessageModal(targets: string[]) {
    if (targets.length === 0) return;
    messageModal = { targets, text: "", centered: false, sending: false };
  }

  async function handleSendMessage() {
    const modal = messageModal;
    if (!modal) return;
    const trimmed = modal.text.trim();
    if (!trimmed) return;
    modal.sending = true;
    try {
      const type = modal.centered ? "toast_center" : "toast";
      await sendMessagesToDevices(modal.targets.map((device) => ({ device, type, content: trimmed })));
      const wasBulk = modal.targets.length > 1;
      messageModal = null;
      if (wasBulk) devicesTableRef?.clearSelection();
    } catch {
      modal.sending = false;
    }
  }

  let deviceInterval: ReturnType<typeof setInterval>;
  let tickInterval: ReturnType<typeof setInterval>;
  let allMatchesInterval: ReturnType<typeof setInterval>;

  onMount(() => {
    loadSettings();
    loadMatchScouts();
    loadSuperScouts();
    loadDevices();
    loadAllMatches();
    loadAllSuperMatches();
    deviceInterval = setInterval(loadDevices, HEARTBEAT_INTERVAL);
    tickInterval = setInterval(() => (now = Date.now()), 1000);
    allMatchesInterval = setInterval(loadMatchesTable, HEARTBEAT_INTERVAL);
  });

  onDestroy(() => {
    clearInterval(deviceInterval);
    clearInterval(tickInterval);
    clearInterval(allMatchesInterval);
  });
</script>

<div class="flex flex-col border-b border-border md:flex-row md:items-stretch">
  <SettingsPanel
    draft={settingsDraft}
    loading={settingsLoading}
    saving={settingsSaving}
    error={settingsError}
    onSave={saveSettings}
  />

  <div class="flex flex-1 flex-col border-t border-border md:border-l md:border-t-0">
    <MatchScoutsPanel
      scouts={matchScouts}
      loading={matchScoutsLoading}
      bind:liveSchedule
      {liveScheduleBusy}
      {liveScheduleError}
      onAdd={() => openAddScout("match")}
      onEdit={openEditMatchScout}
      onToggle={toggleMatchScout}
      onDelete={deleteMatchScout}
      onPodChange={handlePodChange}
    />

    <SuperScoutsPanel
      scouts={superScouts}
      loading={superScoutsLoading}
      onAdd={() => openAddScout("super")}
      onEdit={openEditSuperScout}
      onToggle={toggleSuperScout}
      onDelete={deleteSuperScout}
    />

    <MatchSchedulePanel
      bind:forceMatchInput
      busy={scheduleBusy}
      message={scheduleMessage}
      error={scheduleError}
      onRefreshFromTba={handleRefreshFromTba}
      onGenerateSchedule={handleGenerateSchedule}
      onAdvanceSchedule={handleAdvanceSchedule}
      onForceMatch={handleForceMatch}
    />
  </div>
</div>

<DevicesTable
  bind:this={devicesTableRef}
  {devices}
  {devicesError}
  {showInitialSpinner}
  {now}
  {clockOffset}
  onRemoveDevice={handleRemoveDevice}
  onEditDevice={openEditDeviceModal}
  onMessageDevices={openMessageModal}
/>

<MatchesTable
  mode={matchesTableMode}
  onModeChange={setMatchesTableMode}
  matchesData={allMatchesData}
  matchesLoading={allMatchesLoading}
  matchesError={allMatchesError}
  superMatchesData={allSuperMatchesData}
  superMatchesLoading={allSuperMatchesLoading}
  superMatchesError={allSuperMatchesError}
  {inactiveMatchScouts}
  {inactiveSuperScouts}
/>

<ScoutModal modal={scoutModal} onSave={saveScoutModal} onClose={() => (scoutModal = null)} />

<EditDeviceModal
  modal={editDeviceModal}
  onRename={handleRename}
  onClearStorage={handleClearStorage}
  onClose={() => (editDeviceModal = null)}
/>

<MessageModal modal={messageModal} onSend={handleSendMessage} onClose={() => (messageModal = null)} />
