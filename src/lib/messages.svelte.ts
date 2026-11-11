import { push } from "svelte-spa-router";
import { api } from "./api.svelte";
import { getDeviceName, hasDeviceName, setDeviceName } from "./device";

export interface DeviceMessage {
  content: unknown;
  timestamp: number;
  type: string;
}

export const toastState = $state<{
  message: string;
  centered: boolean;
  visible: boolean;
}>({
  message: "",
  centered: false,
  visible: false,
});

let hideTimer: ReturnType<typeof setTimeout> | null = null;

export function showToast(message: string, centered = false): void {
  toastState.message = message;
  toastState.centered = centered;
  toastState.visible = true;
  if (hideTimer) clearTimeout(hideTimer);
  hideTimer = setTimeout(() => {
    toastState.visible = false;
  }, 3000);
}

function executeMessage(message: DeviceMessage): void {
  switch (message.type) {
    case "rename_device":
      setDeviceName(String(message.content));
      showToast(`Device successfully renamed to ${message.content}`);
      break;
    case "clear_storage":
      showToast("Clearing storage...");
      localStorage.clear();
      push("/setupmodal");
      break;
    case "toast":
      showToast(String(message.content));
      break;
    case "toast_center":
      showToast(String(message.content), true);
      break;
    default:
      console.warn(`Unknown message type: ${message.type}`);
  }
}

function keyOf(m: DeviceMessage): string {
  return `${m.type}:${JSON.stringify(m.content)}`;
}

let seenKeys = new Set<string>();

function updateMessages(queue: DeviceMessage[]): void {
  const currentKeys = new Set(queue.map(keyOf));
  for (const key of seenKeys) {
    if (!currentKeys.has(key)) seenKeys.delete(key);
  }
  for (const message of queue) {
    const key = keyOf(message);
    if (seenKeys.has(key)) continue;
    seenKeys.add(key);
    executeMessage(message);
  }
}

export async function checkMessages(): Promise<void> {
  if (!hasDeviceName()) return;
  try {
    const res = await api.fetch(
      `/api/device_messages/${encodeURIComponent(getDeviceName())}`,
    );
    if (!res.ok) return;
    const data = (await res.json()) as DeviceMessage[];
    updateMessages(data);
  } catch {
    // Skip
  }
}
