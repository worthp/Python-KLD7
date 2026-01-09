import http.server as http
from os.path import isfile
import os
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
    
    def log_message(self, format, *args):
        return

    def do_GET(self):
        # let super class to serve the file since that's what it does
        path = self.translate_path(self.path)
        if (os.path.isfile(path)):
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
    <div class="topnav">
        <a href="/">Home</a>
        <a href="/readings">Readings</a>
        <a href="/stats">Stats</a>
        <a href="/radarcontrol">Radar Control</a>
        <a href="/hostcontrol">Host Control</a>
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
    s = f'''<table class="radar"><thead><tr>
    <th class="parameter-name">Name</th>
    <th class="parameter-value">Value</th>
    <th class="parameter-updates">Updates</th>'''

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
    
def readingsPage(path):
    tdatReadings = []
    
    tdatReadings = HttpRequestHandler._radar.getLastTDATReadings()

    duration = int((time.time() * 1000) - HttpRequestHandler._radar._init_time)

    upHours = int(duration/3600000)
    duration %= 3600000
    
    upMinutes = int(duration/60000)
    duration %= 60000
    
    upSeconds = int(duration/1000)

    s = f'''<p>Uptime {upHours:0>2}:{upMinutes:0>2}:{upSeconds:0>2}</p>'''
    s += '<table class="radar"><thead><tr><th>Distance</th><th>Speed</th><th>Angle</th><th>Magnitude</th>'
    
    if (len(tdatReadings) > 0):
        for reading in tdatReadings:
            s += f"""<tr>
            <td>{reading['distance']:0>4}</td>
            <td>{reading['speed']:0>2.2f}</td>
            <td>{reading['angle']:0>2.4f}</td>
            <td>{reading['magnitude']}</td>
            </tr>
            """
    else:
        s += f"""<tr><td colspan='4'>No Readings Available</td></tr>"""

    s += '</thead></table>'
    return s
    
def hostControlPage(path):
    
    with open("/proc/uptime", mode="r") as data:
      ut = int(float(data.read().split(' ')[0]))
            
    d = int(ut/86400)
    h = int((ut%86400)/3600)
    m = int((ut%3600) / 60)
    s = int((ut%60))

    return f"""
    <h2>Host Control</h2>
    <ol>
        <li>Booted at</li>
        <li>Uptime</li>
        <li>Memory Stats</li>
        <li>Disk Stats</li>
        <li>Camera Control(Or just reboot?</li>
    </ol>
    <div>Uptime {d:0>2} days {h:0>2}:{m:0>2}:{s:0>2}</div>
    <div><a href='/hostcontrol/reboot'>Reboot</a></div>
    """
    
def statsPage(path):
    return f"""
    <h2>Stats</h2>
    """
    
def hostRebootPage(path):
    
    print("shutting down")
    command = "/usr/bin/sudo /sbin/shutdownx -h now"
    import subprocess
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print(output)

    return hostControlPage(path)

def handleHttpRequests(radar):
    HttpRequestHandler._radar = radar

    # order matters here. keep / at the end; longer matches at the top
    HttpRequestHandler._routes['/hostcontrol/reboot'] = hostRebootPage
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