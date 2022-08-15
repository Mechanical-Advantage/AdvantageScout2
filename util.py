import os
import time
import sqlite3 as sql

import config
import math


def int_time():
    """Returns the current epoch time as an integer."""
    return(int(math.floor(time.time())))


def read_text(path):
    "Utility function to read file contents."
    with open(path, "r") as text_file:
        return text_file.read()


def get_game():
    """Returns the name of the selected game."""
    conn_global = sql.connect(config.db_global)
    cur_global = conn_global.cursor()
    cur_global.execute("SELECT value FROM config WHERE key = 'game'")
    game = str(cur_global.fetchall()[0][0])
    conn_global.close()
    return game


def gamedb_connect(force_connect=False):
    """Returns a SQL connection to the current game database."""
    game = get_game()
    if os.path.exists(config.db_games.replace("$GAME", game)) or force_connect:
        conn_game = sql.connect(config.db_games.replace("$GAME", game))
    else:
        conn_game = None
    return conn_game


def get_absolute_path(*path):
    """Returns the absolute path based on a path relative to this folder."""
    joined_path = os.path.dirname(__file__)
    for item in path:
        joined_path = os.path.join(joined_path, item)
    return os.path.abspath(joined_path)
