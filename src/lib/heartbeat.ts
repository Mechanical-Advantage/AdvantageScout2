import { Capacitor } from "@capacitor/core";
import { api } from "./api.svelte";
import { getDeviceName, hasDeviceName } from "./device";
import { scoutingSession } from "./scouting-store.svelte";
import { checkMessages } from "./messages.svelte";
import { checkForFrontendUpdate } from "./frontend-update.svelte";
import { isOnScoutingForm } from "./scouting-route";
import { HEARTBEAT_INTERVAL, VERSION } from "./config";

let timer: ReturnType<typeof setInterval> | null = null;

async function sendHeartbeat(): Promise<void> {
  if (!hasDeviceName()) return;
  const onScoutingForm = isOnScoutingForm();
  try {
    await api.fetch("/api/heartbeat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        device: getDeviceName(),
        platform: Capacitor.getPlatform(),
        version: VERSION,
        mode: scoutingSession.mode,
        timestamp: Date.now(),
        ...(onScoutingForm
          ? {
              scout: scoutingSession.scout,
              team: scoutingSession.team,
              alliance: scoutingSession.alliance,
              match: scoutingSession.match,
            }
          : {}),
      }),
    });
  } catch {
    // Shown as stale
  }
}

function tick(): void {
  sendHeartbeat();
  checkMessages();
  if (Capacitor.isNativePlatform() && !isOnScoutingForm()) {
    checkForFrontendUpdate();
  }
}

export function startHeartbeat(): void {
  if (timer) return;
  tick();
  timer = setInterval(tick, HEARTBEAT_INTERVAL);
}
