import { BleBridge } from "./ble-bridge";
import { getServerUrl } from "./config";
import { getPreferWifi } from "./wifi-preference";

export type FetchStatus = "disconnected" | "connecting" | "connected" | "error";

class ApiService {
  private bridge: BleBridge;
  private connectInFlight: Promise<void> | null = null;

  public status: FetchStatus = $state("disconnected");
  public lastError: string | null = $state(null);
  // Chunk progress (bytes) of whichever BLE request/reply is currently in
  // flight — surfaced for the Advanced Options "dev tools" toggle. null
  // when no transfer is active.
  public chunkProgress: { current: number; max: number } | null = $state(null);
  // The BLE bridge's own connection state, reactive and independent of
  // `status` — `status` also flips to "connected" on any successful plain
  // Wi-Fi/dev-server fetch (by design, for AppHeader's reachability
  // indicator), so Home's "BT Connect" button needs this instead to avoid
  // showing "Connected" before BLE was ever used. Mirrors
  // `this.bridge.connected` but as $state so the UI updates with it —
  // bridge.deviceId isn't itself reactive.
  public bleConnected = $state(false);

  constructor() {
    this.bridge = new BleBridge({
      onConnectionChange: (connected) => {
        this.bleConnected = connected;
        this.status = connected ? "connected" : "disconnected";
      },
      onLog: (msg) => console.log(msg),
      onChunkProgress: (current, max) => {
        this.chunkProgress = { current, max };
      },
    });
  }

  get connected(): boolean {
    return this.bleConnected;
  }

  async connect(): Promise<void> {
    if (this.bridge.connected) return;
    if (this.connectInFlight) return this.connectInFlight;

    this.status = "connecting";
    this.connectInFlight = this.bridge
      .startAccepting()
      .then(() => undefined)
      .catch((e) => {
        this.lastError = e instanceof Error ? e.message : String(e);
        this.status = "error";
        throw e;
      })
      .finally(() => {
        this.connectInFlight = null;
      });
    return this.connectInFlight;
  }

  async disconnect(): Promise<void> {
    await this.bridge.disconnect();
  }

  async fetch(
    path: string,
    init?: RequestInit,
    onProgress?: (current: number, max: number) => void,
  ): Promise<Response> {
    try {
      const res = await this.transport(path, init, onProgress);
      this.status = "connected";
      return res;
    } catch (e) {
      if (this.status !== "connecting") this.status = "disconnected";
      throw e;
    } finally {
      this.chunkProgress = null;
    }
  }

  private async transport(
    path: string,
    init?: RequestInit,
    onProgress?: (current: number, max: number) => void,
  ): Promise<Response> {
    if (getPreferWifi()) {
      try {
        return await fetch(`${getServerUrl()}${path}`, init);
      } catch (e) {
        if (!this.bridge.connected) throw e;
      }
    }

    if (this.bridge.connected) {
      return this.bridge.fetch(path, init, onProgress);
    }
    return fetch(`${getServerUrl()}${path}`, init);
  }
}

export const api = new ApiService();
