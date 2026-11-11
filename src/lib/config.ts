import { Capacitor } from "@capacitor/core";
import { getServerAddress } from "./server-address";

export function getServerUrl(): string {
  // Used for web/wifi fallback
  const default_server_port = 6328
  if (Capacitor.isNativePlatform()) {
    const host = getServerAddress() || "localhost";
    return `http://${host}:${default_server_port}`;
  }
  const host = window.location.hostname || "localhost";
  return `http://${host}:${default_server_port}`;
}

export const API_BASE = "/api";
export const HEARTBEAT_INTERVAL = 3000;

export const SCHEDULE_POLL_INTERVAL = 2000;
export const UPLOAD_CHECK_INTERVAL = 8000;

export const BLE_RECONNECT_INTERVAL = 3000;
export const VERSION = "Alpha";
