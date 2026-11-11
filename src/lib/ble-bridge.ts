import { BleClient } from "@capacitor-community/bluetooth-le";
import type { ScanResult } from "@capacitor-community/bluetooth-le";

/**
 * Capacitor BLE central that speaks the same "HTTP-over-Bluetooth" wire
 * protocol as the peripheral in server/bluetooth_server.py: a Nordic
 * UART-style GATT service where both requests (written to the request
 * characteristic) and replies (delivered via notifications on the response
 * characteristic) are magic-byte length-prefixed frames whose JSON payload
 * is opportunistically zlib-deflated to cut BLE transfer time. See
 * server/bluetooth_server.py for the canonical protocol definition this
 * must stay in sync with.
 */

export const BRIDGE_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e";
export const BRIDGE_REQUEST_CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e";
export const BRIDGE_RESPONSE_CHAR_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e";

const DEFAULT_SERVICE_NAME = "Advscout";
const DEFAULT_SCAN_TIMEOUT_MS = 30_000;
const DEFAULT_REQUEST_TIMEOUT_MS = 60_000;
const FRAME_MAGIC_0 = 0xab;
const FRAME_MAGIC_1 = 0xcd;
const FRAME_HEADER_LEN = 7; // 2 magic bytes + 4-byte big-endian length + 1-byte flags
const FRAME_FLAG_DEFLATE = 0x01;
const FRAME_MAX_BODY = 16 * 1024 * 1024;
// Used only when getMtu() is unavailable (web); matches the legacy web
// bridge's fixed chunk size.
const FALLBACK_CHUNK_BYTES = 180;

// zlib's default "deflate" format (RFC 1950) — matches Python's
// zlib.compress()/zlib.decompress() byte-for-byte, so no custom framing is
// needed to interop with server/bluetooth_server.py's pack_frame().
async function runThroughStream(
  data: Uint8Array,
  stream: CompressionStream | DecompressionStream,
): Promise<Uint8Array> {
  const writer = stream.writable.getWriter();
  // TS's lib.dom types Uint8Array generically by its buffer type; `data` is
  // always a plain (non-shared) ArrayBuffer-backed view at runtime here.
  const written = writer.write(data as unknown as BufferSource);
  const result = new Response(stream.readable).arrayBuffer();
  await written;
  await writer.close();
  return new Uint8Array(await result);
}

async function deflate(data: Uint8Array): Promise<Uint8Array> {
  return runThroughStream(data, new CompressionStream("deflate"));
}

async function inflate(data: Uint8Array): Promise<Uint8Array> {
  return runThroughStream(data, new DecompressionStream("deflate"));
}

function packFrame(payload: Uint8Array, flags: number): Uint8Array {
  const framed = new Uint8Array(FRAME_HEADER_LEN + payload.length);
  framed[0] = FRAME_MAGIC_0;
  framed[1] = FRAME_MAGIC_1;
  new DataView(framed.buffer).setUint32(2, payload.length, false);
  framed[6] = flags;
  framed.set(payload, FRAME_HEADER_LEN);
  return framed;
}

export type HttpMethod = "GET" | "POST" | "PUT" | "DELETE" | "PATCH";

export interface BridgeRequest {
  method?: HttpMethod;
  url: string;
  headers?: Record<string, string>;
  body?: unknown;
}

export interface BridgeResponse {
  id: string;
  status: number;
  headers: Record<string, string>;
  body: string;
  error: string | null;
}

interface Pending {
  resolve: (r: BridgeResponse) => void;
  reject: (err: Error) => void;
  timer: ReturnType<typeof setTimeout>;
  // Per-call progress, as opposed to `onChunkProgress` below (which reports
  // on whatever frame is in flight across ALL requests, for the generic
  // dev-tools indicator). Lets a caller that only cares about one specific
  // request's own bytes (e.g. the frontend-update download bar) track that
  // request without having its number clobbered by an unrelated request
  // (e.g. a heartbeat) that happens to be in flight at the same time.
  onProgress?: (current: number, max: number) => void;
}

export interface BleBridgeOptions {
  serviceName?: string;
  scanTimeoutMs?: number;
  requestTimeoutMs?: number;
  onConnectionChange?: (connected: boolean) => void;
  onLog?: (msg: string) => void;
  // Reports byte-level progress of whichever frame is currently in flight
  // (the outgoing request while writeChunked() is running, then the
  // incoming reply while notifications are still arriving) — a dev-tools
  // aid for watching large transfers (frontend bundle sync, big uploads)
  // chunk across the BLE link. max is 0 until a frame's total size is
  // known (i.e. before the outgoing bytes are built, or before the
  // incoming frame header has arrived).
  onChunkProgress?: (current: number, max: number) => void;
}

let idCounter = 0;
function nextId(): string {
  idCounter += 1;
  return `${Date.now().toString(36)}-${idCounter.toString(36)}`;
}

export class BleBridge {
  private serviceName: string;
  private scanTimeoutMs: number;
  private requestTimeoutMs: number;
  private onConnectionChange?: (connected: boolean) => void;
  private onLog?: (msg: string) => void;
  private onChunkProgress?: (current: number, max: number) => void;

  private deviceId: string | null = null;
  private accepting = false;
  private writeChunkSize = FALLBACK_CHUNK_BYTES;
  private recvBuf = new Uint8Array(0);
  // Count/size-in-progress of the notification chunks making up whatever
  // reply is currently streaming in, purely so the dev-tools indicator can
  // report an actual "Chunk: X/Y" count instead of raw bytes. Reset once a
  // frame finishes parsing in drainFrames() (the next notification starts a
  // new reply's sequence). `recvChunkSize` is captured from the FIRST chunk
  // of a reply (server/bluetooth_server.py sends one reply's chunks back to
  // back at a fixed size, per its own `chunk_bytes`, with only the final
  // chunk possibly shorter), so dividing the reply's total length by it
  // gives a good estimate of how many chunks it'll take.
  private recvChunkCount = 0;
  private recvChunkSize = 0;
  private pending = new Map<string, Pending>();
  // Serializes writeChunked() across concurrent request() calls. Without
  // this, two requests in flight at once (e.g. a match upload racing a
  // schedule poll) interleave their chunks on the wire -- each
  // `await BleClient.write(...)` yields back to JS between chunks, letting
  // another in-progress writeChunked() loop slip a chunk in. The server
  // (server/bluetooth_server.py) has no way to tell those bytes apart; it
  // just sees one bad, un-parseable frame and drops both requests.
  private writeQueue: Promise<void> = Promise.resolve();

  constructor(opts: BleBridgeOptions = {}) {
    this.serviceName = opts.serviceName ?? DEFAULT_SERVICE_NAME;
    this.scanTimeoutMs = opts.scanTimeoutMs ?? DEFAULT_SCAN_TIMEOUT_MS;
    this.requestTimeoutMs = opts.requestTimeoutMs ?? DEFAULT_REQUEST_TIMEOUT_MS;
    this.onConnectionChange = opts.onConnectionChange;
    this.onLog = opts.onLog;
    this.onChunkProgress = opts.onChunkProgress;
  }

  get connected(): boolean {
    return this.deviceId !== null;
  }

  get connectedDeviceId(): string | null {
    return this.deviceId;
  }

  get isAccepting(): boolean {
    return this.accepting;
  }

  private log(msg: string): void {
    this.onLog?.(`[BleBridge] ${msg}`);
  }

  async startAccepting(): Promise<string> {
    if (this.deviceId) return this.deviceId;
    if (this.accepting) throw new Error("Already scanning for Advscout");
    this.accepting = true;

    try {
      await BleClient.initialize();

      const deviceId = await new Promise<string>((resolve, reject) => {
        const timer = setTimeout(() => {
          BleClient.stopLEScan().catch(() => {});
          reject(new Error("Bluetooth scan timed out"));
        }, this.scanTimeoutMs);

        let settled = false;
        const onMatch = (id: string) => {
          if (settled) return;
          settled = true;
          clearTimeout(timer);
          BleClient.stopLEScan()
            .catch(() => {})
            .finally(() => resolve(id));
        };

        BleClient.requestLEScan(
          {
            services: [BRIDGE_SERVICE_UUID],
            optionalServices: [BRIDGE_SERVICE_UUID],
          },
          (result: ScanResult) => {
            const name = result.localName ?? result.device.name;
            const matchesService = (result.uuids ?? []).some(
              (u) => u.toLowerCase() === BRIDGE_SERVICE_UUID,
            );
            if (matchesService || name === this.serviceName) {
              onMatch(result.device.deviceId);
            }
          },
        ).catch((err) => {
          clearTimeout(timer);
          reject(err);
        });
      });

      await BleClient.connect(deviceId, (disconnectedId) =>
        this.handleDisconnect(disconnectedId),
      );

      try {
        const mtu = await BleClient.getMtu(deviceId);
        this.writeChunkSize = Math.max(20, mtu - 3);
      } catch {
        this.writeChunkSize = FALLBACK_CHUNK_BYTES;
      }

      await BleClient.startNotifications(
        deviceId,
        BRIDGE_SERVICE_UUID,
        BRIDGE_RESPONSE_CHAR_UUID,
        (value) => this.handleNotification(value),
      );

      this.deviceId = deviceId;
      this.onConnectionChange?.(true);
      this.log(`connected to ${deviceId}, chunk size ${this.writeChunkSize}`);
      return deviceId;
    } finally {
      this.accepting = false;
    }
  }

  async cancelAccepting(): Promise<void> {
    if (this.accepting) {
      await BleClient.stopLEScan().catch(() => {});
    }
  }

  private handleDisconnect(deviceId: string): void {
    if (this.deviceId !== deviceId) return;
    this.deviceId = null;
    this.recvBuf = new Uint8Array(0);
    this.onConnectionChange?.(false);
    this.log(`disconnected from ${deviceId}`);
    for (const p of this.pending.values()) {
      clearTimeout(p.timer);
      p.reject(new Error("Bluetooth device disconnected"));
    }
    this.pending.clear();
  }

  async disconnect(): Promise<void> {
    if (this.deviceId) {
      const id = this.deviceId;
      await BleClient.disconnect(id).catch(() => {});
      this.handleDisconnect(id);
    }
  }

  destroy(): void {
    this.disconnect().catch(() => {});
  }

  private handleNotification(value: DataView): void {
    const chunk = new Uint8Array(
      value.buffer,
      value.byteOffset,
      value.byteLength,
    );
    if (this.recvChunkCount === 0 && chunk.length > 0) {
      this.recvChunkSize = chunk.length;
    }
    this.recvChunkCount += 1;
    const merged = new Uint8Array(this.recvBuf.length + chunk.length);
    merged.set(this.recvBuf, 0);
    merged.set(chunk, this.recvBuf.length);
    this.recvBuf = merged;
    this.drainFrames();
  }

  private findMagic(buf: Uint8Array): number {
    for (let i = 0; i < buf.length - 1; i++) {
      if (buf[i] === FRAME_MAGIC_0 && buf[i + 1] === FRAME_MAGIC_1) return i;
    }
    return -1;
  }

  private drainFrames(): void {
    while (true) {
      const magicIdx = this.findMagic(this.recvBuf);
      if (magicIdx === -1) {
        // Keep the last byte in case it's the first half of a split magic pair.
        if (this.recvBuf.length > 1) {
          this.recvBuf = this.recvBuf.slice(this.recvBuf.length - 1);
        }
        return;
      }
      if (magicIdx > 0) {
        this.recvBuf = this.recvBuf.slice(magicIdx);
      }
      if (this.recvBuf.length < FRAME_HEADER_LEN) return; // wait for the rest of the header

      const view = new DataView(
        this.recvBuf.buffer,
        this.recvBuf.byteOffset,
        this.recvBuf.byteLength,
      );
      const length = view.getUint32(2, false);
      if (length <= 0 || length > FRAME_MAX_BODY) {
        // Corrupt/garbage length — resync by dropping the false magic and rescanning.
        this.recvBuf = this.recvBuf.slice(2);
        continue;
      }

      const total = FRAME_HEADER_LEN + length;
      const estimatedChunks = Math.max(1, Math.ceil(total / (this.recvChunkSize || total)));
      if (this.recvBuf.length < total) {
        this.onChunkProgress?.(this.recvChunkCount, estimatedChunks);
        this.oldestPending()?.onProgress?.(this.recvBuf.length, total);
        return; // wait for the rest of the body
      }

      const flags = this.recvBuf[6];
      const bodyBytes = this.recvBuf.slice(FRAME_HEADER_LEN, total);
      this.recvBuf = this.recvBuf.slice(total);

      this.onChunkProgress?.(this.recvChunkCount, this.recvChunkCount);
      this.oldestPending()?.onProgress?.(total, total);
      this.recvChunkCount = 0;
      this.recvChunkSize = 0;
      this.handleFrame(flags, bodyBytes).catch((e) => {
        this.log(`failed to parse frame: ${e}`);
        // BLE notify has no delivery ack (see server/bluetooth_server.py),
        // so a dropped notification chunk leaves recvBuf waiting on bytes
        // that will never arrive. Once enough of a LATER reply's bytes
        // accumulate to spuriously satisfy that stale `total`, bodyBytes
        // ends up a corrupt mix of the old reply's tail and the next
        // reply's head, which fails to parse here -- exactly what we just
        // caught. Whatever's left in recvBuf past this point is equally
        // suspect, so drop it and let the next reply resync from its own
        // magic bytes instead of silently corrupting every reply after it
        // (which otherwise times out the still-pending request 60s later
        // with no sign anything went wrong server-side).
        this.recvBuf = new Uint8Array(0);
      });
    }
  }

  private async handleFrame(
    flags: number,
    bodyBytes: Uint8Array,
  ): Promise<void> {
    const raw =
      flags & FRAME_FLAG_DEFLATE ? await inflate(bodyBytes) : bodyBytes;
    const text = new TextDecoder("utf-8").decode(raw);
    const reply = JSON.parse(text) as BridgeResponse;
    this.resolvePending(reply);
  }

  // The reply currently streaming in over notifications belongs to whichever
  // request has been waiting longest -- the server replies to requests in
  // the order they arrived (see heartbeat.ts's comment on the server's
  // single global send lock: a second request's reply can't start until the
  // first's has fully finished sending), and `pending` is a Map, whose keys
  // iterate in insertion order.
  private oldestPending(): Pending | undefined {
    return this.pending.values().next().value;
  }

  private resolvePending(reply: BridgeResponse): void {
    const p = this.pending.get(reply.id);
    if (!p) {
      this.log(`no pending request for reply id ${reply.id}`);
      return;
    }
    clearTimeout(p.timer);
    this.pending.delete(reply.id);
    p.resolve(reply);
  }

  async request(
    req: BridgeRequest,
    onProgress?: (current: number, max: number) => void,
  ): Promise<BridgeResponse> {
    if (!this.deviceId) throw new Error("BLE bridge is not connected");
    const id = nextId();
    const wire = {
      id,
      method: req.method ?? "GET",
      url: req.url,
      headers: req.headers ?? {},
      body: req.body,
    };
    const raw = new TextEncoder().encode(JSON.stringify(wire));
    const compressed = await deflate(raw);
    const bytes =
      compressed.length < raw.length
        ? packFrame(compressed, FRAME_FLAG_DEFLATE)
        : packFrame(raw, 0);

    const responsePromise = new Promise<BridgeResponse>((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`BLE request ${id} timed out`));
      }, this.requestTimeoutMs);
      this.pending.set(id, { resolve, reject, timer, onProgress });
    });

    // Chain onto writeQueue rather than calling writeChunked directly, so a
    // concurrent request() can't interleave its chunks with this one's (see
    // writeQueue's own comment above). The queue itself must never stay
    // rejected -- that would wedge every future request -- so its failure
    // is swallowed there; this call's own promise still rejects normally.
    const writeTask = this.writeQueue.then(() => this.writeChunked(id, bytes));
    this.writeQueue = writeTask.then(
      () => undefined,
      () => undefined,
    );
    await writeTask;
    return responsePromise;
  }

  private async writeChunked(id: string, bytes: Uint8Array): Promise<void> {
    if (!this.deviceId) throw new Error("BLE bridge is not connected");
    const onProgress = this.pending.get(id)?.onProgress;
    // `onChunkProgress` (the generic dev-tools indicator) reports actual
    // chunk index/count, matching its "Chunk: X/Y" label -- `onProgress`
    // (a specific caller's own byte-level progress bar, e.g.
    // frontend-update's download bar) keeps the finer-grained byte count,
    // which animates more smoothly than a handful of discrete chunk steps.
    const totalChunks = Math.max(1, Math.ceil(bytes.length / this.writeChunkSize));
    this.onChunkProgress?.(0, totalChunks);
    onProgress?.(0, bytes.length);
    let chunkIdx = 0;
    for (let offset = 0; offset < bytes.length; offset += this.writeChunkSize) {
      const slice = bytes.slice(offset, offset + this.writeChunkSize);
      const view = new DataView(
        slice.buffer,
        slice.byteOffset,
        slice.byteLength,
      );
      await BleClient.write(
        this.deviceId,
        BRIDGE_SERVICE_UUID,
        BRIDGE_REQUEST_CHAR_UUID,
        view,
      );
      chunkIdx += 1;
      this.onChunkProgress?.(chunkIdx, totalChunks);
      onProgress?.(Math.min(offset + slice.length, bytes.length), bytes.length);
    }
  }

  async fetch(
    input: string,
    init?: RequestInit,
    onProgress?: (current: number, max: number) => void,
  ): Promise<Response> {
    const method = (init?.method as HttpMethod) ?? "GET";
    const headers: Record<string, string> = {};
    if (init?.headers) {
      new Headers(init.headers).forEach((v, k) => {
        headers[k] = v;
      });
    }

    let body: unknown;
    if (init?.body != null) {
      if (typeof init.body === "string") {
        try {
          body = JSON.parse(init.body);
        } catch {
          body = init.body;
        }
      } else {
        throw new TypeError(
          "BleBridge.fetch only supports string/JSON request bodies",
        );
      }
    }

    const reply = await this.request({ method, url: input, headers, body }, onProgress);
    if (reply.error) {
      throw new Error(reply.error);
    }
    return new Response(reply.body, {
      status: reply.status,
      headers: reply.headers,
    });
  }
}
