import sys
import os
import shutil
import logging
import threading
import time

import http.server as http
from os.path import isfile, isdir

from controller.controller import Controller

# Configuration
server = None
HOST_NAME = ""
SERVER_PORT = 8080

logger = logging.getLogger(__name__)

class HttpInterface:
    def __init__(self):
        self.controller:Controller = None
        self.routes = {}

        # order matters here. keep / at the end; longer matches at the top
        self.routes['/hostcontrol/reboot'] = self.hostRebootPage
        self.routes['/hostcontrol'] = self.hostControlPage
        #self.routes['/radarcontrol/resetradar'] = self.radarReset
        self.routes['/radarcontrol/setspeedthreshold'] = self.setSpeedThreshold
        self.routes['/radarcontrol'] = self.radarControlPage
        self.routes['/readings'] = self.readingsPage
        self.routes['/images/takestill'] = self.takeStill
        self.routes['/images'] = self.imagesPage
        self.routes['/stats'] = self.statsPage
        self.routes['/update'] = self.updateRadarParam
        self.routes['/'] = self.homePage
        
        self.isStopped = False
        return
    
    def __del__(self):
        return

    
    def init(self, controller:Controller):
        self.controller = controller
        return

    def stop(self):
        self.isStopped = True

    def updateRadarParam(self, path):

        parts = list(filter(lambda x: x!='', path.split('/')))

        r = self.controller.setParameter(parts[1], parts[2])
        return self.radarControlPage(path, {"name": parts[1], "status":r})

    def homePage(self, path):
        return """
        <h2>Home Page</h2>
        """

    def imagesPage(self, path, translatedPath):
        s = ""
        (total, used, free) = shutil.disk_usage('.')
        s += f'''<p>Disk Usage: free: <b>{int(free/total*100)}%</b> used: <b>{int(used/1073741824)}G</b></p>'''
        s += "<p><a href='/images/takestill'>Take Still</a></<p>"

        files = []
        with os.scandir(translatedPath) as d:
            for f in d:
                files.append(f.name)

        s += "<table class='radar'>"
        files.sort(reverse=True)
        for fileName in files:
                s += f"""<tr><td><a href='{path}/{fileName}'>{fileName}</a></td></tr>"""
        s += "</table>"
        return s

        
    def radarControlPage(self, path, updated=None):
        params = self.controller.getRadarParameters()
        
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
                    s += f"<a href='/update/{name}/{v}'>{n}</a>&nbsp;"
                s += "</td>"
            else:
                s += "<td>Not Settable</td>"
            s += "</tr>"

        currentThreshold = self.controller.speed_threshold

        s += "<tr>"
        s += f'''<td>speed threshold</td><td>{currentThreshold}</td>'''
        s += '<td>'
        for p in self.controller.speed_buckets:
            s += f'''<a href='/radarcontrol/setspeedthreshold/{p}'>{p}</a>&nbsp;'''
        s += '</td>'

        s+= "</tr>"

        s += "</table>"
        # s += "<p><a href='/radarcontrol/resetradar'>Reset Radar</a></<p>"

        return s

    def takeStill(self, path):
        self.controller.takeStill()
        return self.imagesPage('/images', './images')
        
    def readingsPage(self, path):
        tdatReadings = []
        
        tdatReadings = self.controller.getLastTDATReadings()
        
        # get timing of last tracked reading
        duration = int((time.time() * 1000) - self.controller._lastTrackedReadingTime)

        lastTrackedHours = int(duration/3600000)
        duration %= 3600000

        lastTrackedMinutes = int(duration/60000) 
        duration %= 60000

        lastTrackedSeconds = int(duration/1000)

        # get timing of radar up time
        duration = int((time.time() * 1000) - self.controller.getInitTime())

        upHours = int(duration/3600000)
        duration %= 3600000
        
        upMinutes = int(duration/60000)
        duration %= 60000
        
        upSeconds = int(duration/1000)

        s = f'''<p>Uptime {upHours:0>2}:{upMinutes:0>2}:{upSeconds:0>2}</p>'''
        s += f'''<p>Last Tracked Reading Duration {lastTrackedHours:0>2}:{lastTrackedMinutes:0>2}:{lastTrackedSeconds:0>2}</p>'''
        s += '<table class="radar"><thead><tr><th>Elapsed Time</th><th>Distance (cm)</th><th>Speed(mph)</th><th>Angle(rad)</th><th>Magnitude(dB)</th>'
        
        if (len(tdatReadings) > 0):
            for reading in tdatReadings:
                readTime = reading['millis']

                duration = (time.time()*1000) - readTime
                hours = int(duration/3600000)
                duration %= 3600000
                minutes = int(duration/60000) 
                duration %= 60000
                seconds = int(duration/1000)

                s += f"""<tr>
                <td>{hours:0>2}:{minutes:0>2}:{seconds:0>2}</td>
                <td>{reading['speed']:0>2.2f}</td>
                <td>{reading['distance']:0>4}</td>
                <td>{reading['angle']:0>2.4f}</td>
                <td>{reading['magnitude']}</td>
                </tr>
                """
        else:
            s += f"""<tr><td colspan='5'>No Readings Available</td></tr>"""

        s += '</thead></table>'

        s += '<br/>' + self.statsPage(path)

        return s
        
    def statsPage(self, path):
        stats = self.controller.getStats()

        s = '<br/>'
        s += '<table class="radar"><thead>'
        
        s += f"""
        <tr><th>Total Reads</th><td>{stats[self.controller.read_count]}</td></tr>
        <tr><th>Min/Max Distance(cm)</th><td>{stats[self.controller.min_distance]:0>4}/{stats[self.controller.max_distance]:0>4}</td></tr>
        <tr><th>Min/Max Speed (mph)</th><td>{stats[self.controller.min_speed]:0>2.2f}/{stats[self.controller.max_speed]:0>2.2f}</td></tr>
        <tr><th>Min/Max Angle(rad)</th><td>{stats[self.controller.min_angle]:0>2.4f}/{stats[self.controller.max_angle]:0>2.4f}</td></tr>
        <tr><th>Min/Max Magnitude(dB)</th><td>{stats[self.controller.min_magnitude]}/{stats[self.controller.max_magnitude]}</td></tr>
        """

        s += '</thead></table>'

        ####################
        s += '<br/><table class="radar"><thead><tr><th colspan="13">Trackings by Hour</th></tr></thead>'

        counts = stats[self.controller.hourly_counts]

        amRow = "<tr><th>AM</th>"
        for hour in range(0,12):
            amRow += f"""<td>{hour:0>2}/{counts[hour]}</td>"""
        amRow += "</tr>"

        pmRow = "<tr><th>PM</th>"
        for hour in range(12,24):
            pmRow += f"""<td>{hour:0>2}/{counts[hour]}</td>"""
        pmRow += "</tr>"

        s += amRow + pmRow + '</thead></table>'

        s += '<br/>'
        #############################################
        s += '<table class="radar">'
        s += "<thead><th colspan='12'>Trackings by Speed Bucket</th></thead>"
        s += "<tr>"
        s += "<th>Bucket/Count</th>"
        for speed, count in stats[self.controller.speed_counts].items():
            s += f"""<td>{speed}/{count}</td>"""
        s += "</tr>"

        s += '</table>'
        ###############################################################################################
        s += '<br/><table class="radar"><thead><tr><th colspan="13"> Over 30 by Hour</th></tr></thead>'

        counts = stats[self.controller.hourly_count_gt_30]

        amRow = "<tr><th>AM</th>"
        for hour in range(0,12):
            amRow += f"""<td>{hour:0>2}/{counts[hour]}</td>"""
        amRow += "</tr>"

        pmRow = "<tr><th>PM</th>"
        for hour in range(12,24):
            pmRow += f"""<td>{hour:0>2}/{counts[hour]}</td>"""
        pmRow += "</tr>"

        s += amRow + pmRow + '</thead></table>'

        s += '<br/>'

        return s
        
    def hostControlPage(self, path):
        
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

    def hostRebootPage(self, path):
        
        logger.info("shutting down")
        command = "/usr/bin/sudo /usr/sbin/reboot"
        import subprocess
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        output = process.communicate()[0]
        logger.info(output)

        return self.hostControlPage(path)

    def radarReset(self, path):
        self.controller.resetRadarPower()
        return self.radarControlPage(path)


    def setSpeedThreshold(self, path):

        parts = list(filter(lambda x: x!='', path.split('/')))
        self.controller.setSpeedThreshold(parts[2])

        return self.radarControlPage(path)

    def handleGetRequest(self, path):

        # make sure '/' is in the route map
        for r,f in self.routes.items():
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
        <a href="/images">Images</a>
    </div>
    """

    def go(self):

        handler = HttpRequestHandler
        handler.http_interface = self
        self.server = http.HTTPServer((HOST_NAME, SERVER_PORT), handler)
        self.server.timeout = 1
        
        while (not self.isStopped):
            self.server.handle_request()

        logger.info(f'''web interface was stopped''')


class HttpRequestHandler(http.SimpleHTTPRequestHandler):
    """
    A custom handler to process HTTP requests.
    Inherits from BaseHTTPRequestHandler to override standard methods.
    """

    http_interface:HttpInterface = None

    def log_message(self, format, *args):
        super().log_message(format, *args)
        return

    def do_GET(self):
        # let super class to serve the file since that's what it does
        translated_path = self.translate_path(self.path)

        if (os.path.isfile(translated_path)):
            super().do_GET()
            return
        
        self.send_response(200)
        
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        # Note: Content must be encoded to bytes using "utf-8"
        self.wfile.write(bytes("<!DOCTYPE html>\n<html>", "utf-8"))

        self.wfile.write(bytes(self.http_interface.htmlHeader(self.path), "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))

        self.wfile.write(bytes(self.http_interface.pageHeader(self.path), "utf-8"))
        if (self.path.endswith('/images')):
            section = self.http_interface.imagesPage(self.path, translated_path)
            self.wfile.write(bytes(section, "utf-8"))
        else:
            self.wfile.write(bytes(self.http_interface.handleGetRequest(self.path), "utf-8"))

        self.wfile.write(bytes("</body>", "utf-8"))
        self.wfile.write(bytes("</html>", "utf-8"))
