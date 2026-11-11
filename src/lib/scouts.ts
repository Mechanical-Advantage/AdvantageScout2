import { api } from "./api.svelte";
import type { GameFieldsResponse, ScoutingMode } from "./scouting-store.svelte";

export interface MatchScout {
  name: string;
  active: boolean;
  pod: number | null;
}

export interface SuperScout {
  name: string;
  active: boolean;
}

export interface MatchScheduleRow {
  Match: number;
  Blue1: string;
  Blue2: string;
  Blue3: string;
  Red1: string;
  Red2: string;
  Red3: string;
  ScoutBlue1: string;
  ScoutBlue2: string;
  ScoutBlue3: string;
  ScoutRed1: string;
  ScoutRed2: string;
  ScoutRed3: string;
}

export interface SuperScheduleRow {
  Match: number;
  Blue1: string;
  Blue2: string;
  Blue3: string;
  Red1: string;
  Red2: string;
  Red3: string;
  ScoutBlue: string;
  ScoutRed: string;
}

export interface ScheduleSlotStatus {
  uploaded: boolean;
  active: boolean;
  available: boolean;
}

export interface MatchScheduleStatus {
  Match: number;
  slots: Record<
    "Blue1" | "Blue2" | "Blue3" | "Red1" | "Red2" | "Red3",
    ScheduleSlotStatus
  >;
}

export interface SuperScheduleStatus {
  Match: number;
  slots: Record<"Blue" | "Red", ScheduleSlotStatus>;
}

export interface ScheduleSelection {
  match: number;
  alliance: "Red" | "Blue";
  scout: string;
  team?: number;
  teams?: number[];
}

async function errorMessage(res: Response): Promise<string> {
  try {
    const body = (await res.clone().json()) as { error?: string };
    if (body?.error) return body.error;
  } catch {
    // Not JSON
  }
  return `Server returned ${res.status}`;
}

async function fetchJson<T>(path: string): Promise<T> {
  const res = await api.fetch(path);
  if (!res.ok) throw new Error(await errorMessage(res));
  return res.json();
}

async function postJson(path: string, body: unknown): Promise<void> {
  await postJsonReturning(path, body);
}

async function postJsonReturning<T>(path: string, body?: unknown): Promise<T> {
  const res = await api.fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await errorMessage(res));
  return res.json();
}

export async function fetchMatchScouts(): Promise<MatchScout[]> {
  const data = await fetchJson<
    Record<string, { Active: number; PodNumber: number | null }>
  >("/api/match_scout_list");
  return Object.entries(data).map(([name, v]) => ({
    name,
    active: v.Active === 1,
    pod: v.PodNumber,
  }));
}

export async function upsertMatchScout(
  name: string,
  active: boolean,
  pod: number | null,
): Promise<void> {
  await postJson("/api/match_scout_list", {
    [name]: { Active: active ? 1 : 0, PodNumber: pod },
  });
}

export async function removeMatchScout(name: string): Promise<void> {
  await postJson("/api/match_scout_list", { [name]: { Active: -1 } });
}

export async function fetchSuperScouts(): Promise<SuperScout[]> {
  const data = await fetchJson<Record<string, number>>("/api/super_scout_list");
  return Object.entries(data).map(([name, active]) => ({
    name,
    active: active === 1,
  }));
}

export async function upsertSuperScout(
  name: string,
  active: boolean,
): Promise<void> {
  await postJson("/api/super_scout_list", { [name]: active ? 1 : 0 });
}

export async function removeSuperScout(name: string): Promise<void> {
  await postJson("/api/super_scout_list", { [name]: -1 });
}

export async function fetchCurrentMatchSchedule(): Promise<MatchScheduleRow> {
  return fetchJson<MatchScheduleRow>("/api/current_schedule");
}

export async function fetchCurrentSuperSchedule(): Promise<SuperScheduleRow> {
  return fetchJson<SuperScheduleRow>("/api/current_super_schedule");
}

export async function fetchGameFields(
  mode: ScoutingMode,
): Promise<GameFieldsResponse> {
  return fetchJson<GameFieldsResponse>(`/api/game_fields/${mode}`);
}

export async function fetchCurrentMatchScheduleStatus(): Promise<MatchScheduleStatus> {
  return fetchJson<MatchScheduleStatus>("/api/current_schedule_status");
}

export async function fetchCurrentSuperScheduleStatus(): Promise<SuperScheduleStatus> {
  return fetchJson<SuperScheduleStatus>("/api/current_super_schedule_status");
}

export interface AdvanceScheduleResult {
  current_match: number;
  advanced: boolean;
}

export async function advanceScheduleCheck(): Promise<AdvanceScheduleResult> {
  return postJsonReturning<AdvanceScheduleResult>(
    "/api/advance_schedule_check",
  );
}

export async function forceCurrentMatch(
  match: number,
): Promise<{ current_match: number }> {
  return postJsonReturning<{ current_match: number }>("/api/force_match", {
    match,
  });
}

export async function refreshScheduleFromTba(): Promise<void> {
  await postJsonReturning("/api/refresh_schedule_from_tba");
}

export async function generateSchedule(): Promise<void> {
  await postJsonReturning("/api/generate_schedule");
}

export interface MatchUploadStatus {
  match: number;
  teams: number[];
  uploaded: boolean[]; 
  scouts: (string | null)[];
}

export interface AllMatchesStatus {
  current_match: number;
  matches: MatchUploadStatus[];
}

export async function fetchAllMatchesStatus(): Promise<AllMatchesStatus> {
  return fetchJson<AllMatchesStatus>("/api/all_matches_status");
}

export interface SuperMatchUploadStatus {
  match: number;
  alliances: ("Blue" | "Red")[];
  teams: number[][]; 
  uploaded: boolean[]; 
  scouts: (string | null)[]; 
}

export interface AllSuperMatchesStatus {
  current_match: number;
  matches: SuperMatchUploadStatus[];
}

export async function fetchAllSuperMatchesStatus(): Promise<AllSuperMatchesStatus> {
  return fetchJson<AllSuperMatchesStatus>("/api/all_super_matches_status");
}

export async function fetchGlobalSettings(): Promise<Record<string, unknown>> {
  return fetchJson<Record<string, unknown>>("/api/global_settings");
}

export async function saveGlobalSettings(
  settings: Record<string, unknown>,
): Promise<void> {
  await postJson("/api/global_settings", settings);
}

export interface DeviceInfo {
  Name: string;
  LastHeartbeat?: {
    timestamp?: number;
    mode?: string;
    platform?: string;
    version?: string;
    scout?: string;
    team?: string | number;
    alliance?: string;
    match?: string | number;
  } | null;
}

export interface DevicesInfoResponse {
  devices: DeviceInfo[];
  serverTime: number;
}

export async function fetchDevices(): Promise<DevicesInfoResponse> {
  return fetchJson<DevicesInfoResponse>("/api/devices_info");
}

export async function removeDevice(name: string): Promise<void> {
  await postJson("/api/remove_device", { device: name });
}

export interface DeviceMessage {
  device: string;
  type: string;
  content: string;
}

export async function sendMessagesToDevices(
  messages: DeviceMessage[],
): Promise<void> {
  await postJson("/api/send_devices_messages", messages);
}
