#!/usr/bin/python

import os, sys, time, subprocess
import re
from os.path import isfile
import logging

from stat import *

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

control_file='.wifiup'
ssid=""

def isWifiConnected():
	output = subprocess.run(["nmcli", "-f", "general.state", "device", "show", "wlan0"], capture_output=True)
	
	m = re.match(r'GENERAL.STATE: +(100 \(connected\))', output.stdout.decode('utf-8'))
	if (m == None):
		return False
	return True

def upAccessPoint():
	logger.info("Attempting to up radar-ap connection")
	# kinda fragile
	output = subprocess.run(["nmcli", "conn", "up", "radar-ap"], capture_output=True)
	logger.info(output.stdout.decode('utf-8'))
	logger.info(output.stderr.decode('utf-8'))

def check():
	# if wifi is not up for 
	if (not isWifiConnected()):
		if (os.path.isfile(control_file)):
			r = os.stat(control_file)
			# bring up radar-ap connection if wifi is down for 10 minutes
			if (time.time() - r.st_ctime) > 600:
				upAccessPoint()
				# restart the clock 
				open(control_file, "w").close()
	else:
		# touch the file if there is wifi connection or access point is active
		open(control_file, "w").close()
	return

if __name__ == "__main__":
	# start the clock
	open(control_file, "w").close()
	while (True):
		check()
		time.sleep(5)
