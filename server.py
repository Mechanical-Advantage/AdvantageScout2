import json

import cherrypy

from svelte_interface import SvelteInterface
from util import *

GAME = "2022"
PORT = 8000

svelte_interface = None


class Root(object):

    @cherrypy.expose
    def index(self):
        index_html = ""
        with open(get_absolute_path("app.html"), "r") as index_file:
            index_html = index_file.read()
        return index_html.replace("ISWEB", "true")

    @cherrypy.expose
    def admin(self):
        with open(get_absolute_path("admin.html"), "r") as admin_file:
            return admin_file.read()

    @cherrypy.expose("admin.css")
    def admin_css(self):
        cherrypy.response.headers["Content-Type"] = "text/css"
        return svelte_interface.get_admin()["css"]

    @cherrypy.expose("admin.js")
    def admin_js(self):
        cherrypy.response.headers["Content-Type"] = "text/javascript"
        return svelte_interface.get_admin()["js"]

    @cherrypy.expose
    def request(self, query, data="{}"):
        data = json.loads(data)
        if query == "download_app":
            changed = False
            app_data_response = None
            if "hash" not in data or data["hash"] != svelte_interface.get_app()["hash"]:
                changed = True
                app_data_response = svelte_interface.get_app()
            return json.dumps({
                "changed": changed,
                "data": app_data_response
            }, separators=(",", ":"))

        return "{}"


if __name__ == "__main__":
    svelte_interface = SvelteInterface(lambda: GAME)
    svelte_interface.start()

    cherrypy.config.update({
        "server.socket_port": PORT,
        "server.socket_host": "0.0.0.0"
    })
    cherrypy.quickstart(Root(), "/", config={
        "/favicon.ico": {
            "tools.staticfile.on": True,
            "tools.staticfile.filename": get_absolute_path("favicon.ico")
        },
        "/ServerInterfaceWeb.js": {
            "tools.staticfile.on": True,
            "tools.staticfile.filename": get_absolute_path("ServerInterfaceWeb.js")
        }
    })
