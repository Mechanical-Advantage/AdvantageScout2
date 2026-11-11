import { api } from "./api.svelte";

export interface QueuedSubmission {
  id: string;
  payload: Record<string, unknown>;
  queuedAt: number;
}

const STORAGE_KEY = "advantagescout_scoutdata";

function loadQueue(): QueuedSubmission[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as QueuedSubmission[]) : [];
  } catch {
    return [];
  }
}

function persist(items: QueuedSubmission[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  } catch {
    // Non persistant
  }
}

export const uploadQueue = $state<{ items: QueuedSubmission[] }>({
  items: loadQueue(),
});

export function queueSubmission(payload: Record<string, unknown>): void {
  const item: QueuedSubmission = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    payload,
    queuedAt: Date.now(),
  };
  uploadQueue.items = [...uploadQueue.items, item];
  persist(uploadQueue.items);
}

let flushing = false;

export async function flushQueue(): Promise<void> {
  if (flushing || uploadQueue.items.length === 0) return;
  flushing = true;
  try {
    const res = await api.fetch("/api/game_data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(uploadQueue.items.map((i) => i.payload)),
    });
    if (res.ok) {
      uploadQueue.items = [];
      persist([]);
    }
  } catch {
    // No connection
  } finally {
    flushing = false;
  }
}
