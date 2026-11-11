// Client half of the rsync-style delta protocol for OTA frontend updates.
// See server/rsync_delta.py's module docstring for the full rationale (BLE
// bandwidth is scarce and a whole-bundle re-download on every release is the
// single biggest contributor to the write-lock-hogging transfers that cause
// update-loop symptoms) and for why matching is done across the whole pool
// of a device's old files rather than per-path (Vite content-hashes JS/CSS
// filenames, so a changed file's name changes right along with its content).
//
// This file mirrors server/rsync_delta.py's algorithm independently (same
// rolling checksum formula, same SHA-256-truncated strong hash) rather than
// sharing code with it, since one side runs in Python and the other in a
// browser/WebView -- compute_delta()'s self-test there is what verifies the
// algorithm itself; this file only needs to agree with it on the wire
// format and produce byte-identical signatures/reconstructions.

// Must match BLOCK_SIZE in server/rsync_delta.py.
export const RSYNC_BLOCK_SIZE = 4096;

// Largest prime below 2**16, same modulus server/rsync_delta.py uses.
const MOD = 65521;

export interface BlockSignature {
  weak: number;
  strong: string;
}

export interface FileSignature {
  path: string;
  size: number;
  blocks: BlockSignature[];
}

export type DeltaOp = { c: { p: string; i: number } } | { d: number };

export interface FileDelta {
  path: string;
  mime: string;
  size: number;
  ops: DeltaOp[];
  literal: string; // base64 of gzip of this file's concatenated literal bytes
}

function initChecksum(data: Uint8Array, start: number, length: number): [number, number] {
  let a = 0;
  let b = 0;
  for (let i = 0; i < length; i++) {
    const byte = data[start + i];
    a += byte;
    b += (length - i) * byte;
  }
  return [a % MOD, b % MOD];
}

function rollChecksum(a: number, b: number, outByte: number, inByte: number, windowLen: number): [number, number] {
  const newA = ((a - outByte + inByte) % MOD + MOD) % MOD;
  const newB = ((b - windowLen * outByte + newA) % MOD + MOD) % MOD;
  return [newA, newB];
}

function weakChecksum(data: Uint8Array, start: number, length: number): number {
  const [a, b] = initChecksum(data, start, length);
  // `<<` and `|` operate on SIGNED 32-bit ints in JS -- whenever b >= 32768,
  // (b << 16) sets the sign bit and the result comes out negative, while
  // Python's (b << 16) | a (arbitrary-precision ints, no such thing as a
  // sign bit here) stays positive for the exact same (a, b). Server and
  // client would then disagree on this block's weak checksum for roughly
  // half of all blocks, so the server's lookup almost never finds a block
  // the client actually has -- confirmed against real dist/ output: 17 of
  // 36 blocks in one file alone. `>>> 0` reinterprets the bits as unsigned,
  // matching Python's value exactly.
  return ((b << 16) | a) >>> 0;
}

async function strongChecksum(data: Uint8Array, start: number, length: number): Promise<string> {
  // Truncated SHA-256, same choice and same reasoning as
  // server/rsync_delta.py's strong_checksum(): no interop requirement with
  // real rsync, so a hash with no known collisions beats rsync's original
  // MD4/MD5, and 16 hex chars keeps the signature payload compact.
  const digest = await crypto.subtle.digest("SHA-256", data.slice(start, start + length));
  const bytes = new Uint8Array(digest);
  let hex = "";
  for (let i = 0; i < 8; i++) hex += bytes[i].toString(16).padStart(2, "0");
  return hex;
}

export async function computeSignatures(data: Uint8Array, blockSize = RSYNC_BLOCK_SIZE): Promise<BlockSignature[]> {
  const blocks: BlockSignature[] = [];
  for (let i = 0; i < data.length; i += blockSize) {
    const len = Math.min(blockSize, data.length - i);
    blocks.push({
      weak: weakChecksum(data, i, len),
      strong: await strongChecksum(data, i, len),
    });
  }
  return blocks;
}

function gzipDecompress(bytes: Uint8Array): Promise<Uint8Array> {
  const stream = new Blob([bytes as BlobPart]).stream().pipeThrough(new DecompressionStream("gzip"));
  return new Response(stream).arrayBuffer().then((buf) => new Uint8Array(buf));
}

function base64ToBytes(b64: string): Uint8Array {
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

// Reconstructs one file's exact raw bytes from the server's delta plus this
// device's own old files (path -> raw bytes, from whatever it had on disk
// before this update). A "c" op copies a block.blockSize-sized slice out of
// the referenced old file; a "d" op consumes the next N bytes from this
// file's own (gunzipped) literal buffer, in order.
export async function applyDelta(
  delta: FileDelta,
  oldFiles: Map<string, Uint8Array>,
  blockSize = RSYNC_BLOCK_SIZE,
): Promise<Uint8Array> {
  const literal = delta.literal ? await gzipDecompress(base64ToBytes(delta.literal)) : new Uint8Array(0);
  let literalPos = 0;
  const out = new Uint8Array(delta.size);
  let outPos = 0;
  for (const op of delta.ops) {
    if ("c" in op) {
      const oldData = oldFiles.get(op.c.p);
      if (!oldData) {
        throw new Error(`Delta referenced old file "${op.c.p}" that this device doesn't have`);
      }
      const start = op.c.i * blockSize;
      const slice = oldData.subarray(start, start + blockSize);
      out.set(slice, outPos);
      outPos += slice.length;
    } else {
      out.set(literal.subarray(literalPos, literalPos + op.d), outPos);
      literalPos += op.d;
      outPos += op.d;
    }
  }
  return out.subarray(0, outPos);
}
