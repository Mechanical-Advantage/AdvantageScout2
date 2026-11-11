import { fetchGameFields } from "@lib/scouts";

export const gameData = $state<{
  activeTab: number; // 0 Auto, 1 Teleop, 2 Postgame
  preMatchDone: boolean;
  values: Record<string, number | string | boolean>;
  loading: boolean;
  loadError: string | null;
  liveLocation: "Outpost" | "Floor" | "Neutral" | "PreLoaded";
  gameShift: number;
  fuelButtonTap: boolean; // true = BPT, false = BPS
  fuelButtonAmount: number;
  fuelButtonSpeedMs: number;
  fuelCycleCountSuccess: number;
  fuelCycleCountFail: number;
}>({
  activeTab: 0,
  preMatchDone: false,
  values: {},
  loading: true,
  loadError: null,
  liveLocation: "Floor",
  gameShift: 0,
  fuelButtonTap: false,
  fuelButtonAmount: 1,
  fuelButtonSpeedMs: 200,
  fuelCycleCountSuccess: 0,
  fuelCycleCountFail: 0,
});

interface UndoSnapshot {
  values: Record<string, number | string | boolean>;
  fuelCycleCountSuccess: number;
  fuelCycleCountFail: number;
}

const undoStack = $state<UndoSnapshot[]>([]);

export function canUndo(): boolean {
  return undoStack.length > 0;
}

export function pushUndoSnapshot(): void {
  undoStack.push({
    values: { ...gameData.values },
    fuelCycleCountSuccess: gameData.fuelCycleCountSuccess,
    fuelCycleCountFail: gameData.fuelCycleCountFail,
  });
}

export function undo(): void {
  const snapshot = undoStack.pop();
  if (!snapshot) return;
  gameData.values = snapshot.values;
  gameData.fuelCycleCountSuccess = snapshot.fuelCycleCountSuccess;
  gameData.fuelCycleCountFail = snapshot.fuelCycleCountFail;
}

export async function loadMatchFields(): Promise<void> {
  gameData.loading = true;
  gameData.loadError = null;
  try {
    const data = await fetchGameFields("match");
    gameData.values = {
      ...(data.fields as Record<string, number | string | boolean>),
    };
    undoStack.length = 0;
  } catch (e) {
    gameData.loadError = e instanceof Error ? e.message : String(e);
  } finally {
    gameData.loading = false;
  }
}
