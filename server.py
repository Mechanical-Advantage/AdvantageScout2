import base64
import json
import sqlite3 as sql
import sys
from pathlib import Path

import cherrypy
import tbapy
import time
import threading
import os
from ws4py.messaging import TextMessage
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
from simple_websocket_server import WebSocketServer, WebSocket

from config import *
from scheduler import Scheduler
from svelte_interface import SvelteInterface
from util import *
from enum import Enum


# Global variables
tba = tbapy.TBA(tba_key)
root_server = None
admin_server = None
svelte_interface = SvelteInterface()
scheduler = Scheduler()
admin_clients = []

# Init forwarding variables
forward_queues = {}
forward_threads = {}


if bt_enable:
    import serial


def init_global():
    """Creates the global database."""
    conn_global = sql.connect(db_global)
    cur_global = conn_global.cursor()
    cur_global.execute("DROP TABLE IF EXISTS devices")
    cur_global.execute("""CREATE TABLE devices (
        name TEXT,
        last_heartbeat INTEGER,
        last_route TEXT,
        last_battery INTEGER,
        last_charging INTEGER,
        last_status TEXT,
        last_team INTEGER,
        last_match INTEGER,
        last_scoutname TEXT
        ); """)
    cur_global.execute("DROP TABLE IF EXISTS messages")
    cur_global.execute("""CREATE TABLE messages (
        target TEXT,
        expiration INTEGER,
        text TEXT
        ); """)
    cur_global.execute("DROP TABLE IF EXISTS scouts")
    cur_global.execute("""CREATE TABLE scouts (
        name TEXT,
        enabled INTEGER
        ); """)
    cur_global.execute("""CREATE TABLE scout_prefs (
        priority INTEGER UNIQUE,
        team INTEGER,
        scout TEXT
        ); """)
    cur_global.execute("DROP TABLE IF EXISTS schedule_next")
    cur_global.execute("""CREATE TABLE schedule_next (
        team INTEGER,
        scout TEXT
        ); """)
    cur_global.execute("DROP TABLE IF EXISTS schedule")
    cur_global.execute("""CREATE TABLE schedule (
        match INTEGER,
        b1 INTEGER,
        b2 INTEGER,
        b3 INTEGER,
        r1 INTEGER,
        r2 INTEGER,
        r3 INTEGER
        ); """)
    cur_global.execute("DROP TABLE IF EXISTS config")
    cur_global.execute("""CREATE TABLE config (
        key TEXT,
        value TEXT
        ); """)
    cur_global.execute(
        "INSERT INTO config (key, value) VALUES ('game', ?)", (default_game,))
    cur_global.execute(
        "INSERT INTO config (key, value) VALUES ('event', '2022nhgrs')")
    cur_global.execute(
        "INSERT INTO config (key, value) VALUES ('reverse_alliances', '0')")
    cur_global.execute(
        "INSERT INTO config (key, value) VALUES ('dev_mode', '0')")
    cur_global.execute(
        "INSERT INTO config (key, value) VALUES ('schedule_match', '-1')")
    cur_global.execute(
        "INSERT INTO config (key, value) VALUES ('schedule_key', '')")
    cur_global.execute(
        "INSERT INTO config (key, value) VALUES ('event_cached', 'none')")
    cur_global.execute(
        "INSERT INTO config (key, value) VALUES ('auto_schedule', '0')")
    conn_global.commit()
    conn_global.close()


def init_game():
    """Creates the game database."""
    conn_game = gamedb_connect(force_connect=True)
    cur_game = conn_game.cursor()
    config = json.loads(read_text("games" + os.path.sep +
                                  get_game() + ".json"))

    # Matches table
    create_text = "Event TEXT, Team INTEGER, Match INTEGER, DeviceName TEXT, Version TEXT, InterfaceType TEXT, Time INTEGER, UploadTime INTEGER, ScoutName TEXT, "
    for i in range(len(config["fields"])):
        create_text += config["fields"][i] + ","
    create_text = create_text[:-1]
    cur_game.execute("DROP TABLE IF EXISTS match")
    cur_game.execute("CREATE TABLE match (" + create_text + ")")

    # Pit scouting table
    if "pitFields" in config:
        create_text = "Event TEXT, Team INTEGER, DeviceName TEXT, Version TEXT, Time INTEGER, UploadTime INTEGER, ScoutName TEXT, "
        for i in range(len(config["pitFields"])):
            create_text += config["pitFields"][i] + ","
        create_text = create_text[:-1]
        cur_game.execute("DROP TABLE IF EXISTS pit")
        cur_game.execute("CREATE TABLE pit (" + create_text + ")")

    conn_game.commit()
    conn_game.close()


class Root(object):
    """Class for root paths on the web server."""

    def _cp_dispatch(self, vpath):
        global admin_server
        if len(vpath) > 0 and vpath[0] == "admin":
            vpath.pop(0)
            return admin_server

    @cherrypy.expose
    def index(self):
        index_html = ""
        with open(get_absolute_path("app.html"), "r") as index_file:
            index_html = index_file.read()
        return index_html.replace("ISWEB", "true")

    @cherrypy.expose
    def request(self, query, data="{}"):
        # Open databases and prepare data
        conn_global = sql.connect(db_global)
        cur_global = conn_global.cursor()
        conn_game = gamedb_connect()
        cur_game = conn_game.cursor()
        request_data = json.loads(data)
        response = {}

        # Download app - return app data if hash has changed
        # {
        #   "hash": "def345dc57c4b5dc166b82d02b92c34f"
        # } -> {
        #   "changed": True,
        #   "data": {
        #       "hash": "8ef2d05085cb90ee8adb8db41dd58e84",
        #       "config": {...},
        #       "css": "...",
        #       "js": "..."
        #   }
        # }
        if query == "download_app":
            changed = False
            app_data_response = None
            if "hash" not in request_data or request_data["hash"] != svelte_interface.get_app()["hash"]:
                changed = True
                app_data_response = svelte_interface.get_app()
            response = {
                "changed": changed,
                "data": app_data_response
            }

        # Heartbeat - record device status
        # {
        #   "deviceName": "Example Device",
        #   "state": "idle"/"auto"/"teleop"/"endgame"/"pit",
        #   "battery": 100,
        #   "charging": False,
        #   "scoutName": "John Doe",
        #   "team": 6328, (optional)
        #   "match": 42, (optional)
        #   "route": "COM1" (optional)
        # } -> {
        #   "messages": [...]
        # }
        elif query == "heartbeat":
            if "route" in request_data:
                route = request_data["route"]
            else:
                route = cherrypy.request.remote.ip

            names = [x[0] for x in cur_global.execute(
                "SELECT name FROM devices").fetchall()]
            if request_data["deviceName"] not in names:
                cur_global.execute("INSERT INTO devices (name, last_heartbeat, last_route, last_battery, last_charging, last_status, last_scoutname) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                   (request_data["deviceName"], int_time(), route, request_data["battery"], 1 if request_data["charging"] else 0, request_data["state"], request_data["scoutName"]))
            else:
                cur_global.execute("UPDATE devices SET last_heartbeat = ?, last_route = ?, last_battery=?, last_charging = ?, last_status = ?, last_scoutname = ? WHERE name = ?",
                                   (int_time(), route, request_data["battery"], 1 if request_data["charging"] else 0, request_data["state"], request_data["scoutName"], request_data["deviceName"]))

            if "team" in request_data:
                cur_global.execute(
                    "UPDATE devices SET last_team = ? WHERE name = ?", (request_data["team"], request_data["deviceName"]))
            if "match" in request_data:
                cur_global.execute(
                    "UPDATE devices SET last_match = ? WHERE name = ?", (request_data["match"], request_data["deviceName"]))
            cur_global.execute(
                "DELETE FROM messages WHERE expiration<?", (int_time(),))
            messages = [x[0] for x in cur_global.execute(
                "SELECT text FROM messages WHERE target=?", (request_data["deviceName"],))]
            cur_global.execute(
                "DELETE FROM messages WHERE target=?", (request_data["deviceName"],))
            conn_global.commit()
            AdminWebSocketHandler.broadcast_update()
            response = {
                "messages": messages
            }

        # Upload - saves a single match
        # {
        #   "IsMatch": True,
        #   "Event": "2022nhgrs",
        #   "Team": 6328,
        #   "Match": 42, (if type is match)
        #   "DeviceName": "Example Device",
        #   "Version": "web"/"Android 2.0.0",
        #   "Time": 1641013200,
        #   "ScoutName": "John Doe",
        #   ... (game fields)
        # } -> {
        #   "success": True
        # }
        elif query == "upload":
            prefs = json.loads(
                read_text("games" + os.path.sep + get_game() + ".json"))
            response = {
                "success": False
            }

            # Check for duplicate matches
            if request_data["IsMatch"]:
                duplicate_count = cur_game.execute("SELECT COUNT(*) FROM match WHERE Event=? AND Team=? AND Match=? AND DeviceName=? AND Time=?", (
                    request_data["Event"], request_data["Team"], request_data["Match"], request_data["DeviceName"], request_data["Time"])).fetchall()[0][0]
            else:
                duplicate_count = cur_game.execute("SELECT COUNT(*) FROM pit WHERE Event=? AND Team=? AND DeviceName=? AND Time=?", (
                    request_data["Event"], request_data["Team"], request_data["DeviceName"], request_data["Time"])).fetchall()[0][0]

            if duplicate_count == 0:
                # Create full list of fields to scan
                to_save = {}
                if request_data["IsMatch"]:
                    fields = prefs["fields"] + ["Event TEXT", "Team INTEGER", "Match INTEGER", "DeviceName TEXT",
                                                "Version TEXT", "InterfaceType TEXT", "Time INTEGER", "UploadTime INTEGER", "ScoutName TEXT"]
                else:
                    fields = prefs["pitFields"] + ["Event TEXT", "Team INTEGER", "DeviceName TEXT",
                                                   "Version TEXT", "Time INTEGER", "UploadTime INTEGER", "ScoutName TEXT"]

                # Scan fields (saving images as necessary)
                for full_field_name in fields:
                    field_name = full_field_name.split(" ")[0]
                    if field_name in request_data:
                        if request_data[field_name].startswith("data:image/jpeg;base64,"):
                            previous_images = os.listdir(image_dir)
                            max_id = -1
                            for name in previous_images:
                                if name.startswith("IMG_"):
                                    id = int(name[4:9])
                                    if id > max_id:
                                        max_id = id

                            file_path = image_dir + os.path.sep + \
                                "IMG_" + str(max_id + 1).zfill(5) + ".jpg"
                            image_file = open(file_path, "wb")
                            image_file.write(base64.decodebytes(
                                request_data[field_name][23:].encode("utf-8")))
                            image_file.close()
                            to_save[field_name] = file_path
                        else:
                            to_save[field_name] = request_data[field_name]

                # Add upload time and save to database
                fields = ["UploadTime"]
                values = [str(int_time())]
                for field, value in to_save.items():
                    fields.append(field)
                    values.append(str(value))
                if request_data["IsMatch"]:
                    table = "pit"
                else:
                    table = "match"
                cur_game.execute("INSERT INTO " + table + " (" + ",".join(fields) +
                                 ") VALUES (" + ",".join(["?"] * len(fields)) + ")", tuple(values))
                conn_game.commit()
                response = {
                    "success": True
                }

        # Get schedule - returns the schedule for the upcoming match
        # {} -> {
        #   "match": 42,
        #   "key": "gQHyjxLlADpFVsM",
        #   "teams": [6328, 6328, 6328, 6328, 6328, 6328],
        #   "scouts": ["John Doe", "John Doe", "John Doe", "John Doe", "John Doe", "John Doe"],
        #   "ready": [False, False, False, False, False, False]
        # }
        elif query == "get_schedule":
            event = cur_global.execute(
                "SELECT value FROM config WHERE key='event'").fetchall()[0][0]
            event_cached = cur_global.execute(
                "SELECT value FROM config WHERE key='event_cached'").fetchall()[0][0]
            if event == event_cached:
                match = cur_global.execute(
                    "SELECT value FROM config WHERE key='schedule_match'").fetchall()[0][0]
                key = cur_global.execute(
                    "SELECT value FROM config WHERE key='schedule_key'").fetchall()[0][0]
                schedule = cur_global.execute(
                    "SELECT * FROM schedule_next").fetchall()
                teams = []
                scouts = []
                ready = []
                for row in schedule:
                    teams.append(row[0])
                    scouts.append(row[1])
                    ready.append(cur_global.execute("SELECT COUNT() FROM devices WHERE last_team=? AND last_status<>'idle' AND (?-last_heartbeat) <= 30",
                                 (int(row[0]), round(time.time()))).fetchall()[0][0] > 0)
                response = {"match": match, "key": key,
                            "teams": teams, "scouts": scouts, "ready": ready}
            pass

        # Close databases and return result
        conn_global.close()
        conn_game.close()
        return json.dumps(response, separators=(",", ":"))


class Admin(object):
    """Class for the admin paths on the web server."""

    @cherrypy.expose
    def index(self):
        with open(get_absolute_path("admin.html"), "r") as admin_file:
            return admin_file.read()

    @cherrypy.expose("admin.css")
    def css(self):
        cherrypy.response.headers["Content-Type"] = "text/css"
        return svelte_interface.get_admin()["css"]

    @cherrypy.expose("admin.js")
    def js(self):
        cherrypy.response.headers["Content-Type"] = "text/javascript"
        return svelte_interface.get_admin()["js"]

    @cherrypy.expose
    def ws(self):
        pass

    @cherrypy.expose
    def add_scout(self, scout):
        conn_global = sql.connect(db_global)
        cur_global = conn_global.cursor()
        cur_global.execute(
            "INSERT INTO scouts(name,enabled) VALUES (?,0)", (scout,))
        conn_global.commit()
        conn_global.close()
        return

    @cherrypy.expose
    def get_scouts(self):
        conn_global = sql.connect(db_global)
        cur_global = conn_global.cursor()
        cur_global.execute("SELECT * FROM scouts ORDER BY name")
        raw = cur_global.fetchall()
        scouts = []
        for i in range(len(raw)):
            scouts.append({"name": raw[i][0], "enabled": raw[i][1] == 1})
        conn_global.commit()
        conn_global.close()
        return (json.dumps(scouts))

    @cherrypy.expose
    def remove_scout(self, scout):
        conn_global = sql.connect(db_global)
        cur_global = conn_global.cursor()
        print(scout)
        cur_global.execute("DELETE FROM scouts WHERE name=?", (scout,))
        conn_global.commit()
        conn_global.close()
        return

    @cherrypy.expose
    def toggle_scout(self, scout):
        conn_global = sql.connect(db_global)
        cur_global = conn_global.cursor()
        new = 1 - \
            cur_global.execute(
                "SELECT enabled FROM scouts WHERE name=?", (scout,)).fetchall()[0][0]
        cur_global.execute(
            "UPDATE scouts SET enabled=? WHERE name=?", (new, scout))
        conn_global.commit()
        conn_global.close()
        return

    @cherrypy.expose
    def get_devices(self):
        conn_global = sql.connect(db_global)
        cur_global = conn_global.cursor()
        cur_global.execute(
            "SELECT * FROM devices ORDER BY last_heartbeat DESC")
        raw = cur_global.fetchall()
        data = []
        for i in range(len(raw)):
            data.append({"name": raw[i][0], "last_heartbeat": raw[i][1], "last_route": raw[i][2], "last_battery": raw[i][3], "last_charging": raw[i]
                        [4], "last_status": raw[i][5], "last_team": raw[i][6], "last_match": raw[i][7], "last_scoutname": raw[i][8]})
        conn_global.close()
        return json.dumps(data)

    @cherrypy.expose
    def remove_device(self, name):
        conn_global = sql.connect(db_global)
        cur_global = conn_global.cursor()
        cur_global.execute("DELETE FROM devices WHERE name = ?", (name,))
        conn_global.commit()
        conn_global.close()
        return

    @cherrypy.expose
    def send_message(self, target, text):
        conn_global = sql.connect(db_global)
        cur_global = conn_global.cursor()
        cur_global.execute(
            "INSERT INTO messages(target,expiration,text) VALUES (?,?,?)", (target, round(time.time() + message_expiration), text))
        conn_global.commit()
        conn_global.close()
        return

    @cherrypy.expose
    def get_config(self):
        conn_global = sql.connect(db_global)
        cur_global = conn_global.cursor()
        cur_global.execute("SELECT value FROM config WHERE key = 'game'")
        data = {"game": cur_global.fetchall()[0][0]}
        cur_global.execute("SELECT value FROM config WHERE key = 'event'")
        data["event"] = cur_global.fetchall()[0][0]
        cur_global.execute(
            "SELECT value FROM config WHERE key = 'reverse_alliances'")
        data["reverse_alliances"] = cur_global.fetchall()[0][0]
        cur_global.execute("SELECT value FROM config WHERE key = 'dev_mode'")
        data["dev_mode"] = cur_global.fetchall()[0][0]
        cur_global.execute("SELECT * FROM scouts ORDER BY name")
        data["scouts"] = [{"name": x[0], "enabled": x[1] == 1}
                          for x in cur_global.fetchall()]
        cur_global.execute(
            "SELECT value FROM config WHERE key = 'event_cached'")
        data["event_cache"] = cur_global.fetchall()[0][0]
        cur_global.execute(
            "SELECT value FROM config WHERE key = 'auto_schedule'")
        data["auto_schedule"] = cur_global.fetchall()[0][0]
        conn_global.close()
        return json.dumps(data)

    @cherrypy.expose
    def set_config(self, key, value):
        conn_global = sql.connect(db_global)
        cur_global = conn_global.cursor()
        cur_global.execute(
            "UPDATE config SET value = ? WHERE key = ?", (value, key))
        conn_global.commit()
        conn_global.close()

        if key == "game":
            if Path(db_games.replace("$GAME", value)).is_file():
                response = "Updated game to \"" + value + "\""
            else:
                try:
                    init_game()
                    response = "Created database for game \"" + value + "\""
                except:
                    response = "Error: failed to create database for game \"" + \
                        value + "\". Check game prefs"
        elif key == "event":
            response = "Updated event to \"" + value + "\""
        elif key == "reverse_alliances":
            response = "Updated alliance position setting"
        elif key == "dev_mode":
            if value == "0":
                response = "Developer mode disabled"
            else:
                response = "Developer mode enabled"
        elif key == "auto_schedule":
            if value == "0":
                response = "Auto scheduling disabled"
            else:
                response = "Auto scheduling enabled"
        else:
            response = "Error: unknown key \"" + key + "\""
        return response

    @cherrypy.expose
    def get_cache(self, source="tba"):
        conn_global = sql.connect(db_global)
        cur_global = conn_global.cursor()
        event = cur_global.execute(
            "SELECT value FROM config WHERE key = 'event'").fetchall()[0][0]

        if source == "tba":
            # Get from the blue alliace
            try:
                matchlist_raw = tba.event_matches(event)
                matchlist_raw.sort(key=lambda x: x.match_number)
            except:
                return "Error - could not retrieve schedule"

            if len(matchlist_raw) == 0:
                return "Error - no schedule available"

            matches = []
            for match_raw in matchlist_raw:
                if match_raw.comp_level == "qm":
                    b1 = match_raw.alliances["blue"]["team_keys"][0][3:]
                    b2 = match_raw.alliances["blue"]["team_keys"][1][3:]
                    b3 = match_raw.alliances["blue"]["team_keys"][2][3:]
                    r1 = match_raw.alliances["red"]["team_keys"][0][3:]
                    r2 = match_raw.alliances["red"]["team_keys"][1][3:]
                    r3 = match_raw.alliances["red"]["team_keys"][2][3:]
                    matches.append(
                        [match_raw.match_number, b1, b2, b3, r1, r2, r3])
        else:
            # Get from csv
            try:
                csv = open(schedule_csv, "r")
            except:
                conn_global.close()
                return "Failed to open csv file."
            matches = [row.split(",") for row in csv.read().split("\n")]
            conn_global.close()
            csv.close()

        cur_global.execute("DELETE FROM schedule")
        cur_global.execute(
            "UPDATE config SET value=? WHERE key='event_cached'", (event,))
        for match in matches:
            try:
                cur_global.execute(
                    "INSERT INTO schedule(match,b1,b2,b3,r1,r2,r3) VALUES (?,?,?,?,?,?,?)", tuple(match))
            except:
                conn_global.close()
                return "Failed to save schedule data."

        conn_global.commit()
        conn_global.close()
        return "Saved schedule for " + event + "."

    @cherrypy.expose
    def reschedule(self, force_match=None):
        game_result = gamedb_connect()
        conn_game = game_result["conn"]
        cur_game = conn_game.cursor()
        conn_global = sql.connect(db_global)
        cur_global = conn_global.cursor()

        if force_match == None:
            match = scheduler.get_next_match()
        else:
            match = force_match
        success = scheduler.schedule_match(
            cur_game, cur_global, conn_global, match)

        conn_game.close()
        conn_global.close()
        if success:
            response = "Successfully created schedule for match " + \
                str(match) + "."
        else:
            response = "Failed to create schedule for match " + \
                str(match) + "."
        return response

    @cherrypy.expose
    def get_uploaded(self):
        conn_game = gamedb_connect()
        cur_game = conn_game.cursor()
        conn_global = sql.connect(db_global)
        cur_global = conn_global.cursor()

        event = cur_global.execute(
            "SELECT value FROM config WHERE key='event'").fetchall()[0][0]
        event_cached = cur_global.execute(
            "SELECT value FROM config WHERE key='event_cached'").fetchall()[0][0]
        output = []
        if event == event_cached:
            matches = cur_global.execute(
                "SELECT match,b1,b2,b3,r1,r2,r3 FROM schedule ORDER BY match").fetchall()
            for teams in matches:
                match_output = {"teams": teams[1:7], "uploaded": []}
                for team in teams[1:7]:
                    count = cur_game.execute(
                        "SELECT COUNT(*) FROM match WHERE Event=? AND Team=? AND Match=?", (event, team, teams[0])).fetchall()[0][0]
                    match_output["uploaded"].append(count > 0)
                output.append(match_output)

        conn_game.close()
        conn_global.close()
        return json.dumps(output)

    @cherrypy.expose
    def get_scoutprefs(self):
        conn_global = sql.connect(db_global)
        cur_global = conn_global.cursor()

        scout_prefs = []
        pref_data = cur_global.execute(
            "SELECT team, scout FROM scout_prefs ORDER BY priority").fetchall()
        for record in pref_data:
            scout_prefs.append({
                "team": record[0],
                "scout": record[1]
            })

        conn_global.close()
        return (json.dumps(scout_prefs))

    @cherrypy.expose
    def set_scoutprefs(self, data="[]"):
        conn_global = sql.connect(db_global)
        cur_global = conn_global.cursor()

        cur_global.execute("DELETE FROM scout_prefs")
        scout_prefs = json.loads(data)

        for i in range(len(scout_prefs)):
            cur_global.execute("INSERT INTO scout_prefs(priority,team,scout) VALUES (?,?,?)",
                               (i, scout_prefs[i]["team"], scout_prefs[i]["scout"]))
        conn_global.commit()
        conn_global.close()


class AdminWebSocketHandler(WebSocket):
    """WebSocket handler for each connection."""
    _admin_clients = []

    @classmethod
    def broadcast_update(cls):
        data = admin_server.get_devices()
        for client in cls._admin_clients:
            client.send(TextMessage(data))

    def opened(self):
        cherrypy.log("Opened admin WebSocket connection from " +
                     self.peer_address[0])
        self._admin_clients.append(self)

    def closed(self, code, _):
        cherrypy.log("Closed admin WebSocket connection from " +
                     self.peer_address[0])
        self._admin_clients.remove(self)


def log(output, before_text=""):
    if before_text == "":
        print(time.strftime("[%d/%b/%Y:%H:%M:%S] ") + output)
    else:
        print(before_text +
              time.strftime(" - - [%d/%b/%Y:%H:%M:%S] ") + output)


def serial_readline(source, name, mode):
    # Attempt to connect repeatedly
    def connect(ser):
        while True:
            try:
                ser.open()
            except:
                x = 0
            else:
                break

    # Timeout thread, resets line if no data for 3 seconds
    def timeout():
        nonlocal full_line
        while True:
            time.sleep(0.5)
            if last_data == -2:
                break
            if full_line != "" and time.time() - last_data > 3:
                log("Request timed out", name)
                full_line = ""

    full_line = ""
    last_data = -1
    timeout = threading.Thread(target=timeout, daemon=True)
    timeout.start()
    while True:
        if mode == serial_mode.WEBSOCKET:
            wait = True
            while wait:
                time.sleep(0.2)
                try:
                    wait = len(forward_queues[source]) == 0
                except:
                    return (False)
            line = forward_queues[source].pop(0)
        else:
            if source.is_open:
                line = source.readline().decode("utf-8")
            else:
                # Skip if not yet connected
                line = ""

        last_data = time.time()
        if line[-5:] == "CONT\n":
            full_line += line[:-5]
            if mode == serial_mode.WEBSOCKET:
                source.send_message("CONT\n")
            else:
                source.write("CONT\n".encode("utf-8"))
        elif line == "" and mode != serial_mode.WEBSOCKET:
            # Reconnect because device appears to be disconnected (timeout reached)
            if source.is_open:
                log("Disconnected, waiting", name)
            try:
                source.close()
            except:
                x = 0
            time.sleep(3)
            log("Trying to connect...", name)
            connect(source)
            log("Connected successfully, ready for data", name)
        else:
            full_line += line[:-1]
            break
    last_data = -2
    return (full_line)


class serial_mode(Enum):
    INCOMING = 0
    OUTGOING = 1
    WEBSOCKET = 2


def bluetooth_server(name, mode, client=None):
    if mode == serial_mode.WEBSOCKET:
        wait = True
        while wait:
            try:
                wait = len(forward_queues[client]) == 0
            except:
                return
        name = forward_queues[client].pop(0)
        log("Started forwarding thread", name)
    else:
        try:
            ser = serial.Serial()
            ser.port = name

            # Open immediately if incoming

            ser.timeout = 5
        except:
            log("WARNING - failed to connect to \"" +
                name + "\" Is the connection busy?")
            return

        type = "outgoing"
        log("Started Bluetooth server on " + type + " port \"" + name + "\"")

    while True:
        if mode == serial_mode.WEBSOCKET:
            raw = serial_readline(client, name, mode)
        else:
            raw = serial_readline(ser, name, mode)

        if raw == False:
            # Shutdown thread
            return

        try:
            msg = json.loads(raw)
        except:
            log("Unable to parse request", name)
            if mode == serial_mode.WEBSOCKET:
                client.send_message("[]\n")
            else:
                ser.write("[]\n".encode('utf-8'))
            continue

        try:
            if msg[1] == "load_data":
                config = quickread("cordova/config.xml").split('"')
                result = {"game": json.loads(main_server().load_game()), "config": json.loads(
                    main_server().get_config()), "version": config[3]}
            elif msg[1] == "upload":
                result = json.loads(main_server().upload(msg[2][0]))
            elif msg[1] == "heartbeat":
                data = msg[2]
                data["device_name"] = msg[0]
                data["route"] = name
                result = main_server().heartbeat(**data)
            elif msg[1] == "get_schedule":
                result = json.loads(main_server().get_schedule())
            else:
                result = "error"
        except:
            log("Unable to process request", name)
            if mode == serial_mode.WEBSOCKET:
                client.send_message("[]\n")
            else:
                ser.write("[]\n".encode('utf-8'))
        else:
            response = [msg[0], result]
            if mode == serial_mode.WEBSOCKET:
                client.send_message(json.dumps(response) + "\n")
            else:
                ser.write((json.dumps(response) + "\n").encode('utf-8'))
            if bt_showheartbeats or msg[1] != "heartbeat":
                log("\"" + msg[1] + "\" from device \"" + msg[0] + "\"", name)

# Break data into 2000 byte chunks


def serial_writeline(source, name, mode, data):

   
    continueQueue = []
    breakFrequency = 2000
    dataLeft = data
    
    while (len(dataLeft) > breakFrequency):
        continueQueue.append((dataLeft[0:breakFrequency]) + 'CONT')
        dataLeft = dataLeft[2000:]
    continueQueue.append(dataLeft[:])


    for outputLine in continueQueue:
        if mode == serial_mode.WEBSOCKET:
            serial.write(json.dumps(outputLine + "\n"))
            # wait for a response from websocket connections?
        else:
            serial.write(json.dumps(outputLine + "\n".encode('utf-8')))
            response = source.readline().decode("utf-8")
            # wait for timeout - how to do this
        if len(continueQueue) != 1:
            if response != "CONT\n":
                log("Bad response from device", name)
                return

    
    if len(continueQueue) == 1:
        if mode == serial_mode.WEBSOCKET:
            source.send_message(json.dumps(continueQueue[0]) + "\n")
        else:
            serial.write(json.dumps(continueQueue[0]) + "\n".encode('utf-8'))
        return
    else:
        for outputLine in continueQueue:
            if mode == serial_mode.WEBSOCKET:
                source.send_message(json.dumps(outputLine + "\n"))
                wait = True
                responseTime = time.time()
                while wait:
                    time.sleep(0.2)
                    if time.time() - responseTime > 3:
                        return (False)
                    try:
                        wait = len(forward_queues[source]) == 0

                    except:
                        return (False)
                response = forward_queues[source].pop(0)
            
            else:
                serial.write(json.dumps(outputLine + "\n".encode('utf-8')))
                response = source.readline().decode("utf-8")
                
                # wait for timeout - how to do this
                if response != "CONT\n":
                    log("Bad response from device", name)
                    return
                elif outputLine[:-5] != "CONT\n":
                    return

                    



# TODO
# build function to write data over serial or WS connection
# wait for confirmation on client side


# Forward web socket server
class forward_server(WebSocket):
    global forward_clients

    def handle(self):
        forward_queues[self].append(self.data)

    def connected(self):
        log("Forwarding web socket opened", self.address[0])
        forward_queues[self] = []
        forward_threads[self] = threading.Thread(
            target=bluetooth_server, args=(None, serial_mode.WEBSOCKET, self))
        forward_threads[self].start()

    def handle_close(self):
        log("Forwarding web socket closed", self.address[0])
        del forward_queues[self]
        del forward_threads[self]


def run_websocket(host, port, server):
    server = WebSocketServer(host, port, server)
    log("Starting web socket server on ws://" + host + ":" + str(port))
    server.serve_forever()
    log("Stopping web socket server on ws://" + host + ":" + str(port))


def quickread(file):
    file = open(file, "r")
    result = file.read()
    file.close()
    return (result)


class main_server(object):
    @cherrypy.expose
    def index(self):
        output = ""


if __name__ == "__main__":

    # Create databases
    if not Path(db_global).is_file():
        cherrypy.log("Creating new global database")
        init_global()
    game = get_game()
    if not Path(db_games.replace("$GAME", game)).is_file():
        cherrypy.log("Creating database for game \"" + game + "\"")
        init_game()
    if not os.path.exists(image_dir):
        cherrypy.log("Creating image directory")
        os.mkdir(image_dir)

    # Start external threads
    svelte_interface.start()
    scheduler.start()
    if bt_enable:
        bt_servers = []
        for i in range(len(bt_ports_outgoing)):
            bt_servers.append(threading.Thread(target=bluetooth_server, args=(
                bt_ports_outgoing[i], serial_mode.OUTGOING), daemon=True))
            bt_servers[i].start()
    # Launch web server
    root_server = Root()
    admin_server = Admin()
    port = default_port
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    cherrypy.config.update({
        "server.socket_port": port,
        "server.socket_host": host
    })
    WebSocketPlugin(cherrypy.engine).subscribe()
    cherrypy.tools.websocket = WebSocketTool()
    cherrypy.quickstart(root_server, "/", config={
        "/favicon.ico": {
            "tools.staticfile.on": True,
            "tools.staticfile.filename": get_absolute_path("favicon.ico")
        },
        "/ServerInterfaceWeb.js": {
            "tools.staticfile.on": True,
            "tools.staticfile.filename": get_absolute_path("ServerInterfaceWeb.js")
        },
        "/admin/ws": {
            "tools.websocket.on": True,
            "tools.websocket.handler_cls": AdminWebSocketHandler
        }
    })
