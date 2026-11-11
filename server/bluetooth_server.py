"""
Architecture:
  * This script is the BLE PERIPHERAL (GATT server). It advertises the
    bridge service and waits for a central to connect.
  * The TABLET is the BLE CENTRAL: it scans for the advertised service
    UUID, connects, subscribes to notifications, and writes requests.

Setup:
  pip install bless requests

  # Linux may need:
  sudo setcap cap_net_raw,cap_net_admin+eip $(which python3)
  # or just run with sudo.

  # macOS / Windows: no extra setup; BlueZ / WinRT handle permissions.

  python bluetooth_server.py

GATT layout (must match bluetooth-http-bridge.ts on the phone):
  Service  : 6e400001-b5a3-f393-e0a9-e50e24dcca9e   (Nordic UART layout)
  Request  : 6e400002-b5a3-f393-e0a9-e50e24dcca9e   write          phone -> pc
  Response : 6e400003-b5a3-f393-e0a9-e50e24dcca9e   notify/read    pc   -> phone

Framing: both directions use the same magic + length-prefixed binary frame

Protocol:
  Request:  {"id","method","url","headers","body"}
  Reply:    {"id","status","headers","body","error"}
"""

import argparse
import asyncio
import json
import logging
import signal
import struct
import sys
import zlib
from typing import Any, Optional
from urllib.parse import urljoin
from typing import Dict
from config import config
import requests
from bless import (  # type: ignore[import-not-found]
    BlessGATTCharacteristic,
    BlessServer,
    GATTAttributePermissions,
    GATTCharacteristicProperties,
)

# bless 0.3.0's CoreBluetooth delegate (bless/backends/corebluetooth/
# peripheral_manager_delegate.py) discards the CBCentral identity of every
# write request before calling into application code. Without it, two
# simultaneously-connected devices' writes can interleave into the same
# shared request-reassembly buffer and corrupt each other's requests.
#
# bless hardcodes constructing its own base delegate class inside
# BlessServerCoreBluetooth.__init__ with no way to inject a different one
# through its public API, so the only way to recover each write's central
# identity is to subclass the delegate (confirmed empirically that a genuine
# CoreBluetooth-dispatched callback only honors a *subclass* override, not
# an instance-level monkeypatch of the same method) and swap bless's
# module-level reference to it before constructing BlessServer.
#
# This patch does NOT also target replies at the specific requesting
# central (bless's update_value() always broadcasts notifications to every
# subscribed central, via a hardcoded onSubscribedCentrals: None) -- an
# earlier version of this code did that too, but targeting a specific
# CBCentral via onSubscribedCentrals: turned out to be unreliable in
# practice (broke even the single-device case until the process was
# restarted) and couldn't be verified against real hardware from this dev
# environment (macOS can't discover its own simultaneously advertised
# peripheral, so there's no way to test central-targeted delivery here with
# two real connections). So replies still broadcast to everyone, same as
# before this patch -- a second connected device will see replies meant for
# others and ignore them by `id` (src/lib/ble-bridge.ts's resolvePending()),
# wasteful but correct.
if sys.platform == "darwin":
    import objc  # type: ignore[import-not-found]
    from bless.backends.corebluetooth.peripheral_manager_delegate import (  # type: ignore[import-not-found]
        PeripheralManagerDelegate,
    )
    import bless.backends.corebluetooth.server as _cb_server_module  # type: ignore[import-not-found]
    from CoreBluetooth import CBATTErrorSuccess  # type: ignore[import-not-found]

    class _MultiCentralPeripheralManagerDelegate(PeripheralManagerDelegate):  # type: ignore[misc]
        # Only the central's UUID *string* is captured here (for keying the
        # per-central request buffers in BleBridgeServer), not the CBCentral
        # object itself -- an earlier version also cached CBCentral objects
        # to target replies at a specific device via
        # updateValue:forCharacteristic:onSubscribedCentrals:, but that
        # turned out to be unreliable in practice (see _notify_chunk) and
        # has been reverted. Keeping just the UUID bookkeeping here since
        # it's what makes per-central request buffers possible.

        def peripheralManager_didReceiveReadRequest_(self, peripheral_manager, request):  # noqa: N802,E501
            # Side channel for _on_read (server/bluetooth_server.py) to read
            # synchronously, within the same call stack, right after
            # read_request_func runs below. Safe because bless processes
            # requests one at a time on its own serial dispatch queue (see
            # PeripheralManagerDelegate.init()).
            self._pending_read_central_uuid = request.central().identifier().UUIDString()
            objc.super(
                _MultiCentralPeripheralManagerDelegate, self
            ).peripheralManager_didReceiveReadRequest_(peripheral_manager, request)

        def peripheralManager_didReceiveWriteRequests_(self, peripheral_manager, requests):  # noqa: N802,E501
            for request in requests:
                char = request.characteristic()
                value = request.value()
                # Side channel for _on_write (server/bluetooth_server.py),
                # same reasoning as _pending_read_central_uuid above.
                self._pending_central_uuid = request.central().identifier().UUIDString()
                self.write_request_func(char.UUID().UUIDString(), value)
            peripheral_manager.respondToRequest_withResult_(requests[0], CBATTErrorSuccess)

    _cb_server_module.PeripheralManagerDelegate = _MultiCentralPeripheralManagerDelegate

# bless 0.3.0's WinRT backend (bless/backends/winrt/server.py) has the same
# problem as its CoreBluetooth backend above: write_characteristic() and
# read_characteristic() never look at the WinRT event args' `.session`
# property (which identifies which connected device made the request), so
# application code has no way to tell two simultaneously-connected devices'
# requests apart.
#
# Unlike the macOS patch above, this does NOT hand the device identity off
# through a shared instance-attribute side channel. bless's macOS delegate
# is documented to serialize callbacks on one dedicated dispatch queue
# (PeripheralManagerDelegate.init()), which is what makes a side channel
# safe there; nothing here establishes the same guarantee for WinRT's GATT
# event callbacks, which are COM/WinRT events that may not be guaranteed to
# run one at a time on a single thread. So two devices writing at nearly
# the same time could clobber a shared attribute before it's read. Instead,
# write_characteristic/read_characteristic are reimplemented (rather than
# wrapped) to thread the device id through as an explicit argument, all the
# way to write_request_func/read_request_func (_on_write/_on_read) below --
# no shared mutable state involved, so it can't race regardless of which
# thread(s) WinRT invokes these callbacks from.
#
# UNVERIFIED AGAINST REAL HARDWARE: this was written and developed on
# macOS, which cannot run or test the WinRT backend at all. The
# `args.session.device_id.id` attribute chain was confirmed against the
# actual type stubs shipped in both winrt-Windows.Devices.Bluetooth.* (used
# on Python 3.12+) and bleak-winrt (used on Python <3.12, which is what
# this project's own requirements-windows.txt installs) -- not just
# inferred from documentation -- but the control flow (deferral timing,
# threading behavior, WRITE_WITHOUT_RESPONSE handling) has only been
# reasoned through by reading bless's existing implementation, never run.
# Please verify this on a real Windows machine with two BLE centrals
# connected before relying on it.
if sys.platform == "win32":
    from bless.exceptions import BlessError  # type: ignore[import-not-found]

    if sys.version_info >= (3, 12):
        from winrt.windows.devices.bluetooth.genericattributeprofile import (  # type: ignore[import-not-found] # noqa: E501
            GattWriteOption,
        )
        from winrt.windows.storage.streams import DataReader, DataWriter  # type: ignore[import-not-found] # noqa: E501
    else:
        from bleak_winrt.windows.devices.bluetooth.genericattributeprofile import (  # type: ignore[import-not-found] # noqa: E501
            GattWriteOption,
        )
        from bleak_winrt.windows.storage.streams import DataReader, DataWriter  # type: ignore[import-not-found] # noqa: E501

    class _MultiClientBlessServerWinRT(BlessServer):  # type: ignore[misc]
        @staticmethod
        def _device_uuid(args: Any) -> Optional[str]:
            try:
                session = args.session
                return session.device_id.id if session is not None else None
            except Exception:
                return None

        # Reimplements bless's read_characteristic/write_characteristic
        # (bless/backends/winrt/server.py) rather than wrapping them with
        # super(), so the device id extracted above can be passed through
        # as an explicit argument instead of a shared attribute (see the
        # threading-safety reasoning in the comment above this class).
        def read_characteristic(self, sender: Any, args: Any) -> None:
            deferral = args.get_deferral()
            if deferral is None:
                return
            device_uuid = self._device_uuid(args)
            value = self.read_request(str(sender.uuid), device_uuid=device_uuid)
            value = value if value is not None else b"\x00"
            writer = DataWriter()
            writer.write_bytes(value)

            request = None

            async def f() -> None:
                nonlocal request
                request = await args.get_request_async()

            asyncio.new_event_loop().run_until_complete(f())
            request.respond_with_value(writer.detach_buffer())
            deferral.complete()

        def write_characteristic(self, sender: Any, args: Any) -> None:
            deferral = args.get_deferral()
            if deferral is None:
                return
            device_uuid = self._device_uuid(args)

            request = None

            async def f() -> None:
                nonlocal request
                request = await args.get_request_async()

            asyncio.new_event_loop().run_until_complete(f())
            reader = DataReader.from_buffer(request.value)
            if reader is None:
                return
            n_bytes = reader.unconsumed_buffer_length
            value = bytearray()
            for _ in range(n_bytes):
                value.append(reader.read_byte())

            self.write_request(str(sender.uuid), value, device_uuid=device_uuid)

            if request.option == GattWriteOption.WRITE_WITH_RESPONSE:
                request.respond()
            deferral.complete()

        # Overrides of BaseBlessServer.read_request/write_request
        # (bless/backends/server.py) -- same job, plus forwarding
        # device_uuid through to read_request_func/write_request_func
        # (_on_read/_on_write) as an explicit keyword argument.
        def read_request(
            self, uuid: str, options: Optional[dict] = None, device_uuid: Optional[str] = None
        ) -> bytearray:
            characteristic = self.get_characteristic(uuid)
            if not characteristic:
                raise BlessError("Invalid characteristic: {}".format(uuid))
            return self.read_request_func(characteristic, device_uuid=device_uuid)

        def write_request(self, uuid: str, value: Any, device_uuid: Optional[str] = None) -> None:
            characteristic = self.get_characteristic(uuid)
            self.write_request_func(characteristic, value, device_uuid=device_uuid)

SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
REQUEST_CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
RESPONSE_CHAR_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

# payload is UTF-8 JSON, zlib-deflated (RFC 1950 — matches the Web Streams
# API's "deflate" format, i.e. CompressionStream/DecompressionStream on the
# phone side) when FRAME_FLAG_DEFLATE is set in flags, raw UTF-8 JSON
# otherwise. Compression is skipped per-frame when it doesn't actually
# shrink the payload (small messages have little redundancy, and zlib's own
# header/trailer can make them larger).
FRAME_MAGIC = b"\xab\xcd"
FRAME_FLAG_DEFLATE = 0x01
FRAME_HEADER_LEN = 7  # magic (2) + length (4) + flags (1)


def pack_frame(payload: bytes) -> bytes:
    compressed = zlib.compress(payload, 6)
    if len(compressed) < len(payload):
        flags, body = FRAME_FLAG_DEFLATE, compressed
    else:
        flags, body = 0, payload
    return FRAME_MAGIC + struct.pack(">IB", len(body), flags) + body


def unpack_payload(flags: int, body: bytes) -> bytes:
    return zlib.decompress(body) if flags & FRAME_FLAG_DEFLATE else body


DEVICE_NAME: str = "Advscout"

BASE_URL: Optional[str] = None

HTTP_TIMEOUT: float = 30.0

NOTIFY_CHUNK_BYTES: int = 244

INTER_CHUNK_DELAY_S: float = 0.004

MAX_BODY_BYTES: int = 12 * 1024 * 1024

log = logging.getLogger("bt-bridge")


def forward_http(
    msg: dict,
    base_url: Optional[str],
    timeout: float,
    tag: str = "",
) -> dict:
    req_id = msg.get("id", "")
    method = (msg.get("method") or "GET").upper()
    url = msg.get("url") or ""
    headers = msg.get("headers") or {}
    body = msg.get("body", None)
    prefix = f"{tag} " if tag else ""

    if base_url and not url.lower().startswith(("http://", "https://")):
        url = urljoin(base_url.rstrip("/") + "/", url.lstrip("/"))

    reply: dict[str, Any] = {
        "id": req_id,
        "status": 0,
        "headers": {},
        "body": "",
        "error": None,
    }

    try:
        kwargs: dict[str, Any] = {"headers": headers, "timeout": timeout}
        if body is not None:
            if isinstance(body, (dict, list)):
                kwargs["json"] = body
            else:
                kwargs["data"] = body

        log.info("%s[%s] -> %s %s", prefix, req_id[:8], method, url)
        resp = requests.request(method, url, **kwargs)

        raw = resp.content[:MAX_BODY_BYTES]
        try:
            text = raw.decode(resp.encoding or "utf-8", errors="replace")
        except LookupError:
            text = raw.decode("utf-8", errors="replace")

        reply["status"] = resp.status_code
        # Omit HTTP headers — the client never reads them and they add
        # ~200 bytes to every reply frame, increasing the BLE notification count.
        reply["headers"] = {}
        reply["body"] = text
        log.info(
            "%s[%s] <- %s (%d bytes)", prefix, req_id[:8], resp.status_code, len(raw)
        )
    except requests.RequestException as e:
        reply["error"] = f"{type(e).__name__}: {e}"
        log.warning("%s[%s] !! %s", prefix, req_id[:8], reply["error"])

    return reply


class BleBridgeServer:
    def __init__(
        self,
        device_name: str,
        base_url: Optional[str],
        timeout: float,
        chunk_bytes: int,
        inter_chunk_delay: float = INTER_CHUNK_DELAY_S,
    ) -> None:
        self.device_name = device_name
        self.base_url = base_url
        self.timeout = timeout
        self.chunk_bytes = chunk_bytes
        self.inter_chunk_delay = inter_chunk_delay

        # Incoming bytes accumulate here until a full frame is available,
        # keyed by central UUID (or None on platforms without the per-central
        # delegate patch above, i.e. everywhere but macOS) so that two
        # simultaneously-connected devices' writes can't interleave into the
        # same buffer and corrupt each other's requests.
        self._bufs: Dict[Optional[str], bytearray] = {}

        # Last response payload per central — served from reads too, so a
        # central that doesn't subscribe to notifications can still poll.
        self._last_responses: Dict[Optional[str], bytes] = {}

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._server: Optional[BlessServer] = None
        self._write_lock = asyncio.Lock()
        self._stop_event = asyncio.Event()

    def _pending_central_uuid(self, attr: str) -> Optional[str]:
        # The delegate stashes which central a write/read just came from in
        # this attribute (set just before calling into us, within the same
        # synchronous call stack) — see the _MultiCentralPeripheralManagerDelegate
        # patch above. Absent on non-macOS platforms, where there's only ever
        # one shared bucket (keyed by None), matching the original behavior.
        delegate = getattr(self._server, "peripheral_manager_delegate", None)
        return getattr(delegate, attr, None) if delegate is not None else None

    def _on_read(
        self,
        characteristic: BlessGATTCharacteristic,
        device_uuid: Optional[str] = None,
        **_: Any,
    ) -> bytes:
        # Central is reading the response characteristic directly (rare — they
        # usually subscribe to notifications). Return whatever was last sent
        # to THIS central.
        if characteristic.uuid.lower() == RESPONSE_CHAR_UUID.lower():
            # On Windows, _MultiClientBlessServerWinRT passes device_uuid
            # explicitly (see its own comment for why: no shared-attribute
            # side channel there). Everywhere else, fall back to the
            # macOS delegate's side channel (None on Linux, matching the
            # original single-bucket behavior there).
            central_uuid = (
                device_uuid
                if device_uuid is not None
                else self._pending_central_uuid("_pending_read_central_uuid")
            )
            return self._last_responses.get(central_uuid, b"")
        return b""

    def _on_write(
        self,
        characteristic: BlessGATTCharacteristic,
        value: bytearray,
        device_uuid: Optional[str] = None,
        **_: Any,
    ) -> None:
        # bless invokes this from its own thread (on macOS, from a CoreBluetooth
        # dispatch queue via PyObjC) — any exception raised in here has no
        # Python call stack above it to report to, so it's logged explicitly
        # rather than left to propagate and vanish silently.
        try:
            central_uuid = (
                device_uuid
                if device_uuid is not None
                else self._pending_central_uuid("_pending_central_uuid")
            )
            log.info(
                "write received: central=%s char=%s len=%d first=%s",
                central_uuid,
                characteristic.uuid,
                len(value),
                bytes(value[:8]).hex(),
            )
            if characteristic.uuid.lower() != REQUEST_CHAR_UUID.lower():
                log.debug(
                    "write to unexpected char %s (len=%d)",
                    characteristic.uuid,
                    len(value),
                )
                return

            buf = self._bufs.setdefault(central_uuid, bytearray())
            buf.extend(value)
            self._drain_request_frames(central_uuid)
        except Exception:
            log.exception("unhandled error in _on_write")

    def _drain_request_frames(self, central_uuid: Optional[str]) -> None:
        buf = self._bufs[central_uuid]
        while True:
            magic_idx = buf.find(FRAME_MAGIC)
            if magic_idx == -1:
                log.info(
                    "no frame magic in buffer yet (central=%s buf_len=%d first=%s)",
                    central_uuid,
                    len(buf),
                    bytes(buf[:8]).hex(),
                )
                # Keep the last byte in case it's the first half of a split magic pair.
                if len(buf) > 1:
                    del buf[: len(buf) - 1]
                return
            if magic_idx > 0:
                del buf[:magic_idx]
            if len(buf) < FRAME_HEADER_LEN:
                log.info(
                    "waiting for frame header (central=%s buf_len=%d)",
                    central_uuid,
                    len(buf),
                )
                return  # wait for the rest of the header

            length, flags = struct.unpack(">IB", buf[2:FRAME_HEADER_LEN])
            if length <= 0 or length > MAX_BODY_BYTES:
                # Corrupt/garbage length — resync by dropping the false magic and rescanning.
                log.warning("bad frame length=%d flags=%d; resyncing", length, flags)
                del buf[:2]
                continue

            total = FRAME_HEADER_LEN + length
            if len(buf) < total:
                log.info(
                    "waiting for frame body (central=%s have=%d need=%d)",
                    central_uuid,
                    len(buf),
                    total,
                )
                return  # wait for the rest of the body

            body = bytes(buf[FRAME_HEADER_LEN:total])
            del buf[:total]

            if self._loop is not None:
                # Schedule HTTP forwarding on the main loop.
                asyncio.run_coroutine_threadsafe(
                    self._handle_frame(flags, body, central_uuid),
                    self._loop,
                )

    async def _handle_frame(
        self, flags: int, body: bytes, central_uuid: Optional[str]
    ) -> None:
        try:
            payload = unpack_payload(flags, body)
            msg = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, zlib.error) as e:
            # BLE writes to the request characteristic are unacknowledged,
            # so a dropped chunk leaves this central's buffer waiting on
            # bytes that will never arrive; once a later request's bytes
            # accumulate to spuriously satisfy that stale `total`, body ends
            # up a corrupt mix of two requests and fails to decode here.
            # Whatever's left in the buffer past this point is equally
            # suspect (same reasoning as the client's BleBridge.drainFrames()),
            # so drop it rather than let it silently corrupt every request
            # after it from this same central. Scoped to just this central's
            # buffer — one device's corrupted frame shouldn't wipe out a
            # different, unrelated device's in-flight request.
            self._bufs[central_uuid].clear()
            reply = {
                "id": "",
                "status": 0,
                "headers": {},
                "body": "",
                "error": f"bad json: {e}",
            }
            await self._send_reply(reply, central_uuid)
            return

        reply = await asyncio.to_thread(
            forward_http,
            msg,
            self.base_url,
            self.timeout,
            "[ble]",
        )
        await self._send_reply(reply, central_uuid)

    def _notify_chunk(self, char: Any, chunk: bytes) -> bool:
        # NOTE: this broadcasts to every subscribed central rather than
        # targeting just the one that made this request. An earlier version
        # of this code targeted the specific CBCentral via
        # onSubscribedCentrals:, which
        # turned out to be unreliable on at least one real macOS setup (it
        # broke even the single-device case until the process was
        # restarted) and couldn't be verified against real hardware from
        # this environment (macOS can't discover its own simultaneously
        # advertised peripheral, so there's no way to test central-targeted
        # delivery here with two real connections). Broadcasting is the
        # behavior this was already shipping with before that attempt, so
        # it's the safer default until targeted delivery can be verified
        # against real devices. A second connected device will still see
        # replies meant for others and ignore them by `id`
        # (src/lib/ble-bridge.ts's resolvePending()) — wasteful but correct.
        try:
            from Foundation import NSData  # type: ignore[import]

            pm = self._server.peripheral_manager_delegate.peripheral_manager  # type: ignore[union-attr]
            data = NSData.dataWithBytes_length_(chunk, len(chunk))
            return bool(
                pm.updateValue_forCharacteristic_onSubscribedCentrals_(
                    data, char.obj, None
                )
            )
        except Exception as exc:
            log.debug("NSData path unavailable (%s), using bless update_value", exc)
        # Fallback: bless's own update_value (works on Linux / Windows, but
        # always broadcasts to every subscribed central — those backends
        # don't currently get the per-central delegate patch above).
        char.value = bytearray(chunk)
        return self._server.update_value(SERVICE_UUID, RESPONSE_CHAR_UUID)  # type: ignore[union-attr]

    async def _send_reply(self, reply: dict, central_uuid: Optional[str]) -> None:
        if self._server is None:
            return

        body = json.dumps(reply, ensure_ascii=False).encode("utf-8")
        framed = pack_frame(body)

        # Cache for optional polling reads.
        self._last_responses[central_uuid] = framed

        async with self._write_lock:
            # Fragment across notifications and use the return value of
            # updateValue:forCharacteristic: as backpressure.  CoreBluetooth
            # returns NO when its outbound queue is full; spinning on True
            # (rather than a fixed sleep) gives us the radio's actual line rate
            # without ever overwriting an unsent fragment.
            chunk_count = -(-len(framed) // self.chunk_bytes)
            for chunk_idx, i in enumerate(range(0, len(framed), self.chunk_bytes)):
                chunk = framed[i : i + self.chunk_bytes]
                char = self._server.get_characteristic(RESPONSE_CHAR_UUID)
                if char is None:
                    log.warning("response characteristic missing")
                    return
                log.info(
                    "[%s] chunk %d/%d len=%d first=%s",
                    reply.get("id", "")[:8],
                    chunk_idx + 1,
                    chunk_count,
                    len(chunk),
                    chunk[:8].hex(),
                )

                backoff = 0.001
                deadline_attempts = 0
                while True:
                    ok = self._notify_chunk(char, bytes(chunk))
                    if ok:
                        break
                    deadline_attempts += 1
                    if deadline_attempts > 500:
                        # ~10 s of a permanently full queue means the link
                        # is dead; abandon this reply rather than block
                        # other requests forever.
                        log.warning(
                            "[%s] notify queue stuck; dropping remainder",
                            reply.get("id", "")[:8],
                        )
                        return
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 1.5, 0.05)
                # Pace delivery so the Android central's notification receive
                # buffer doesn't overflow and silently drop packets. BLE notify
                # has no ACK; the only protection is not sending too fast.
                if self.inter_chunk_delay > 0:
                    await asyncio.sleep(self.inter_chunk_delay)

    async def run(self) -> None:
        self._loop = asyncio.get_running_loop()
        server_cls = (
            _MultiClientBlessServerWinRT if sys.platform == "win32" else BlessServer
        )
        self._server = server_cls(name=self.device_name, loop=self._loop)
        self._server.read_request_func = self._on_read
        self._server.write_request_func = self._on_write

        await self._server.add_new_service(SERVICE_UUID)

        # Write-only (plus write-without-response for low-latency chunks from
        # the phone), no encryption/bonding — keep it simple. If you need
        # auth, switch permissions to encryption_required / authentication_required.
        await self._server.add_new_characteristic(
            SERVICE_UUID,
            REQUEST_CHAR_UUID,
            GATTCharacteristicProperties.write
            | GATTCharacteristicProperties.write_without_response,
            None,
            GATTAttributePermissions.writeable,
        )

        await self._server.add_new_characteristic(
            SERVICE_UUID,
            RESPONSE_CHAR_UUID,
            GATTCharacteristicProperties.read | GATTCharacteristicProperties.notify,
            None,
            GATTAttributePermissions.readable,
        )

        # bless's CoreBluetooth backend drops the service UUID from the
        # advertisement whenever prioritize_local_name is true (the default)
        # and the device name is >10 bytes — the Android app's scan filters
        # on that UUID at the OS level, so without this the phone never even
        # sees the advertisement.
        await self._server.start(prioritize_local_name=False)
        log.info(
            "advertising '%s' - waiting for a central to connect", self.device_name
        )

        try:
            await self._stop_event.wait()
        finally:
            log.info("stopping GATT server")
            try:
                await self._server.stop()
            except Exception as e:
                log.warning("server stop error: %s", e)

    def stop(self) -> None:
        if self._loop is not None and not self._stop_event.is_set():
            self._loop.call_soon_threadsafe(self._stop_event.set)


def run_bridge(
    *,
    device_name: str = DEVICE_NAME,
    base_url: Optional[str] = None,
    timeout: float = HTTP_TIMEOUT,
    chunk_bytes: int = NOTIFY_CHUNK_BYTES,
    inter_chunk_delay: float = INTER_CHUNK_DELAY_S,
    install_signal_handlers: bool = True,
) -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
            datefmt="%H:%M:%S",
        )

    server = BleBridgeServer(
        device_name, base_url, timeout, chunk_bytes, inter_chunk_delay
    )

    async def _main() -> None:
        if install_signal_handlers:
            loop = asyncio.get_running_loop()
            stop_sigs = [signal.SIGINT]
            if hasattr(signal, "SIGTERM"):
                stop_sigs.append(signal.SIGTERM)
            for sig in stop_sigs:
                try:
                    loop.add_signal_handler(sig, server.stop)
                except NotImplementedError:
                    # Windows ProactorEventLoop doesn't support add_signal_handler;
                    # fall back to the synchronous signal module. It still fires,
                    # just on the main thread instead of as a loop callback.
                    signal.signal(sig, lambda *_: server.stop())
        await server.run()

    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        pass


def main() -> int:
    p = argparse.ArgumentParser(
        description="BLE GATT peripheral -> HTTP bridge",
    )
    p.add_argument(
        "--name",
        default=DEVICE_NAME,
        help=f"Advertised BLE local name (default: {DEVICE_NAME!r})",
    )
    p.add_argument(
        "--base-url",
        default=BASE_URL,
        help="Base URL prepended to relative paths from the client",
    )
    p.add_argument(
        "--timeout",
        type=float,
        default=HTTP_TIMEOUT,
        help=f"HTTP request timeout, seconds (default: {HTTP_TIMEOUT})",
    )
    p.add_argument(
        "--chunk-bytes",
        type=int,
        default=NOTIFY_CHUNK_BYTES,
        help=f"Notification fragment size (default: {NOTIFY_CHUNK_BYTES})",
    )
    p.add_argument(
        "--inter-chunk-delay",
        type=float,
        default=INTER_CHUNK_DELAY_S,
        help=f"Delay between notification chunks in seconds (default: {INTER_CHUNK_DELAY_S}). "
        "Set to 0 to disable. Paces delivery so Android's BLE receive buffer doesn't overflow.",
    )
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    run_bridge(
        device_name=args.name,
        base_url=args.base_url,
        timeout=args.timeout,
        chunk_bytes=args.chunk_bytes,
        inter_chunk_delay=args.inter_chunk_delay,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
