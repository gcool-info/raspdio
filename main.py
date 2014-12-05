# Imports
import gspread
from time import sleep
from threading import Timer
import os
import sys
import subprocess
import datetime
from datetime import timedelta
import urllib2
import RPi.GPIO as GPIO

############################################ Definitions ##############################################  
streamURL = "http://2QMTL0.akacast.akamaistream.net/7/953/177387/v1/rc.akacast.akamaistream.net/2QMTL0"
gDocURL = "1iO9__C7b31zWULhzjJbyP4z-LmNbKU_2CnkXlfL1QnA"
gDocLogin = "george.koulouris1@gmail.com"
gDocPSW = "CoolOuris=+"
volDiff = 20 			# The difference in volume between sleep & wake

######################################### Global Variables ############################################## 
connectionAttempts = 0
isPlaying = False
currVol = 0
durarion = 30 
wakeTime = 0
sleepTime = 0

######################################### Pin Defimitions ############################################## 

# GPIO Pins for the button
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.OUT)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.output(4, GPIO.LOW)

# Pins for ADC using the SPI port
SPICLK = 18
SPIMISO = 23
SPIMOSI = 24
SPICS = 25

# set up the SPI interface pins
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)

# Potentiometer connected to adc #7
potentiometer_adc = 7;

############################################ Functions ############################################## 

# Connection to Gdocs
def gConnect():
	
	global gDocLogin, gDocPSW, wakeTime, sleepTime, duration	

	# Login with your Google account
	gc = gspread.Client(auth=(gDocLogin, gDocPSW))
	
	while True:	
		try:
			# Login & Connect to the spreadsheet
			gc.login()
			sht = gc.open_by_key(gDocURL)
			worksheet = sht.get_worksheet(0)
			
			# Get the values from the cells
			duration = int(worksheet.acell('B5').value)
			wakeHour = int(worksheet.acell('B2').value)
			wakeMin = int(worksheet.acell('C2').value)
			sleepHour = int(worksheet.acell('B3').value)
			sleepMin = int(worksheet.acell('C3').value)

			# Combine the data to construct the wake & sleep times / + timedelta(minutes=duration)			
			wakeTime = datetime.datetime(year=2014, month=11, day=15, hour=wakeHour, minute=wakeMin, second=0, microsecond=0)
			sleepTime = datetime.datetime(year=2014, month=11, day=15, hour=sleepHour, minute=sleepMin, second=0, microsecond=0)

			# Reset connection attempts counter
			connectionAttempts = 0
	
			break
		except:
			print "Could not connect to GDocs.  Retrying..."

			# Update the connection attempts variable
			connectionAttempts = connectionAttempts + 1

			# If too many failures, reboot
			if connectionAttempts > 10:
				os.system("sudo reboot")

			# Reset in 10s
			sleep(10)


# Start playing music
def startMusic(volume):
	
	global isPlaying

	# Set-up the volume	
	os.system("sudo mpc volume " + volume)
	
	# Start Playing
	os.system("sudo mpc play 1")
	isPlaying = True
	
	# Light-up the button
	GPIO.output(4, GPIO.HIGH)

# Stop playing music
def stopMusic():
	
	global isPlaying
	
	os.system("sudo mpc pause")
	isPlaying = False
	
	# Switch-off the button
	GPIO.output(4, GPIO.LOW)

# Button Press interrupt
def buttonPress(pin):
	global isPlaying, currVol

	if not isPlaying:
            	startMusic(str(currVol))		
        else:
            	stopMusic()


# Check the poetentiometer and set the volume if change
def checkVolume():
	
	global currVol

        # read the analog pin from the ADC
        trim_pot = readadc(potentiometer_adc, SPICLK, SPIMOSI, SPIMISO, SPICS)

	# Define a tolerence to avoid jitters - say +-5% of previous value
	tolerence = 5

	# Convert it to a percentage value
	newVol = trim_pot / 10.24

	if (abs(currVol - newVol) > tolerence):
		# Set the volume on the MPC
		os.system("sudo mpc volume " + str(newVol))

		# Update the global variable
		currVol = newVol
		print newVol
		

# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7) - From adafruit tutorial
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)

        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)     # bring CS low

        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1

        GPIO.output(cspin, True)
        
        adcout >>= 1       # first bit is 'null' so drop it
        return adcout



######################################### Program Entry Point  ############################################## 

# Set-up audio MPD
os.system("sudo modprobe snd_bcm2835")
os.system("sudo mpc clear")

# Add the stream
os.system("sudo mpc add " + streamURL)

# Add an interrupt fot the button press
GPIO.add_event_detect(17,GPIO.FALLING, callback=buttonPress, bouncetime=100)


#### Main Loop ####
while True:				
	if isPlaying:
		checkVolume()

	#gConnect()

'''
# Check if internet is up
def internet_on():
    try:
	# http://74.125.228.100 is a server for google
        response=urllib2.urlopen('http://74.125.228.100')
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
GPIO.setup(4, GPIO.OUT)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.output(4, GPIO.LOW)

################### Google Docs Section ##############################

def buttonPress(pin):
	global isPlaying

	if not isPlaying:
            	GPIO.output(4, GPIO.HIGH)
		os.system("sudo mpc play 1")
		isPlaying = True		
        else:
            	GPIO.output(4, GPIO.LOW)        
		os.system("sudo mpc pause")
		isPlaying = False
	 
# make sure the audio card is started, as well as MPD
os.system("sudo modprobe snd_bcm2835")
os.system("sudo mpc clear")
os.system("sudo mpc add http://2QMTL0.akacast.akamaistream.net/7/953/177387/v1/rc.akacast.akamaistream.net/2QMTL0")
os.system("sudo mpc volume 90")

isPlaying = False

# Add an interrupt fot the button press
GPIO.add_event_detect(17,GPIO.FALLING, callback=buttonPress, bouncetime=100)

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
			GPIO.output(4, GPIO.HIGH)
			print "Rise & shine!"

	elif currentTime > eveningStart.time() and currentTime < eveningEnd.time():
        	if not isPlaying:
        	       	os.system("sudo mpc play 1")
			isPlaying = True
			GPIO.output(4, GPIO.HIGH)
			print "Nighty nighty...!"

	else:
		if isPlaying:
			os.system("sudo mpc pause")
			#GPIO.output(4, GPIO.LOW)
			isPlaying = False
			print "Check again...!"
'''
