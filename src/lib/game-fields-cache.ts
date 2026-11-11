import type { GameFieldsResponse, ScoutingMode } from "./scouting-store.svelte";

function cacheKey(mode: ScoutingMode): string {
  return `advantagescout_game_fields_${mode}`;
}

export function getCachedGameFields(
  mode: ScoutingMode,
): GameFieldsResponse | null {
  const raw = localStorage.getItem(cacheKey(mode));
  if (!raw) return null;
  try {
    return JSON.parse(raw) as GameFieldsResponse;
  } catch {
    return null;
  }
}

export function setCachedGameFields(
  mode: ScoutingMode,
  data: GameFieldsResponse,
): void {
  localStorage.setItem(cacheKey(mode), JSON.stringify(data));
}
