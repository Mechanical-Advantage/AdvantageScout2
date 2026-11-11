import json
import os
import argparse
import socket
import mimetypes
import shutil
import subprocess
import threading
import time
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import global_data as global_data
import data_init
import data_update
import schedule
import rsync_delta
from config import config
import logging
from typing import List

app = FastAPI(title="Scouting App")
logger = logging.getLogger("uvicorn.error")

server_config = {
    "host": "0.0.0.0",
    "port": 6328,
}

os.makedirs(os.path.join(config.WEB_DIR, "assets"), exist_ok=True)
os.makedirs(os.path.join(config.WEB_DIR, "fonts"), exist_ok=True)
os.makedirs(os.path.join(config.WEB_DIR, "images"), exist_ok=True)

app.mount(
    "/assets",
    StaticFiles(directory=os.path.join(config.WEB_DIR, "assets")),
    name="assets",
)
app.mount(
    "/fonts",
    StaticFiles(directory=os.path.join(config.WEB_DIR, "fonts")),
    name="fonts",
)
app.mount(
    "/images",
    StaticFiles(directory=os.path.join(config.WEB_DIR, "images")),
    name="images",
)
favicon_path = os.path.join(config.WEB_DIR, "favicon.ico")


origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "*",  # Temporary
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/", include_in_schema=False)
def index():
    index_path = os.path.join(config.WEB_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"error": "index.html not found"}, status_code=404)


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return JSONResponse({"error": "favicon.ico not found"}, status_code=404)


@app.get("/version.txt", include_in_schema=False)
def version_txt():
    version_path = os.path.join(config.WEB_DIR, "version.txt")
    if os.path.exists(version_path):
        return FileResponse(version_path, media_type="text/plain")
    return JSONResponse({"error": "version.txt not found"}, status_code=404)


def get_frontend_version() -> str:
    version_path = os.path.join(config.WEB_DIR, "version.txt")
    try:
        with open(version_path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"


@app.get("/api/frontend_version")
def frontend_version():
    return {"version": get_frontend_version()}


frontend_files_cache = {"version": None, "files": None}


def get_frontend_files() -> list:
    """Returns this version's dist/ files as {path, mime, raw} (raw, undecorated
    bytes -- callers compress/encode as needed for their own response shape).
    Cached per version since dist/ doesn't change without a new build, and
    frontend_delta() re-reads this on every request.
    """
    version = get_frontend_version()
    if (
        frontend_files_cache["version"] == version
        and frontend_files_cache["files"] is not None
    ):
        return frontend_files_cache["files"]

    files = []
    for root, dirs, filenames in os.walk(config.WEB_DIR):
        for filename in filenames:
            if filename == "version.txt":
                continue
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, config.WEB_DIR).replace(os.sep, "/")
            with open(full_path, "rb") as f:
                raw = f.read()
            mime, _ = mimetypes.guess_type(filename)
            files.append({"path": rel_path, "mime": mime or "application/octet-stream", "raw": raw})

    frontend_files_cache["version"] = version
    frontend_files_cache["files"] = files
    return files


@app.post("/api/frontend_delta")
def frontend_delta(payload: dict):
    """Computes an rsync-style delta of the current frontend bundle against
    whatever old bundle the requesting device describes (see rsync_delta.py
    for why -- short version: BLE bandwidth is scarce, and re-sending a whole
    ~100-300KB bundle for a one-line change wastes most of a transfer that
    already risks starving other devices' requests). `payload["files"]` is a
    list of {"path", "blocks": [{"weak", "strong"}, ...]} describing the
    device's own old files; an empty list (fresh install, nothing to diff
    against) degrades gracefully to a full literal transfer per file, the
    same cost as the old /api/frontend_bundle endpoint this replaces.
    """
    old_signatures = payload.get("files", [])
    version = get_frontend_version()
    result_files = []
    for f in get_frontend_files():
        delta = rsync_delta.compute_delta(f["raw"], old_signatures)
        result_files.append(
            {
                "path": f["path"],
                "mime": f["mime"],
                "size": len(f["raw"]),
                "ops": delta["ops"],
                "literal": delta["literal"],
            }
        )
    return {"version": version, "blockSize": rsync_delta.BLOCK_SIZE, "files": result_files}


@app.get("/api/game_fields/{mode}")
def game_fields(mode: str):
    if mode not in ("match", "super", "pit"):
        return JSONResponse({"error": "Mode not found"}, status_code=404)

    try:
        compiled, _sql_columns = data_init.compile_game_json(mode)
        return compiled
    except FileNotFoundError:
        return JSONResponse({"error": "File not found"}, status_code=404)


@app.get("/api/devices_info")
def devices_info():
    info = global_data.get_devices_info()
    return {"devices": info, "serverTime": time.time() * 1000}


@app.get("/api/device_messages/{device}")
def device_message(device: str):
    messages = global_data.get_messages_for_device(device)
    return messages


@app.get("/api/global_settings")
def get_global_settings():
    settings = global_data.get_settings()
    return settings


@app.get("/api/match_scout_list")
def get_match_scout_list():
    scouts = schedule.get_match_scouts()
    return scouts


@app.get("/api/super_scout_list")
def get_super_scout_list():
    scouts = schedule.get_super_scouts()
    return scouts


@app.get("/api/current_schedule")
def get_current_schedule():
    current_schedule = schedule.current_match_schedule()
    if current_schedule is None:
        return JSONResponse(
            {"error": "No match schedule generated yet"}, status_code=404
        )
    return current_schedule


@app.get("/api/current_super_schedule")
def get_current_super_schedule():
    current_schedule = schedule.current_super_schedule()
    if current_schedule is None:
        return JSONResponse(
            {"error": "No super schedule generated yet"}, status_code=404
        )
    return current_schedule


@app.get("/api/current_schedule_status")
def get_current_schedule_status():
    status = schedule.current_match_schedule_status()
    if status is None:
        return JSONResponse(
            {"error": "No match schedule generated yet"}, status_code=404
        )
    return status


@app.get("/api/current_super_schedule_status")
def get_current_super_schedule_status():
    status = schedule.current_super_schedule_status()
    if status is None:
        return JSONResponse(
            {"error": "No super schedule generated yet"}, status_code=404
        )
    return status


@app.get("/api/all_matches_status")
def get_all_matches_status():
    return schedule.all_matches_upload_status()


@app.get("/api/all_super_matches_status")
def get_all_super_matches_status():
    return schedule.all_super_matches_upload_status()


@app.post("/api/advance_schedule_check")
def post_advance_schedule_check():
    return schedule.advance_current_match_if_needed()


@app.post("/api/force_match")
def force_match(payload: dict):
    try:
        match_number = int(payload["match"])
    except (KeyError, TypeError, ValueError):
        return JSONResponse({"error": "Invalid match number"}, status_code=400)
    schedule.set_current_match_number(match_number)
    return {"current_match": match_number}


@app.post("/api/refresh_schedule_from_tba")
def post_refresh_schedule_from_tba():
    try:
        schedule.refresh_schedule_from_tba()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    return {"status": "ok"}


@app.post("/api/generate_schedule")
def post_generate_schedule():
    try:
        schedule.generate_schedule()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    return {"status": "ok"}


@app.post("/api/send_devices_messages")
def send_devices_messages(payload: List[dict]):
    global_data.add_messages(payload)
    return {"status": "ok"}


@app.post("/api/remove_device")
def remove_device(payload: dict):
    global_data.remove_device(payload["device"])
    return {"status": "ok"}


@app.post("/api/game_data")
def game_data(payload: List[dict]):
    print("Data received:")
    print(json.dumps(payload, indent=2))

    if not payload:
        return {"status": "ok", "message": "No data provided"}

    db_routing_map = {
        "match": (config.MATCH_DB_PATH, config.MATCH_TABLE),
        "super": (config.SUPER_DB_PATH, config.SUPER_TABLE),
        "pit": (config.PIT_DB_PATH, config.PIT_TABLE),
    }

    grouped_data = {}

    for item in payload:
        mode = str(item.get("Mode", "")).lower()

        if mode not in db_routing_map:
            print(f"Warning: Skipping item with unknown mode '{mode}'")
            continue

        routing_destination = db_routing_map[mode]

        cleaned_item = {k: v for k, v in item.items() if k != "Mode"}
        cleaned_item["Event"] = config.EVENT

        if routing_destination not in grouped_data:
            grouped_data[routing_destination] = []

        grouped_data[routing_destination].append(cleaned_item)

    for (db_path, table_name), items in grouped_data.items():
        data_update.insert_data(items, db_path, table_name)

    if (config.MATCH_DB_PATH, config.MATCH_TABLE) in grouped_data:
        schedule.advance_current_match_if_needed()

    return {"status": "ok"}


@app.post("/api/game_data_active")
def game_data_active(payload: dict):
    print("Active data received:")
    print(json.dumps(payload, indent=2))
    return {"status": "ok"}


@app.post("/api/global_settings")
def set_global_settings(payload: dict):
    global_data.set_settings(payload)
    return {"status": "ok"}


@app.post("/api/match_scout_list")
def set_match_scout_list(payload: dict):
    schedule.update_match_scouts(payload)
    return {"status": "ok"}


@app.post("/api/super_scout_list")
def set_super_scout_list(payload: dict):
    schedule.update_super_scouts(payload)
    return {"status": "ok"}


@app.post("/api/heartbeat")
def heartbeat(payload: dict):
    name = payload.pop("device", None)
    if name:
        logger.info(f"Heartbeat from {name}")
        payload["timestamp"] = time.time() * 1000
        data = {"Name": name, "LastHeartbeat": payload}
        data_update.update_data(
            data=[data],
            db_path=config.GLOBAL_DB_PATH,
            table="devices",
            conflict_col="Name",
            target_column="LastHeartbeat",
        )
        return {"status": "ok"}
    else:
        raise JSONResponse({"error": "Invalid device name"}, status_code=400)


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print("WebSocket connected:", websocket.client)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print("WebSocket disconnected:", websocket.client)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.append(connection)
        for ws in disconnected:
            self.disconnect(ws)


manager = ConnectionManager()

FRONTEND_WATCH_PATHS = [
    "src",
    "games",
    "index.html",
    "vite.config.ts",
    "svelte.config.js",
    "tsconfig.json",
    "assets",
]
FRONTEND_IGNORE_DIRS = {"node_modules", "dist", ".git", "android", ".venv", "data"}


def watch_log(msg: str) -> None:
    print(f"[frontend-watch] {msg}", flush=True)


def run_frontend_build_and_sync():
    top_dir = config.TOP_DIR
    for label, cmd in (
        ("npm run build", ["npm", "run", "build"]),
        ("npx cap sync android", ["npx", "cap", "sync", "android"]),
    ):
        watch_log(f"Running `{label}`...")
        resolved = shutil.which(cmd[0])
        if resolved is None:
            watch_log(f"`{label}` failed: `{cmd[0]}` not found on PATH")
            return
        result = subprocess.run(
            [resolved, *cmd[1:]], cwd=top_dir, capture_output=True, text=True
        )
        if result.stdout.strip():
            watch_log(f"{label}:\n{result.stdout.strip()}")
        if result.returncode != 0:
            watch_log(
                f"`{label}` failed (exit {result.returncode}):\n{result.stderr.strip()}"
            )
            return
    watch_log("Rebuild + sync complete.")


def _watch_frontend_and_rebuild():
    from watchfiles import watch

    top_dir = config.TOP_DIR
    watch_paths = [
        os.path.join(top_dir, p)
        for p in FRONTEND_WATCH_PATHS
        if os.path.exists(os.path.join(top_dir, p))
    ]

    def _filter(change, path: str) -> bool:
        parts = set(os.path.relpath(path, top_dir).split(os.sep))
        return not (parts & FRONTEND_IGNORE_DIRS)

    watch_log(f"Watching for frontend changes in: {', '.join(FRONTEND_WATCH_PATHS)}")
    for changes in watch(*watch_paths, watch_filter=_filter):
        watch_log(f"Detected {len(changes)} change(s), rebuilding...")
        run_frontend_build_and_sync()


def start_frontend_watcher():
    watch_log("Building frontend before startup...")
    run_frontend_build_and_sync()

    thread = threading.Thread(target=_watch_frontend_and_rebuild, daemon=True)
    thread.start()


@app.get("/{full_path:path}", include_in_schema=False)
def spa_redirect(full_path: str):
    if full_path == "api" or full_path.startswith("api/"):
        return JSONResponse({"error": "Not found"}, status_code=404)
    return RedirectResponse(url=f"/#/{full_path}")


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scouting Server")
    parser.add_argument(
        "--regen-db", action="store_true", help="Regenerate Database from game JSON"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable uvicorn auto-reload on server/*.py changes",
    )
    parser.add_argument(
        "--quiet",
        action="store_false",
        help="Disable logging for requests to the server",
    )

    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=6328)

    args = parser.parse_args()

    server_config["host"] = args.host
    server_config["port"] = args.port

    if args.regen_db:
        data_init.init_database_fields(True)
    else:
        data_init.init_database_fields(False)
    global_data.ensure_default_settings()
    config.update_config()

    local_ip = get_local_ip()
    host_message = f"Hosting at: http://{local_ip}:{args.port}"
    print("-" * len(host_message))
    print(host_message)
    print("-" * len(host_message))

    if args.reload:
        start_frontend_watcher()

        existing_pythonpath = os.environ.get("PYTHONPATH")
        os.environ["PYTHONPATH"] = (
            config.SERVER_DIR
            if not existing_pythonpath
            else os.pathsep.join([config.SERVER_DIR, existing_pythonpath])
        )

    uvicorn.run(
        "http_server:app",
        host=server_config["host"],
        port=server_config["port"],
        reload=args.reload,
        access_log=args.quiet,
        reload_dirs=[config.SERVER_DIR] if args.reload else None,
    )
