#imports
import gspread
from time import sleep
import os
import sys
import subprocess
import datetime
from datetime import timedelta
import urllib2
import RPi.GPIO as GPIO

# Check if internet is up
def internet_on():
    try:
	# http://74.125.228.100 is a server for google
        response=urllib2.urlopen('http://74.125.228.100',timeout=1)
        return True
    except urllib2.URLError as err: pass
    return False

while not internet_on():
	sleep(60)	

print "Wifi is on"

# Set global variables
delta = 30
wakeHour = 8
wakeMin = 0
sleepHour = 23
sleepMin = 0
morningStart = datetime.datetime(year=2014, month=11, day=15, hour=8, minute=0, second=0, microsecond=0)
eveningStart = datetime.datetime(year=2014, month=11, day=15, hour=17, minute=50, second=0, microsecond=0)
morningEnd = morningStart + timedelta(minutes=delta)
eveningEnd = eveningStart + timedelta(minutes=delta)

# GPIO Pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.output(18, GPIO.LOW)

################### Google Docs Section ##############################

def connectToDocs(): # Connect to docs & get values
	print "Connecting to Google Docs"
	
	# Login with your Google account
	gc = gspread.Client(auth=('', ''))
	
	while True:	
		try:
			gc.login()
			sht = gc.open_by_key('1iO9__C7b31zWULhzjJbyP4z-LmNbKU_2CnkXlfL1QnA')
			worksheet = sht.get_worksheet(0)
	
			# Set global variables
			global delta, wakeHour, wakeMin, sleepHour, sleepMin, morningStart, eveningStart, morningEnd, eveningEnd
			delta = int(worksheet.acell('B5').value)
			wakeHour = int(worksheet.acell('B2').value)
			wakeMin = int(worksheet.acell('C2').value)
			sleepHour = int(worksheet.acell('B3').value)
			sleepMin = int(worksheet.acell('C3').value)

			morningStart = datetime.datetime(year=2014, month=11, day=15, hour=wakeHour, minute=wakeMin, second=0, microsecond=0)
			eveningStart = datetime.datetime(year=2014, month=11, day=15, hour=sleepHour, minute=sleepMin, second=0, microsecond=0)
			morningEnd = morningStart + timedelta(minutes=delta)
			eveningEnd = eveningStart + timedelta(minutes=delta)	

			# Print the results
			print "Wake Up -> ",morningStart.time()," - ",morningEnd.time()
			print "Sleep -> ",eveningStart.time()," - ",eveningEnd.time()
			break
		except:
			print "Could not connect to GDocs.  Retrying..."
			sleep(10)
def buttonPress(pin):
	global isPlaying

	if not isPlaying:
            	state = 1
            	GPIO.output(18, GPIO.HIGH)
		os.system("sudo mpc play 1")
		isPlaying = True		
        else:
            	state = 0
            	GPIO.output(18, GPIO.LOW)        
		os.system("sudo mpc pause")
		isPlaying = False
	 
# make sure the audio card is started, as well as MPD
os.system("sudo modprobe snd_bcm2835")
os.system("sudo mpc clear")
os.system("sudo mpc add http://2QMTL0.akacast.akamaistream.net/7/953/177387/v1/rc.akacast.akamaistream.net/2QMTL0")
os.system("sudo mpc volume 90")

isPlaying = False

# Add an interrupt fot the button press
GPIO.add_event_detect(23,GPIO.FALLING, callback=buttonPress, bouncetime=100)

print "############################ Rasdio Playing! ####################"

while True:
	# Get the current time
	currentTime = datetime.datetime.now().time()

	#Get the google doc parameters
	connectToDocs()	
	
	if currentTime > morningStart.time() and currentTime < morningEnd.time():
		if not isPlaying:
			os.system("sudo mpc play 1")
			isPlaying = True
			GPIO.output(18, GPIO.HIGH)
			print "Rise & shine!"

	elif currentTime > eveningStart.time() and currentTime < eveningEnd.time():
        	if not isPlaying:
        	       	os.system("sudo mpc play 1")
			isPlaying = True
			GPIO.output(18, GPIO.HIGH)
			print "Nighty nighty...!"

	else:
		if isPlaying:
			os.system("sudo mpc pause")
			#GPIO.output(18, GPIO.LOW)
			isPlaying = False
		
		print "Check again...!"
