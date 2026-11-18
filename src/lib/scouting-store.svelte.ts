export type ScoutingMode = "match" | "pit" | "super";
export type Alliance = "Red" | "Blue";

export const scoutingSession = $state({
  mode: "match" as ScoutingMode,
  scout: "",
  team: "",
  match: "",
  alliance: "Red" as Alliance,
  team1: "",
  team2: "",
  team3: "",
});

export interface GameFieldsResponse {
  fields: Record<string, unknown>;
  setup: Record<string, unknown>;
}

export const gameFieldsCache = $state<{
  mode: ScoutingMode | null;
  data: GameFieldsResponse | null;
}>({
  mode: null,
  data: null,
});
