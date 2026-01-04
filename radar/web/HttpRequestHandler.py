import http.server as http
from kld7.kld7 import KLD7
import threading
import time

from collections import deque
# Configuration
server = None
HOST_NAME = "localhost"
SERVER_PORT = 8080

class HttpRequestHandler(http.BaseHTTPRequestHandler):
    """
    A custom handler to process HTTP requests.
    Inherits from BaseHTTPRequestHandler to override standard methods.
    """
    _radar = None
    _routes = {}

    def addRoute(self, path, handler):
        self._routes[path] = handler
    
    def do_GET(self):
        
        self.send_response(200)
        
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        # Note: Content must be encoded to bytes using "utf-8"
        self.wfile.write(bytes("<html>", "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))

        self.wfile.write(bytes(self.htmlHeader(self.path), "utf-8"))

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
        <meta http-equiv="refresh" content="3">
        <style>
        table, th, td {{
          border: 1px solid black;
          border-collapse: collapse;
        }}
</style>
    </head>
        """

    def pageHeader(self, path):
        return f"""\
    <div class='pageheader'>
    <a class='headerlink' href='/'>Home</a>
    <a class='headerlink' href='/stats'>Stats</a>
    <a class='headerlink' href='/readings'>Readings</a>
    <a class='headerlink' href='/radarcontrol'>Radar Control</a>
    <a class='headerlink' href='/hostcontrol'>Host Control</a>
    </div>
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

    s = '<table>'
    for name, p in params.items():
        s += "<tr>"
        if (updated == None or updated['name'] != name):
            s += f"<td>{name}<td><td>{p['value']}</td>"
        elif (updated['status']== 0):
            s += f"<td>{name}<td><td style='font-weight:bold;'>{p['value']}</td>"
        else :
            s += f"<td>{name}<td><td style='font-style:italic;'>{p['value']}</td>"
            
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
    
    s = '<table>'
    tdatReadings.append( HttpRequestHandler._radar.getLastTDATReading().copy())
    
    for reading in tdatReadings:
        s += f"""<tr>
        <td>{reading['distance']}</td>
        <td>{reading['speed']}</td>
        <td>{reading['angle']}</td>
        <td>{reading['magnitude']}</td>
        </tr>
        """
    s += '</table>'
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