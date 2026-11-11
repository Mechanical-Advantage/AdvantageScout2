import os
import sqlite3
from config import config

def init_global():
    try:
        os.remove(config.GLOBAL_DB_PATH)
    except Exception:
        pass
    conn = sqlite3.connect(config.GLOBAL_DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS devices (
        Name TEXT PRIMARY KEY,
        LastHeartbeat JSONB,
        MessageQueue JSONB
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS scouts_match (
        Scout TEXT PRIMARY KEY,
        Active INTEGER,
        PodNumber INTEGER
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS scouts_super (
        Scout TEXT PRIMARY KEY,
        Active INTEGER
    )""")
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            Match INTEGER PRIMARY KEY,
            Blue1 TEXT,
            Blue2 TEXT,
            Blue3 TEXT,
            Red1 TEXT,
            Red2 TEXT,
            Red3 TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS schedule_match (
            Match INTEGER PRIMARY KEY,
            Blue1 TEXT,
            Blue2 TEXT,
            Blue3 TEXT,
            Red1 TEXT,
            Red2 TEXT,
            Red3 TEXT,
            ScoutBlue1 TEXT,
            ScoutBlue2 TEXT,
            ScoutBlue3 TEXT,
            ScoutRed1 TEXT,
            ScoutRed2 TEXT,
            ScoutRed3 TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS schedule_super (
            Match INTEGER PRIMARY KEY,
            Blue1 TEXT,
            Blue2 TEXT,
            Blue3 TEXT,
            Red1 TEXT,
            Red2 TEXT,
            Red3 TEXT,
            ScoutBlue TEXT,
            ScoutRed TEXT
        )
    ''')

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        Key TEXT PRIMARY KEY,
        Value
    )""")

    settings = {
        "Game": "2026",
        "Event": "2026cmptx",
        "Break Size": 1,
        "Current Match": 1,
        # Which alliance's starting wall is physically on the left side of
        # the field as scouts/the scoring table see it: 0 = Blue Left/Red
        # Right, 1 = Red Left/Blue Right. Determines how PreMatchTab.svelte
        # mirrors the starting-position diagram.
        "Field Orientation": 1
    }

    cur.executemany(
        "INSERT OR IGNORE INTO settings (Key, Value) VALUES (?, ?)",
        list(settings.items())
    )
    conn.commit()
    conn.close()
    print("Initialized global!")


if __name__ == "__main__":
    init_global()