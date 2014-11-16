# this file is run using this command: "sudo python radio.py"
# python must be installed, and you must call the command while
# you are in the same folder as the file

#imports
import gspread
from time import sleep
import os
import subprocess
import datetime
from datetime import timedelta

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


################### Google Docs Section ##############################

def connectToDocs(): # Connect to docs & get values
	print "Connecting to Google Docs"
	
	# Login with your Google account
	gc = gspread.Client(auth=('???@gmail.com', '???'))
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
 
# make sure the audio card is started, as well as MPD
os.system("sudo modprobe snd_bcm2835")
os.system("sudo mpc clear")
os.system("sudo mpc add http://2QMTL0.akacast.akamaistream.net/7/953/177387/v1/rc.akacast.akamaistream.net/2QMTL0")

isPlaying = False

print "############################ Rasdio Playing! ####################"

while True:
	# Get the current time
	currentTime = datetime.datetime.now().time()

	#Get the google doc parameters
	connectToDocs()	
	
	if currentTime > morningStart.time() and currentTime < morningEnd.time():
		if not isPlaying:
			os.system("sudo mpc volume 100")
			os.system("sudo mpc play 1")
			isPlaying = True
			print "Rise & shine!"

	elif currentTime > eveningStart.time() and currentTime < eveningEnd.time():
        	if not isPlaying:
			os.system("sudo mpc volume 80")
                	os.system("sudo mpc play 1")
			isPlaying = True
			print "Nighty nighty...!"

	else:
		os.system("sudo mpc pause")
		isPlaying = False
		print "sleeping"

	#sleep for a bit - 1min
	sleep(60)

print "Rasdio is playing...!"
