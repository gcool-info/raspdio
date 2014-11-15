# this file is run using this command: "sudo python radio.py"
# python must be installed, and you must call the command while
# you are in the same folder as the file

#imports
import gdata.docs.service
from time import sleep
import os
import subprocess
import datetime
from datetime import timedelta

print "Rasdio V0"

# Definitions
# Time interval 
delta = 30

morningStart = datetime.datetime(year=2014, month=11, day=15, hour=8, minute=0, second=0, microsecond=0)
eveningStart = datetime.datetime(year=2014, month=11, day=15, hour=19, minute=0, second=0, microsecond=0)
morningEnd = morningStart + timedelta(minutes=delta)
eveningEnd = eveningStart + timedelta(minutes=delta)
 
# make sure the audio card is started, as well as MPD
os.system("sudo modprobe snd_bcm2835")
#os.system("sudo mpd")
os.system("sudo mpc clear")
os.system("sudo mpc add http://208.53.164.181:80")

isPlaying = False

while True:
	# Get the current time
	currentTime = datetime.datetime.now().time()	

	if currentTime > morningStart.time() and currentTime < morningEnd.time():
		if not isPlaying:
			os.system("sudo mpc volume 100")
			os.system("sudo mpc play 1")
			isPlaying = True
			print "Rise & shine!"

	elif currentTime > eveningStart.time() and currentTime < eveningEnd.time():
        	if not isPlaying:
			os.system("sudo mpc volume 70")
                	os.system("sudo mpc play 1")
			isPlaying = True
			print "Nighty nighty...!"

	else:
		os.system("sudo mpc pause")
		isPlaying = False
		print "sleeping"

	#sleep for a bit
	sleep(10)

print "Rasdio is playing...!"
