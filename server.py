import hashlib
import json
import os
import subprocess
import threading
import time

import cherrypy

GAME = "2022"
PORT = 8000

app_data = None


def get_absolute_path(*path):
    """Returns the absolute path based on a path relative to this folder."""
    joined_path = os.path.dirname(__file__)
    for item in path:
        joined_path = os.path.join(joined_path, item)
    return os.path.abspath(joined_path)


class Root(object):

    @cherrypy.expose
    def index(self):
        index_html = ""
        with open(get_absolute_path("index.html"), "r") as index_file:
            index_html = index_file.read()
        return index_html.replace("ISWEB", "true")

    @cherrypy.expose
    def request(self, query, data="{}"):
        data = json.loads(data)
        if query == "download_app":
            changed = False
            app_data_response = None
            if "hash" not in data or data["hash"] != app_data["hash"]:
                changed = True
                app_data_response = app_data
            return json.dumps({
                "changed": changed,
                "data": app_data_response
            }, separators=(",", ":"))

        return "{}"


def app_build_thread():
    global app_data
    while True:
        cherrypy.log("Building the app...")
        node = subprocess.Popen(["npm", "run", "build", "--", GAME],
                                cwd=get_absolute_path("app"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        code = node.wait()
        if code == 0:
            cherrypy.log("App build succeeded")
        else:
            cherrypy.log("WARNING: App build failed")

        app_data_tmp = {
            "config": json.load(open(get_absolute_path("games", GAME + ".json"), "r")),
            "css": open(get_absolute_path("app", "build", "bundle.css"), "r").read(),
            "js": open(get_absolute_path("app", "build", "bundle.js"), "r").read()
        }
        app_data_hash = hashlib.sha1(json.dumps(
            app_data_tmp).encode("UTF-8")).hexdigest()
        app_data_tmp["hash"] = app_data_hash
        app_data = app_data_tmp

        time.sleep(30)


if __name__ == "__main__":
    threading.Thread(target=app_build_thread, daemon=True).start()

    while app_data == None:
        time.sleep(0.1)

    cherrypy.config.update({
        "server.socket_port": PORT,
        "server.socket_host": "0.0.0.0"
    })
    cherrypy.quickstart(Root(), "/", config={
        "/ServerInterfaceWeb.js": {
            "tools.staticfile.on": True,
            "tools.staticfile.filename": get_absolute_path("ServerInterfaceWeb.js")
        }
    })
