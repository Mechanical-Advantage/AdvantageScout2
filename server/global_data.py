import json
import sqlite3
import time

from config import config

def get_devices_info():
    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM devices")
        rows = cur.fetchall()

        devices = []
        for row in rows:
            device_dict = dict(row)
            if device_dict.get("LastHeartbeat"):
                try:
                    device_dict["LastHeartbeat"] = json.loads(
                        device_dict["LastHeartbeat"]
                    )
                except Exception:
                    pass

            if device_dict.get("MessageQueue"):
                try:
                    device_dict["MessageQueue"] = json.loads(
                        device_dict["MessageQueue"]
                    )
                except Exception:
                    device_dict["MessageQueue"] = []

            devices.append(device_dict)

        return devices

    except Exception as e:
        print(f"Error getting devices: {e}")
        return []
    finally:
        conn.close()


def remove_device(device_name: str):
    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    print(device_name)
    try:
        cur.execute("DELETE FROM devices WHERE Name = ?", (device_name,))
        conn.commit()
    except Exception as e:
        print(f"Error removing device: {e}")
    finally:
        conn.close()


def get_messages_for_device(device_name: str):
    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("SELECT MessageQueue FROM devices WHERE Name = ?", (device_name,))
    row = cur.fetchone()
    conn.close()

    if not row or not row["MessageQueue"]:
        return []

    try:
        all_messages = json.loads(row["MessageQueue"])
        current_ms = int(time.time() * 1000)
        expiry_ms = config.MESSAGE_EXPIRY_TIME_SEC * 1000
        
        valid_messages = [
            message for message in all_messages 
            if (current_ms - message.get("timestamp", 0)) < expiry_ms
        ]
        return valid_messages
    except Exception:
        return []


def add_messages(messages):
    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    current_ms = int(time.time() * 1000)

    grouped_data = {}
    for message in messages:
        device_name = message.pop("device", None)
        if not device_name:
            continue

        message["timestamp"] = current_ms

        if device_name not in grouped_data:
            grouped_data[device_name] = []

        grouped_data[device_name].append(message)

    try:
        for device_name, new_items in grouped_data.items():
            cur.execute(
                "SELECT MessageQueue FROM devices WHERE Name = ?", (device_name,)
            )
            row = cur.fetchone()

            if row:
                try:
                    current_queue = (
                        json.loads(row["MessageQueue"]) if row["MessageQueue"] else []
                    )
                except Exception:
                    current_queue = []

                current_queue.extend(new_items)

                cur.execute(
                    "UPDATE devices SET MessageQueue = ? WHERE Name = ?",
                    (json.dumps(current_queue), device_name),
                )

        conn.commit()
        return True

    except Exception as e:
        print(f"Error adding messages: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_settings():
    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT Key, Value FROM settings")
    settings = dict(cur.fetchall())
    conn.close()
    return settings

def ensure_default_settings():
    try:
        conn = sqlite3.connect(config.GLOBAL_DB_PATH)
        cur = conn.cursor()
        cur.executemany(
            "INSERT OR IGNORE INTO settings (Key, Value) VALUES (?, ?)",
            [("Field Orientation", 1)],
        )

        cur.execute(
            "UPDATE settings SET Value = 1 WHERE Key = 'Field Orientation' AND Value = 'Red Left'"
        )
        cur.execute(
            "UPDATE settings SET Value = 0 WHERE Key = 'Field Orientation' AND Value = 'Blue Left'"
        )

        conn.commit()
        conn.close()
    except sqlite3.OperationalError:
        pass

def set_settings(settings: dict):
    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    cur = conn.cursor()

    data_to_update = list(settings.items())
    
    cur.executemany("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", data_to_update)

    conn.commit()
    conn.close()

    config.update_config()
