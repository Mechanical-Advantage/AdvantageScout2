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

export interface FieldDef {
  name: string;
  type: "Integer" | "Numeric" | "Text" | "Boolean" | string;
  min?: number;
  max?: number;
  default?: unknown;
  displayType?: string;
  display?: {
    name?: string;
    behavior?: string;
    x?: number;
    y?: number;
    size?: [number, number];
  };
}

export interface GameFieldsResponse {
  fields: Record<string, unknown>;
  setup: Record<string, { fields: FieldDef[] }>;
}

export const gameFieldsCache = $state<{
  mode: ScoutingMode | null;
  data: GameFieldsResponse | null;
}>({
  mode: null,
  data: null,
});
