import http.server as http
from os.path import isfile
from kld7.kld7 import KLD7
import threading
import time

from collections import deque
# Configuration
server = None
HOST_NAME = ""
SERVER_PORT = 8080

class HttpRequestHandler(http.SimpleHTTPRequestHandler):
    """
    A custom handler to process HTTP requests.
    Inherits from BaseHTTPRequestHandler to override standard methods.
    """
    _radar = None
    _routes = {}

    def addRoute(self, path, handler):
        self._routes[path] = handler
    
    def do_GET(self):
        # whatta hack. if the request is for a file gotta check
        # without the leading slash. if we have it defer to the
        # super class to serve the file since that's what it does
        # and does all the path translations
        if (isfile(self.path[1:])):
            super().do_GET()
            return
        
        self.send_response(200)
        
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        # Note: Content must be encoded to bytes using "utf-8"
        self.wfile.write(bytes("<html>", "utf-8"))

        self.wfile.write(bytes(self.htmlHeader(self.path), "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))

        self.wfile.write(bytes(self.pageHeader(self.path), "utf-8"))
        self.wfile.write(bytes(self.handleGetRequest(self.path), "utf-8"))

        self.wfile.write(bytes("</body>", "utf-8"))
        self.wfile.write(bytes("</html>", "utf-8"))

    def handleGetRequest(self, path):

        # make sure '/' is in the route map
        for r,f in self._routes.items():
            if (path.startswith(r)):
                return f(path)

        return "404"

    def htmlHeader(self, path):
        return f"""\
    <head>
        <link rel='stylesheet' href='/web/styles.css'/>
    </head>
        """

    def pageHeader(self, path):
        return f"""\
    <ul class="top-menu">
        <li class="top-menu-item"><a href="/">Home</a></li>
        <li class="top-menu-item"><a href="/readings">Readings</a></li>
        <li class="top-menu-item"><a href="/stats">Stats</a></li>
        <li class="top-menu-item"><a href="/radarcontrol">Radar Control</a></li>
        <li class="top-menu-item"><a href="/hostcontrol">Host Control</a></li>
    </ul>
    """

def updateRadarParam(path):

    parts = list(filter(lambda x: x!='', path.split('/')))

    r = HttpRequestHandler._radar.setParameter(parts[1], parts[2])
    return radarControlPage(path, {"name": parts[1], "status":r})

def homePage(path):
    return """
    <h2>Home Page</h2>
    """
    
def radarControlPage(path, updated=None):
    params = HttpRequestHandler._radar.getRadarParameters()

    s = '<table class="radar">'
    s = '<table class="radar"><thead><tr><th class="parameter-name">Name</th><th class="parameter-value">Value</th><th class="parameter-updates">Updates</th>'
    for name, p in params.items():
        s += "<tr>"
        s += f"<td>{name}</td>"

        value = ''
        if ('value' in p):
            value = p['value']

        if (updated == None or updated['name'] != name):
            s += f"<td>{value}</td>"
        elif (updated['status']== 0):
            s += f"<td style='font-weight:bold;'>{value}</td>"
        else :
            s += f"<td style='font-style:italic;'>{value}</td>"
            
        if (p['values'] != None):
            s += "<td>"
            for n,v in p['values'].items():
                s += (f"<a href='/update/{name}/{v}'>{n}</a>&nbsp;")
            s += "</td>"
        else:
            s += "<td>Not Settable</td>"
        s += "</tr>"

    s += "</table>"

    return s
    
tdatReadings = deque([],10)
def readingsPage(path):
    global tdatReadings
    
    tdatReadings.append( HttpRequestHandler._radar.getLastTDATReading().copy())

    s = '<table class="radar"><thead><tr><th>Distance</th><th>Speed</th><th>Angle</th><th>Magnitude</th>'
    
    for reading in tdatReadings:
        s += f"""<tr>
        <td>{reading['distance']:0>4}</td>
        <td>{reading['speed']:0>2.2f}</td>
        <td>{reading['angle']:0>2.4f}</td>
        <td>{reading['magnitude']}</td>
        </tr>
        """
    s += '</thead></table>'
    return s

    
def hostControlPage(path):
    return f"""
    <h2>Host Control</h2>
    """
    
def statsPage(path):
    return f"""
    <h2>Stats</h2>
    """

def handleHttpRequests(radar):
    HttpRequestHandler._radar = radar

    # order matters here. keep / at the end; longer matches at the top
    HttpRequestHandler._routes['/hostcontrol'] = hostControlPage
    HttpRequestHandler._routes['/radarcontrol'] = radarControlPage
    HttpRequestHandler._routes['/readings'] = readingsPage
    HttpRequestHandler._routes['/stats'] = statsPage
    HttpRequestHandler._routes['/update'] = updateRadarParam
    HttpRequestHandler._routes['/'] = homePage

    handler = HttpRequestHandler
    server = http.HTTPServer((HOST_NAME, SERVER_PORT), handler)
    
    while True:
        t = threading.Thread(target=server.handle_request)
        t.start()
        t.join()