import threading
import json
import hashlib
import os
import subprocess
import time
from pathlib import Path

import cherrypy

from util import *


class SvelteInterface:
    """Automatically builds the app and admin page as necessary."""

    _app_data = None
    _admin_data = None

    def __init__(self, get_game):
        """
        Creates a new SvelteInterface.

        Parameters:
            get_game: A function that returns the name of the current game.
        """

        self._get_game = get_game

    def get_app(self):
        """Returns a dictionary with the app bundle data."""
        return self._app_data

    def get_admin(self):
        """Returns a dictionary with the admin bundle data."""
        return self._admin_data

    def _build(self, is_app, game=""):
        if is_app:
            node = subprocess.Popen(["npm", "run", "build-app", "--", game],
                                    cwd=get_absolute_path("svelte"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            node = subprocess.Popen(["npm", "run", "build-admin"],
                                    cwd=get_absolute_path("svelte"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        code = node.wait()
        if code == 0:
            cherrypy.log(
                ("App" if is_app else "Admin") + " build succeeded")
        else:
            cherrypy.log(
                "WARNING: " + ("App" if is_app else "Admin") + " build failed")

        if is_app:
            app_data_tmp = {
                "config": json.load(open(get_absolute_path("games", game + ".json"), "r")),
                "css": open(get_absolute_path("svelte", "build", "app.css"), "r").read(),
                "js": open(get_absolute_path("svelte", "build", "app.js"), "r").read()
            }
            app_data_hash = hashlib.md5(json.dumps(
                app_data_tmp).encode("UTF-8")).hexdigest()
            app_data_tmp["hash"] = app_data_hash
            self._app_data = app_data_tmp
        else:
            self._admin_data = {
                "css": open(get_absolute_path("svelte", "build", "admin.css"), "r").read(),
                "js": open(get_absolute_path("svelte", "build", "admin.js"), "r").read()
            }

    def _build_thread(self, is_app):
        # Get the list of folders to monitor
        if is_app:
            monitor_folders = [get_absolute_path(
                "games"), get_absolute_path("svelte", "src", "app")]
        else:
            monitor_folders = [get_absolute_path("svelte", "src", "admin")]

        last_modified_cache = {}
        last_game = None
        first_cycle = True
        while True:
            # Wait for file changes
            has_changed = False
            while not has_changed:
                game = self._get_game()
                if last_game != game:
                    last_game = game
                    has_changed = True

                current_files = []
                for folder in monitor_folders:
                    current_files = current_files + \
                        [str(x) for x in Path(folder).rglob("*.*")]

                for x in current_files:
                    if x not in last_modified_cache or last_modified_cache[x] != os.stat(x).st_mtime:
                        has_changed = True
                        last_modified_cache[x] = os.stat(x).st_mtime
                for x in last_modified_cache.keys():
                    if x not in current_files:
                        has_changed = True
                        del last_modified_cache[x]

                if not has_changed:
                    time.sleep(1)

            # Build the app
            if has_changed and not first_cycle:
                if is_app:
                    self._build(True, last_game)
                else:
                    self._build(False)
            first_cycle = False

    def start(self):
        # Check for "node_modules"
        if not os.path.isdir(get_absolute_path("svelte", "node_modules")):
            launch_allowed = True
            response = input("Install Node modules for Svelte? (y-n) ")
            if response == "y" or response == "yes":
                node = subprocess.Popen(["npm", "install"],
                                        cwd=get_absolute_path("svelte"))
                code = node.wait()
                if code == 0:
                    print("Successfully installed Node modules.\n")
                else:
                    print("Failed to install Node modules.\n")
                    launch_allowed = False
            else:
                print(
                    "App and admin builds will be skipped (expect things to be broken).\n")
                launch_allowed = False

            time.sleep(2)
            if not launch_allowed:
                return

        # Build initial version
        self._build(True, self._get_game())
        self._build(False)

        # Start threads
        threading.Thread(target=self._build_thread,
                         daemon=True, args=(True,)).start()
        threading.Thread(target=self._build_thread,
                         daemon=True, args=(False,)).start()


if __name__ == "__main__":
    svelte_interface = SvelteInterface(lambda: "2022")
    svelte_interface.start()
    while True:
        time.sleep(1)
