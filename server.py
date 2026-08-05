import threading
import cherrypy
from jinja2 import Environment,FileSystemLoader
from users import USERS
from gui import Gui

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

conf={"/static":{"tools.staticdir.on":True,
                 "tools.staticdir.dir":"static"}}

threading.Thread(target=lambda: cherrypy.quickstart(App(),"/",conf),daemon=True).start()
gui.run()
