import threading
import cherrypy
from jinja2 import Environment,FileSystemLoader
from users import USERS
from gui import Gui
import os

from utillc import *

fileDir = os.path.dirname(os.path.abspath(__file__))
localDir = os.path.join(fileDir, '.')


env=Environment(loader=FileSystemLoader("templates"))
gui=Gui(USERS)

class App:
    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("/enter")

    @cherrypy.expose
    def enter(self):
        c=cherrypy.request.cookie.get("user")
        if c:
            return env.get_template("buttons.html").render(user=c.value)
        return env.get_template("login.html").render(users=USERS)

    @cherrypy.expose
    def login(self,user):
        cherrypy.response.cookie["user"]=user
        raise cherrypy.HTTPRedirect("/enter")

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def message(self,value):
        c=cherrypy.request.cookie.get("user")
        if not c:
            return {"ok":False}
        gui.q.put((c.value,value))
        return {"ok":True}

    @cherrypy.expose
    def logout(self):
        cherrypy.response.cookie["user"]=""
        cherrypy.response.cookie["user"]["expires"]=0
        raise cherrypy.HTTPRedirect("/enter")

port = 8080
conf={
	"/static":{"tools.staticdir.on":True,
               "tools.staticdir.dir" : os.path.join(fileDir, "static") },
	'global' : {
		'server.socket_host' : '0.0.0.0', #192.168.1.5', #'127.0.0.1',
		'server.socket_port' : port,
		'server.thread_pool' : 8,
		'log.screen': False,
		'log.error_file': './error.log',
		'log.access_file': './access.log',
		'tools.response_headers.on': True,
		'tools.response_headers.headers': [
			('X-Frame-options', 'deny'),
			('X-XSS-Protection', '1; mode=block'),
			('X-Content-Type-Options', 'nosniff')]
	},
}

threading.Thread(target=lambda: cherrypy.quickstart(App(),"/",conf),daemon=True).start()
gui.run()
