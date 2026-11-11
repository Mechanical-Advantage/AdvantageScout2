import json
import sqlite3
import time

from config import config

ACTIVE_THRESHOLD_SEC = 10
ADVANCE_UPLOAD_THRESHOLD = 3
SUPER_ADVANCE_ALLIANCE_THRESHOLD = 2


def update_match_scouts(scouts_dict: dict):
    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    cur = conn.cursor()

    rows = []
    for name, payload in scouts_dict.items():
        if isinstance(payload, dict):
            active = int(payload.get("Active", 1))
            pod = payload.get("PodNumber")
            pod = int(pod) if pod is not None else None
        else:
            active = int(payload)
            pod = None

        if pod is None:
            cur.execute("SELECT PodNumber FROM scouts_match WHERE Scout = ?", (name,))
            existing = cur.fetchone()
            pod = existing[0] if existing and existing[0] is not None else 1

        rows.append((name, active, pod))

    cur.executemany(
        """
        INSERT OR REPLACE INTO scouts_match (Scout, Active, PodNumber)
        VALUES (?, ?, ?)
    """,
        rows,
    )

    cur.execute("DELETE FROM scouts_match WHERE Active = -1")

    conn.commit()
    conn.close()


def get_match_scouts():
    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT Scout, Active, PodNumber FROM scouts_match")
    scouts = {
        row["Scout"]: {"Active": row["Active"], "PodNumber": row["PodNumber"]}
        for row in cur.fetchall()
    }
    conn.close()
    return scouts


def update_super_scouts(scouts_dict: dict):
    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    cur = conn.cursor()

    data_to_insert = list(scouts_dict.items())

    cur.executemany(
        """
        INSERT OR REPLACE INTO scouts_super (Scout, Active)
        VALUES (?, ?)
    """,
        data_to_insert,
    )

    cur.execute("DELETE FROM scouts_super WHERE Active = -1")

    conn.commit()
    conn.close()


def get_super_scouts():
    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT Scout, Active FROM scouts_super")
    scouts = dict(cur.fetchall())
    conn.close()
    return scouts


def locked_match_numbers(existing_rows: dict, current_match: int, has_upload_fn) -> set:
    locked = {m for m in existing_rows if m < current_match}
    if current_match in existing_rows and has_upload_fn(
        current_match, existing_rows[current_match]
    ):
        locked.add(current_match)
    return locked


def match_row_has_any_upload(match_num, row) -> bool:
    teams = [
        row["Blue1"],
        row["Blue2"],
        row["Blue3"],
        row["Red1"],
        row["Red2"],
        row["Red3"],
    ]
    return any(is_match_data_uploaded(match_num, t) for t in teams)


def super_row_has_any_upload(match_num, row) -> bool:
    teams = [row["Blue1"], row["Blue2"], row["Blue3"]]
    if is_super_data_uploaded("Blue", *teams):
        return True
    teams = [row["Red1"], row["Red2"], row["Red3"]]
    return is_super_data_uploaded("Red", *teams)


def create_match_scout_schedule():
    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT Value FROM settings WHERE Key = 'Break Size'")
    row = cur.fetchone()
    break_size = int(row["Value"])

    cur.execute(
        "SELECT Scout, PodNumber FROM scouts_match WHERE Active = 1 ORDER BY PodNumber"
    )
    scouts_data = cur.fetchall()

    pods = {}
    for scout in scouts_data:
        pod_id = scout["PodNumber"]
        name = scout["Scout"]

        if pod_id not in pods:
            pods[pod_id] = []

        pods[pod_id].append(name)

    sorted_pod_ids = sorted(pods.keys())

    if not sorted_pod_ids:
        print("No pods with active scouts found")
        conn.close()
        return

    cur.execute(
        "SELECT * FROM matches WHERE Match NOT IN ('Break Size', 'Key') ORDER BY CAST(Match AS INTEGER)"
    )
    matches = cur.fetchall()

    cur.execute("SELECT * FROM schedule_match")
    existing_rows = {int(r["Match"]): dict(r) for r in cur.fetchall()}
    conn.close()

    current_match = get_current_match_number()
    locked = locked_match_numbers(
        existing_rows, current_match, match_row_has_any_upload
    )

    schedule_data = []

    for i, match in enumerate(matches):
        match_num = int(match["Match"])
        if match_num in locked:
            existing = existing_rows[match_num]
            schedule_data.append(
                (
                    existing["Match"],
                    existing["Blue1"],
                    existing["Blue2"],
                    existing["Blue3"],
                    existing["Red1"],
                    existing["Red2"],
                    existing["Red3"],
                    existing["ScoutBlue1"],
                    existing["ScoutBlue2"],
                    existing["ScoutBlue3"],
                    existing["ScoutRed1"],
                    existing["ScoutRed2"],
                    existing["ScoutRed3"],
                )
            )
            continue

        pod_index = (i // break_size) % len(sorted_pod_ids)
        current_pod_id = sorted_pod_ids[pod_index]
        all_scouts_in_pod = pods[current_pod_id]

        num_scouts = len(all_scouts_in_pod)
        shift = i % num_scouts

        rotated = (all_scouts_in_pod[shift:] + all_scouts_in_pod[:shift]) * 6

        s = rotated[:6]

        schedule_data.append(
            (
                match["Match"],
                match["Blue1"],
                match["Blue2"],
                match["Blue3"],
                match["Red1"],
                match["Red2"],
                match["Red3"],
                s[0],
                s[1],
                s[2],
                s[3],
                s[4],
                s[5],
            )
        )

    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM schedule_match")
    cur.executemany(
        """
        INSERT INTO schedule_match (
            Match, Blue1, Blue2, Blue3, Red1, Red2, Red3,
            ScoutBlue1, ScoutBlue2, ScoutBlue3, ScoutRed1, ScoutRed2, ScoutRed3
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        schedule_data,
    )

    conn.commit()
    conn.close()
    print(
        f"Schedule generated. Used {len(sorted_pod_ids)} pods. {len(locked)} already-reached match(es) left unchanged."
    )


def create_super_scout_schedule():
    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT Scout FROM scouts_super WHERE Active = 1")
    scouts_pool = [row["Scout"] for row in cur.fetchall()]

    if len(scouts_pool) < 2:
        print("Error: Need at least 2 active scouts to assign to both sides.")
        conn.close()
        return

    cur.execute("SELECT * FROM matches ORDER BY CAST(Match AS INTEGER)")
    matches = cur.fetchall()

    cur.execute("SELECT * FROM schedule_super")
    existing_rows = {int(r["Match"]): dict(r) for r in cur.fetchall()}
    conn.close()

    current_match = get_current_match_number()
    locked = locked_match_numbers(
        existing_rows, current_match, super_row_has_any_upload
    )

    schedule_data = []
    scout_index = 0
    num_scouts = len(scouts_pool)

    for match in matches:
        match_num = int(match["Match"])
        if match_num in locked:
            existing = existing_rows[match_num]
            schedule_data.append(
                (
                    existing["Match"],
                    existing["Blue1"],
                    existing["Blue2"],
                    existing["Blue3"],
                    existing["Red1"],
                    existing["Red2"],
                    existing["Red3"],
                    existing["ScoutBlue"],
                    existing["ScoutRed"],
                )
            )
            scout_index += 2
            continue

        blue_scout = scouts_pool[scout_index % num_scouts]
        red_scout = scouts_pool[(scout_index + 1) % num_scouts]

        schedule_data.append(
            (
                match["Match"],
                match["Blue1"],
                match["Blue2"],
                match["Blue3"],
                match["Red1"],
                match["Red2"],
                match["Red3"],
                blue_scout,
                red_scout,
            )
        )

        scout_index += 2

    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM schedule_super")
    cur.executemany(
        """
        INSERT INTO schedule_super (
            Match, Blue1, Blue2, Blue3, Red1, Red2, Red3,
            ScoutBlue, ScoutRed
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        schedule_data,
    )

    conn.commit()
    conn.close()
    print(f"Schedule generated using {num_scouts} scouts in a rotating pool.")


def current_match_schedule():
    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT Value FROM settings WHERE Key = 'Current Match'")
    row = cur.fetchone()
    current_match = int(row["Value"])
    cur.execute("SELECT * FROM schedule_match WHERE Match = ?", (current_match,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def current_super_schedule():
    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT Value FROM settings WHERE Key = 'Current Match'")
    row = cur.fetchone()
    current_match = int(row["Value"])
    cur.execute("SELECT * FROM schedule_super WHERE Match = ?", (current_match,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def is_match_data_uploaded(match, team):
    conn = sqlite3.connect(config.MATCH_DB_PATH)
    cur = conn.cursor()
    cur.execute(
        f"SELECT COUNT(*) FROM {config.MATCH_TABLE} WHERE Match = ? AND Team = ? AND Event = ?",
        (match, team, config.EVENT),
    )
    count = cur.fetchone()[0]
    conn.close()
    return count > 0


def is_super_data_uploaded(alliance, team1, team2, team3):
    conn = sqlite3.connect(config.SUPER_DB_PATH)
    cur = conn.cursor()
    cur.execute(
        f"SELECT COUNT(*) FROM {config.SUPER_TABLE} "
        "WHERE Alliance = ? AND Team1 = ? AND Team2 = ? AND Team3 = ? AND Event = ?",
        (alliance, team1, team2, team3, config.EVENT),
    )
    count = cur.fetchone()[0]
    conn.close()
    return count > 0


def active_scouts(mode, match):
    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT LastHeartbeat FROM devices")
    rows = cur.fetchall()
    conn.close()

    now_ms = time.time() * 1000
    active = set()
    for row in rows:
        raw = row["LastHeartbeat"]
        if not raw:
            continue
        try:
            heartbeat = json.loads(raw)
        except Exception:
            continue
        if heartbeat.get("mode") != mode:
            continue
        if str(heartbeat.get("match")) != str(match):
            continue
        timestamp = heartbeat.get("timestamp")
        if not timestamp or (now_ms - timestamp) > ACTIVE_THRESHOLD_SEC * 1000:
            continue
        scout = heartbeat.get("scout")
        if scout:
            active.add(scout)
    return active


def current_match_schedule_status():
    row = current_match_schedule()
    if row is None:
        return None
    match = row["Match"]
    active = active_scouts("match", match)
    available_scouts = {
        name for name, info in get_match_scouts().items() if info["Active"] == 1
    }
    slots = {}
    for alliance in ("Blue", "Red"):
        for i in (1, 2, 3):
            key = f"{alliance}{i}"
            team = row[key]
            scout = row[f"Scout{key}"]
            slots[key] = {
                "uploaded": is_match_data_uploaded(match, team),
                "active": scout in active,
                "available": (not scout) or (scout in available_scouts),
            }
    return {"Match": match, "slots": slots}


def current_super_schedule_status():
    row = current_super_schedule()
    if row is None:
        return None
    match = row["Match"]
    active = active_scouts("super", match)
    available_scouts = {
        name for name, is_active in get_super_scouts().items() if is_active == 1
    }
    slots = {}
    for alliance in ("Blue", "Red"):
        scout = row[f"Scout{alliance}"]
        teams = [row[f"{alliance}{i}"] for i in (1, 2, 3)]
        slots[alliance] = {
            "uploaded": is_super_data_uploaded(alliance, *teams),
            "active": scout in active,
            "available": (not scout) or (scout in available_scouts),
        }
    return {"Match": match, "slots": slots}


def get_current_match_number():
    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT Value FROM settings WHERE Key = 'Current Match'")
    row = cur.fetchone()
    conn.close()
    return int(row[0]) if row else 1


def set_current_match_number(match_number: int):
    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO settings (Key, Value) VALUES ('Current Match', ?)",
        (str(match_number),),
    )
    conn.commit()
    conn.close()


def match_upload_count(match_number, teams):
    conn = sqlite3.connect(config.MATCH_DB_PATH)
    cur = conn.cursor()
    count = 0
    for team in teams:
        cur.execute(
            f"SELECT COUNT(*) FROM {config.MATCH_TABLE} WHERE Match = ? AND Team = ? AND Event = ?",
            (match_number, team, config.EVENT),
        )
        if cur.fetchone()[0] > 0:
            count += 1
    conn.close()
    return count


def super_upload_count(blue_teams, red_teams):
    count = 0
    if is_super_data_uploaded("Blue", *blue_teams):
        count += 1
    if is_super_data_uploaded("Red", *red_teams):
        count += 1
    return count


def advance_current_match_if_needed():
    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT Match, Blue1, Blue2, Blue3, Red1, Red2, Red3 FROM matches "
        "WHERE Match NOT IN ('Break Size', 'Key') ORDER BY CAST(Match AS INTEGER)"
    )
    matches = cur.fetchall()
    conn.close()

    current_match = get_current_match_number()
    if not matches:
        return {"current_match": current_match, "advanced": False}

    last_ready = None
    for m in matches:
        blue_teams = [m["Blue1"], m["Blue2"], m["Blue3"]]
        red_teams = [m["Red1"], m["Red2"], m["Red3"]]
        teams = blue_teams + red_teams
        match_ready = match_upload_count(m["Match"], teams) >= ADVANCE_UPLOAD_THRESHOLD
        super_ready = (
            super_upload_count(blue_teams, red_teams)
            >= SUPER_ADVANCE_ALLIANCE_THRESHOLD
        )
        if match_ready or super_ready:
            last_ready = m["Match"]

    if last_ready is None:
        return {"current_match": current_match, "advanced": False}

    next_match = int(last_ready) + 1
    if next_match > current_match:
        set_current_match_number(next_match)
        return {"current_match": next_match, "advanced": True}
    return {"current_match": current_match, "advanced": False}


def generate_schedule():
    create_match_scout_schedule()
    create_super_scout_schedule()


def refresh_schedule_from_tba():
    import tba_data

    conn = tba_data.setup_database(config.GLOBAL_DB_PATH)
    try:
        tba_data.fetch_and_store_matches(conn, config.EVENT, tba_data.TBA_API_KEY)
    finally:
        conn.close()

    generate_schedule()


SCOUT_SLOT_KEYS = [
    "ScoutBlue1",
    "ScoutBlue2",
    "ScoutBlue3",
    "ScoutRed1",
    "ScoutRed2",
    "ScoutRed3",
]


def all_matches_upload_status():
    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT Match, Blue1, Blue2, Blue3, Red1, Red2, Red3 FROM matches "
        "WHERE Match NOT IN ('Break Size', 'Key') ORDER BY CAST(Match AS INTEGER)"
    )
    matches = cur.fetchall()

    cur.execute(
        "SELECT Match, ScoutBlue1, ScoutBlue2, ScoutBlue3, ScoutRed1, ScoutRed2, ScoutRed3 FROM schedule_match"
    )
    schedule_rows = {int(r["Match"]): r for r in cur.fetchall()}
    conn.close()

    current_match = get_current_match_number()

    match_conn = sqlite3.connect(config.MATCH_DB_PATH)
    match_conn.row_factory = sqlite3.Row
    match_cur = match_conn.cursor()

    result = []
    for m in matches:
        match_num = int(m["Match"])
        teams = [m["Blue1"], m["Blue2"], m["Blue3"], m["Red1"], m["Red2"], m["Red3"]]
        sched = schedule_rows.get(match_num)

        uploaded = []
        scouts = []
        for i, team in enumerate(teams):
            match_cur.execute(
                f"SELECT Scout FROM {config.MATCH_TABLE} WHERE Match = ? AND Team = ? AND Event = ? "
                "ORDER BY rowid DESC LIMIT 1",
                (match_num, team, config.EVENT),
            )
            row = match_cur.fetchone()
            if row is not None:
                uploaded.append(True)
                scouts.append(row["Scout"])
            else:
                uploaded.append(False)
                scouts.append(sched[SCOUT_SLOT_KEYS[i]] if sched is not None else None)

        result.append(
            {
                "match": match_num,
                "teams": [int(t) for t in teams],
                "uploaded": uploaded,
                "scouts": scouts,
            }
        )
    match_conn.close()
    return {"current_match": current_match, "matches": result}


def all_super_matches_upload_status():
    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT Match, Blue1, Blue2, Blue3, Red1, Red2, Red3 FROM matches "
        "WHERE Match NOT IN ('Break Size', 'Key') ORDER BY CAST(Match AS INTEGER)"
    )
    matches = cur.fetchall()

    cur.execute("SELECT Match, ScoutBlue, ScoutRed FROM schedule_super")
    schedule_rows = {int(r["Match"]): r for r in cur.fetchall()}
    conn.close()

    current_match = get_current_match_number()

    super_conn = sqlite3.connect(config.SUPER_DB_PATH)
    super_conn.row_factory = sqlite3.Row
    super_cur = super_conn.cursor()

    result = []
    for m in matches:
        match_num = int(m["Match"])
        sched = schedule_rows.get(match_num)

        alliances = []
        teams = []
        uploaded = []
        scouts = []
        for alliance, scout_key in (("Blue", "ScoutBlue"), ("Red", "ScoutRed")):
            alliance_teams = [
                int(m[f"{alliance}1"]),
                int(m[f"{alliance}2"]),
                int(m[f"{alliance}3"]),
            ]
            super_cur.execute(
                f"SELECT Scout FROM {config.SUPER_TABLE} "
                "WHERE Alliance = ? AND Team1 = ? AND Team2 = ? AND Team3 = ? AND Event = ? "
                "ORDER BY rowid DESC LIMIT 1",
                (alliance, *alliance_teams, config.EVENT),
            )
            row = super_cur.fetchone()
            alliances.append(alliance)
            teams.append(alliance_teams)
            if row is not None:
                uploaded.append(True)
                scouts.append(row["Scout"])
            else:
                uploaded.append(False)
                scouts.append(sched[scout_key] if sched is not None else None)

        result.append(
            {
                "match": match_num,
                "alliances": alliances,
                "teams": teams,
                "uploaded": uploaded,
                "scouts": scouts,
            }
        )
    super_conn.close()
    return {"current_match": current_match, "matches": result}


if __name__ == "__main__":
    create_match_scout_schedule()
