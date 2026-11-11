"""
rsync-style delta computation for OTA frontend bundle updates.

The motivation is bandwidth, not disk: a frontend bundle update is carried
over this app's custom HTTP-over-Bluetooth bridge (see bluetooth_server.py),
which tops out far below Wi-Fi/LAN speeds and holds one global write lock for
an entire reply's duration. Re-sending the whole ~100-300KB bundle on every
release -- even when a change only touched one function -- is the single
biggest contributor to that lock being held a long time (see
frontend-update.svelte.ts's extensive comments on the knock-on effects: other
devices' requests queuing behind it, scouts getting update-loop symptoms).

This module implements the classic rsync algorithm (Tridgell & Mackerras,
"The rsync algorithm", 1996): the receiver (a scouting device) already has
*some* old version of the files and describes it to the sender (this server)
as a list of block checksums, not the files themselves; the sender finds
which parts of the new data match the old blocks (even if they moved) using
a cheap rolling checksum to locate candidates and a cryptographic hash to
confirm them, and describes the new data back as "copy this old block" /
"here are these new literal bytes" instructions. The receiver reconstructs
the new data from its own old bytes plus those instructions, without the
sender ever needing a copy of the receiver's old data.

One wrinkle specific to this app: Vite content-hashes JS/CSS output
filenames (dist/assets/index-<hash>.js), so a changed file's *name* changes
on every build right along with its content, and a plain per-path "diff this
new file against the old file of the same name" would almost never find a
match for exactly the files that matter most. compute_delta() below matches
each new file's blocks against a *global* pool of blocks from every old file
the client described, keyed by content rather than path, so unrelated code
that happens to still be byte-identical (shared vendor chunks, an unchanged
function, unchanged CSS) is still found and copied even though the file
around it was renamed.
"""

import base64
import gzip
import hashlib
from collections import defaultdict
from typing import TypedDict

# Must match RSYNC_BLOCK_SIZE in src/lib/rsync-delta.ts -- it's a plain
# shared constant rather than something negotiated per-request, since both
# sides are deployed from the same repo and there's nothing to gain from
# letting it vary.
BLOCK_SIZE = 4096

# Classic Adler-32-style rolling checksum. 65521 is the largest prime below
# 2**16 (the same modulus Adler-32 itself uses) -- any reasonably large prime
# works here, this isn't required to interoperate with anything outside this
# module and its TypeScript mirror.
_MOD = 65521


class BlockSignature(TypedDict):
    weak: int
    strong: str


class FileSignature(TypedDict):
    path: str
    size: int
    blocks: list[BlockSignature]


def _init_checksum(window: bytes) -> tuple[int, int]:
    a = 0
    b = 0
    length = len(window)
    for i, byte in enumerate(window):
        a += byte
        b += (length - i) * byte
    return a % _MOD, b % _MOD


def _roll_checksum(a: int, b: int, out_byte: int, in_byte: int, window_len: int) -> tuple[int, int]:
    """Advances a (a, b) checksum pair by one byte: drops `out_byte` (the
    byte leaving the window at its start) and appends `in_byte` (the byte
    entering at its end), without re-summing the whole window."""
    new_a = (a - out_byte + in_byte) % _MOD
    new_b = (b - window_len * out_byte + new_a) % _MOD
    return new_a, new_b


def weak_checksum(data: bytes) -> int:
    a, b = _init_checksum(data)
    return (b << 16) | a


def strong_checksum(data: bytes) -> str:
    # Truncated SHA-256 rather than rsync's original MD4/MD5 -- this is an
    # internal protocol with no interop requirement, and a cryptographic
    # hash with no known collision attacks is a strictly safer choice to
    # confirm a weak-checksum match before trusting it. 16 hex chars (8
    # bytes/64 bits) keeps the signature payload compact; a 64-bit hash
    # collision is astronomically unlikely for the handful of blocks a
    # frontend bundle breaks into, and a wrong guess here would only corrupt
    # the downloaded bundle (caught by the existing apply-failure path), not
    # anything security-sensitive.
    return hashlib.sha256(data).hexdigest()[:16]


def compute_signatures(data: bytes, block_size: int = BLOCK_SIZE) -> list[BlockSignature]:
    """Reference implementation of the receiver-side half of the algorithm --
    used by this module's own self-test (see __main__ below) to produce
    signatures in-process without needing the TypeScript client. The real
    client (src/lib/rsync-delta.ts) implements this independently."""
    blocks: list[BlockSignature] = []
    for i in range(0, len(data), block_size):
        chunk = data[i : i + block_size]
        blocks.append({"weak": weak_checksum(chunk), "strong": strong_checksum(chunk)})
    return blocks


class CopyOp(TypedDict):
    c: dict  # {"p": old path, "i": block index within that old file}


class LiteralOp(TypedDict):
    d: int  # number of bytes to take next from the file's `literal` buffer


def compute_delta(
    new_data: bytes,
    old_file_signatures: list[FileSignature],
    block_size: int = BLOCK_SIZE,
) -> dict:
    """Computes the sender side of the algorithm: given the bytes of one new
    file and the *client's* block signatures for all of its old files
    (regardless of path -- see module docstring), returns
    {"ops": [...], "literal": "<base64 of gzip of concatenated literal bytes>"}.

    Runtime is O(len(new_data)) in the common case (matches dominate) via the
    rolling checksum, falling back to O(len(new_data)) worst case with a
    larger constant when nothing matches (every position needs a fresh
    strong-hash check -- still linear, just not block_size-amortized).
    """
    n = len(new_data)
    ops: list[dict] = []
    literal_chunks: list[bytes] = []
    pending_literal_len = 0

    def flush_literal() -> None:
        nonlocal pending_literal_len
        if pending_literal_len:
            ops.append({"d": pending_literal_len})
            pending_literal_len = 0

    if n == 0:
        return {"ops": [], "literal": ""}

    # Keyed by (weak, length), not just weak -- every block is block_size
    # long *except* the last block of whichever file it came from, which is
    # almost always shorter (a file's size is rarely an exact multiple of
    # block_size). Folding length into the key lets the final, necessarily
    # short window at the end of new_data still match a same-length old
    # trailing block, without a short window ever being compared against a
    # full-size one (which could only coincidentally collide, never
    # correctly match -- they cover different amounts of data).
    weak_index: dict[tuple[int, int], list[tuple[str, int, str]]] = defaultdict(list)
    for file_sig in old_file_signatures:
        blocks = file_sig["blocks"]
        size = file_sig["size"]
        for idx, block in enumerate(blocks):
            is_last = idx == len(blocks) - 1
            length = size - idx * block_size if is_last else block_size
            weak_index[(block["weak"], length)].append((file_sig["path"], idx, block["strong"]))

    if not weak_index:
        # No old data at all (fresh install) -- everything is literal, same
        # cost as today's full-bundle download.
        return {"ops": [{"d": n}], "literal": _compress(new_data)}

    i = 0
    window_len = min(block_size, n)
    a, b = _init_checksum(new_data[0:window_len])

    while i < n:
        window_len = min(block_size, n - i)
        match: tuple[str, int] | None = None
        weak = (b << 16) | a
        candidates = weak_index.get((weak, window_len))
        if candidates:
            strong = strong_checksum(new_data[i : i + window_len])
            for path, idx, candidate_strong in candidates:
                if candidate_strong == strong:
                    match = (path, idx)
                    break

        if match is not None:
            flush_literal()
            ops.append({"c": {"p": match[0], "i": match[1]}})
            i += window_len
            if i < n:
                next_len = min(block_size, n - i)
                a, b = _init_checksum(new_data[i : i + next_len])
            continue

        literal_chunks.append(new_data[i : i + 1])
        pending_literal_len += 1
        i += 1
        if i < n:
            next_len = min(block_size, n - i)
            if window_len == block_size and next_len == block_size:
                out_byte = new_data[i - 1]
                in_byte = new_data[i + block_size - 1]
                a, b = _roll_checksum(a, b, out_byte, in_byte, block_size)
            else:
                a, b = _init_checksum(new_data[i : i + next_len])

    flush_literal()

    literal_bytes = b"".join(literal_chunks)
    return {"ops": ops, "literal": _compress(literal_bytes) if literal_bytes else ""}


def _compress(data: bytes) -> str:
    return base64.b64encode(gzip.compress(data)).decode("ascii")


def _decompress(data_b64: str) -> bytes:
    if not data_b64:
        return b""
    return gzip.decompress(base64.b64decode(data_b64))


def apply_delta(delta: dict, old_files: dict[str, bytes]) -> bytes:
    """Reference reconstruction, mirroring what the TypeScript client
    (applyDelta() in src/lib/rsync-delta.ts) does with a real old bundle.
    Used by this module's self-test to verify compute_delta() end to end
    without a browser. `old_files`: path -> full old file bytes.
    `delta["blockSize"]` is required (or pass block_size explicitly -- see
    __main__) since reconstructing a copy op needs it to slice the right
    byte range out of the referenced old file.
    """
    block_size = delta["blockSize"]
    literal = _decompress(delta.get("literal", ""))
    literal_pos = 0
    out = bytearray()
    for op in delta["ops"]:
        if "c" in op:
            path = op["c"]["p"]
            index = op["c"]["i"]
            old_data = old_files[path]
            start = index * block_size
            out += old_data[start : start + block_size]
        else:
            length = op["d"]
            out += literal[literal_pos : literal_pos + length]
            literal_pos += length
    return bytes(out)


if __name__ == "__main__":
    import random

    def _assert_roll_matches_init() -> None:
        rng = random.Random(42)
        data = bytes(rng.randrange(256) for _ in range(5000))
        block_size = 37  # deliberately not a power of two / not BLOCK_SIZE
        a, b = _init_checksum(data[0:block_size])
        for i in range(1, len(data) - block_size):
            out_byte = data[i - 1]
            in_byte = data[i + block_size - 1]
            a, b = _roll_checksum(a, b, out_byte, in_byte, block_size)
            expected_a, expected_b = _init_checksum(data[i : i + block_size])
            assert (a, b) == (expected_a, expected_b), f"roll mismatch at i={i}"
        print("OK: rolling checksum matches from-scratch computation at every offset")

    def _assert_round_trip(name: str, old_files: dict[str, bytes], new_data: bytes, block_size: int = 16) -> dict:
        signatures = [
            {"path": path, "size": len(data), "blocks": compute_signatures(data, block_size)}
            for path, data in old_files.items()
        ]
        delta = compute_delta(new_data, signatures, block_size)
        delta["blockSize"] = block_size
        reconstructed = apply_delta(delta, old_files)
        assert reconstructed == new_data, f"{name}: reconstruction mismatch"
        print(f"OK: {name} ({len(delta['ops'])} ops, {len(delta.get('literal') or '')} b64 literal bytes)")
        return delta

    _assert_roll_matches_init()

    # Identical content -- should copy, essentially no literal bytes.
    content = bytes(range(256)) * 10
    d = _assert_round_trip("identical file", {"old.js": content}, content)
    assert all("c" in op for op in d["ops"]), "identical content should be all copies"

    # Completely unrelated content -- should be all-literal.
    import os as _os

    unrelated = _os.urandom(500)
    d = _assert_round_trip("completely different content", {"old.js": content}, unrelated)
    assert all("d" in op for op in d["ops"]), "unrelated content should be all literal"

    # Small edit in the middle -- most of the file should still copy.
    edited = content[:100] + b"EDITED" + content[100:]
    _assert_round_trip("small insertion in the middle", {"old.js": content}, edited)

    # Classic rsync strength test: inserting bytes at the very start shifts
    # every subsequent block's byte offset, so a naive fixed-offset diff
    # would see zero overlap -- the rolling checksum must still find all of
    # it shifted.
    shifted = b"XYZ123" + content
    d = _assert_round_trip("insertion at the start (block-shifting)", {"old.js": content}, shifted)
    copy_ops = [op for op in d["ops"] if "c" in op]
    assert len(copy_ops) >= len(content) // 16 - 2, "shifted content should still mostly copy"

    # A file's last block is almost never a full block_size (file sizes are
    # rarely exact multiples of it) -- that shorter final block must still
    # be matchable, including when it lands at the very end of the new file
    # too (the one place the main scan loop can't roll any further and has
    # to evaluate a short window).
    odd_sized = content + b"tail"  # not a multiple of block_size=16
    _assert_round_trip("unchanged trailing partial block", {"old.js": odd_sized}, odd_sized)
    d = _assert_round_trip(
        "unchanged trailing partial block, content prepended",
        {"old.js": odd_sized},
        b"prefix-" + odd_sized,
    )
    assert any("c" in op for op in d["ops"]), "trailing partial block should still be found and copied"

    # Cross-file matching: content moved to a differently-named/hashed file,
    # the scenario this module exists for (Vite's content-hashed filenames).
    _assert_round_trip(
        "content moved to a renamed file (vite hash change)",
        {"assets/index-OLDHASH.js": content},
        content + b"new trailing code",
    )

    # No prior bundle at all (fresh install) -- must fall back to all-literal
    # cleanly, not crash on an empty signature list.
    empty_delta = compute_delta(content, [], block_size=16)
    assert empty_delta["ops"] == [{"d": len(content)}]
    assert apply_delta({**empty_delta, "blockSize": 16}, {}) == content
    print("OK: fresh install (no old signatures) falls back to all-literal")

    # Empty new file.
    assert compute_delta(b"", [{"path": "x", "size": 0, "blocks": []}], 16) == {"ops": [], "literal": ""}
    print("OK: empty new file produces no ops")

    print("\nAll rsync_delta self-tests passed.")
