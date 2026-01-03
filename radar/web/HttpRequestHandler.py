import http.server as http
from kld7.kld7 import KLD7
import threading
import time

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
        
        # 1. Send the HTTP Status Code (200 = OK)
        self.send_response(200)
        
        # 2. Define the Content Type (HTML)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        # 3. Write the HTML content to the page
        # Note: Content must be encoded to bytes using "utf-8"
        self.wfile.write(bytes("<html><head><title>Python Server</title></head>", "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        self.wfile.write(bytes("<h1>Request Received!</h1>", "utf-8"))
        self.wfile.write(bytes(f"<p>You accessed path: {self.path}</p>", "utf-8"))
        self.wfile.write(bytes(f"<p>dynamic data is : {self.handleGetRequest(self.path)}</p>", "utf-8"))
        self.wfile.write(bytes("</body></html>", "utf-8"))

    def handleGetRequest(self, path):

        if (path in self._routes):
            return self._routes[path]()

        parts = path.split('/')
        if ('/'+parts[1] in self._routes):
            return self._routes['/'+parts[1]](parts[2:])
        
        return "404"

def updateParam(parts):

    r = HttpRequestHandler._radar.setParameter(parts[0], parts[1])
    if (r == 0):
        return f'set [{parts[0]}] to [{parts[1]}]]'
    else:
        return f'error[{r}] trying to set [{parts[0]}] to [{parts[1]}]]'


def handleHttpRequests(radar):
    HttpRequestHandler._radar = radar

    HttpRequestHandler._routes['/update'] = updateParam
    HttpRequestHandler._routes['/radar/version'] = radar.version

    handler = HttpRequestHandler
    server = http.HTTPServer((HOST_NAME, SERVER_PORT), handler)
    
    while True:
        t = threading.Thread(target=server.handle_request)
        t.start()
        t.join()