import os
import sqlite3

class AppConfig:
    def __init__(self):
        self.GAME = "2026"
        self.EVENT = "2026cmptx"

        self.TOP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.DATA_DIR = os.path.join(self.TOP_DIR, "data")
        self.SERVER_DIR = os.path.join(self.TOP_DIR, "server")
        self.GAME_DIR = os.path.join(self.TOP_DIR, "games")
        self.WEB_DIR = os.path.join(self.TOP_DIR, "dist")

        self.MATCH_DB_PATH = os.path.join(self.DATA_DIR, f"{self.GAME}Match.db")
        self.SUPER_DB_PATH = os.path.join(self.DATA_DIR, f"{self.GAME}Super.db")
        self.PIT_DB_PATH = os.path.join(self.DATA_DIR, f"{self.GAME}Pit.db")
        self.GLOBAL_DB_PATH = os.path.join(self.DATA_DIR, "global.db")

        self.MATCH_TABLE = "data"
        self.SUPER_TABLE = "data"
        self.PIT_TABLE = "data"

        self.MATCH_JSON_PATH = os.path.join(self.GAME_DIR, self.GAME, "Match.json")
        self.SUPER_JSON_PATH = os.path.join(self.GAME_DIR, self.GAME, "Super.json")
        self.PIT_JSON_PATH = os.path.join(self.GAME_DIR, self.GAME, "Pit.json")

        self.MESSAGE_EXPIRY_TIME_SEC = 120

    def update_config(self):
        try:
            conn = sqlite3.connect(self.GLOBAL_DB_PATH)
            cur = conn.cursor()

            cur.execute("SELECT Key, Value FROM settings")
            data = dict(cur.fetchall())

            self.GAME = data["Game"]
            self.EVENT = data["Event"]

            self.MATCH_DB_PATH = os.path.join(self.DATA_DIR, f"{self.GAME}Match.db")
            self.SUPER_DB_PATH = os.path.join(self.DATA_DIR, f"{self.GAME}Super.db")
            self.PIT_DB_PATH = os.path.join(self.DATA_DIR, f"{self.GAME}Pit.db")

            self.MATCH_JSON_PATH = os.path.join(self.GAME_DIR, self.GAME, "Match.json")
            self.SUPER_JSON_PATH = os.path.join(self.GAME_DIR, self.GAME, "Super.json")
            self.PIT_JSON_PATH = os.path.join(self.GAME_DIR, self.GAME, "Pit.json")
        except Exception:
            pass

config = AppConfig()