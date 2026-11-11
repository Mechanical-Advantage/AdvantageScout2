import os
import tbapy
import sqlite3
from dotenv import load_dotenv

from config import config

load_dotenv()

TBA_API_KEY = os.getenv('TBA_API_KEY')

EVENT_KEY = '2026nhalt' 

def setup_database(db_name):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    
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
    conn.commit()
    return conn

def fetch_and_store_matches(conn, event_key, api_key):
    tba = tbapy.TBA(api_key)
    cur = conn.cursor()
    
    print(f"Attempting to fetch qualification matches for: {event_key}...")

    try:
        raw_matches = tba._get(f"event/{event_key}/matches")
    except Exception as e:
        print(f"Error fetching from TBA: {e}")
        return

    if isinstance(raw_matches, dict):
        message = raw_matches.get("Error") or raw_matches.get("Errors") or raw_matches
        print(f"Error fetching from TBA: {message} (is '{event_key}' a valid TBA event key?)")
        return

    if not raw_matches:
        print(f"No matches found for '{event_key}'")
        return

    all_matches = [tbapy.Match(m) for m in raw_matches]
    quals = [m for m in all_matches if m.comp_level == 'qm']

    quals.sort(key=lambda x: x.match_number)

    if not quals:
        print(f"No qualification matches published yet for '{event_key}'")
        return

    inserted_count = 0
    cur.execute("DELETE FROM matches")
    for match in quals:
        match_id = int(match.match_number)
        
        blue_teams = [team.replace('frc', '') for team in match.alliances['blue']['team_keys']]
        red_teams = [team.replace('frc', '') for team in match.alliances['red']['team_keys']]
        
        try:
            cur.execute('''
                INSERT OR REPLACE INTO matches (Match, Blue1, Blue2, Blue3, Red1, Red2, Red3)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                match_id,
                blue_teams[0], blue_teams[1], blue_teams[2],
                red_teams[0], red_teams[1], red_teams[2]
            ))
            inserted_count += 1
            
        except Exception as e:
            print(f"Database error on match {match_id}: {e}")

    conn.commit()
    print(f"Successfully inserted {inserted_count} qualification matches")

if __name__ == "__main__":
    conn = setup_database(config.GLOBAL_DB_PATH)
    
    fetch_and_store_matches(conn, EVENT_KEY, TBA_API_KEY)
    
    conn.close()