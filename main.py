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
gDocURL = "YOUR_GDOC_KEY"
gDocLogin = "YOUR_GMAIL"
gDocPSW = "YOUR_GMAIL_PASSWORD"
volDiff = 20 			# The difference in volume between sleep & wake

######################################### Global Variables ############################################## 
connectionAttempts = 0		# The number of times we have tried to connect to gDocs & failed
isPlaying = False
currVol = 100			# The current volume (as a percentage)
duration = 30			# The play duration in min
wakeTime = 0			# The wake up time (created by the gDoc)
sleepTime = 0			# The sleep time (created by the gDoc)
gDocsInterrupted = False	# The button interrupted music played at the specified time (from the gDoc)
gDocsPlaying = False		# Music is playing because of the gDoc

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
	
	global gDocLogin, gDocPSW, wakeTime, sleepTime, duration, connectionAttempts	

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


# Function to resume checking gDocs
def resumeGDocs():
	global gDocsInterrupted

	gDocsInterrupted = False



# Stop playing music
def stopMusic():
	
	global isPlaying, startTimer		
	
	os.system("sudo mpc pause")

	# For some reason, invoking "os.system" destroys the interrupt. So I recreate it
	# If you evern find-out why, email me (george.koulouris1@gmail.com) ! I'm curious... 	
	GPIO.remove_event_detect(17)
	GPIO.add_event_detect(17,GPIO.FALLING, callback=buttonPress, bouncetime=100)

	isPlaying = False
	
	# Switch-off the button
	GPIO.output(4, GPIO.LOW)

	# Cancel the start music timer
	startTimer.cancel()


# Start playing music
def startMusic(volume):
	
	global isPlaying, startTimer, duration
	
	# Set-up the volume	
	os.system("sudo mpc volume " + volume)
	
	# Start Playing
	os.system("sudo mpc play 1")
	isPlaying = True

	# For some reason, invoking "os.system" destroys the interrupt. So I recreate it
	# If you evern find-out why, email me (george.koulouris1@gmail.com) ! I'm curious... 	
	GPIO.remove_event_detect(17)
	GPIO.add_event_detect(17,GPIO.FALLING, callback=buttonPress, bouncetime=100)

	
	# Light-up the button
	GPIO.output(4, GPIO.HIGH)

	# Create a start music timer to stop playing music after "duration"
	startTimer = Timer(duration*60, stopMusic)
	startTimer.start()	



# Button Press interrupt
def buttonPress(pin):
	global isPlaying, currVol, gDocsInterrupted, gDocsPlaying, stopTimer

	if not isPlaying:
            	startMusic(str(currVol))
        else:
            	stopMusic()
	
		# if the gDoc requested the play, then  we need to stop it for "duration"
		# we do this by setting up a timer
		if gDocsPlaying:
			gDocsInterrupted = True
			gDocsPlaying = False
			stopTimer = Timer(duration*60, resumeGDocs)
			stopTimer.start()	

	


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
		os.system("mpc volume " + str(int(newVol)))
	
		# For some reason, invoking "os.system" destroys the interrupt. So I recreate it
		# If you evern find-out why, email me (george.koulouris1@gmail.com) ! I'm curious... 	
		GPIO.remove_event_detect(17)
		GPIO.add_event_detect(17,GPIO.FALLING, callback=buttonPress, bouncetime=100)


		currVol = newVol
		

# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7) - From adafruit tutorial
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, GPIO.HIGH)

        GPIO.output(clockpin, GPIO.LOW)  # start clock low
        GPIO.output(cspin, GPIO.LOW)     # bring CS low

        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, GPIO.HIGH)
                else:
                        GPIO.output(mosipin, GPIO.LOW)
                commandout <<= 1
                GPIO.output(clockpin, GPIO.HIGH)
                GPIO.output(clockpin, GPIO.LOW)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
                GPIO.output(clockpin, GPIO.HIGH)
                GPIO.output(clockpin, GPIO.LOW)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1

        GPIO.output(cspin, GPIO.HIGH)
        
        adcout >>= 1       # first bit is 'null' so drop it
        return adcout



######################################### Program Entry Point  ############################################## 

# Set-up audio MPD
os.system("sudo modprobe snd_bcm2835")
os.system("sudo mpc pause")
os.system("sudo mpc clear")

# Add the stream
os.system("sudo mpc add " + streamURL)

# Add an interrupt fot the button press
GPIO.add_event_detect(17,GPIO.FALLING, callback=buttonPress, bouncetime=100)

running = True

#### Main Loop ####
while running:	
	
	try:
		# Get the current time
		currentTime = datetime.datetime.now().time()
			
		if isPlaying:
		
			checkVolume()		
			sleep(0.5)

		elif not gDocsInterrupted:

			# Connect to the gDoc
			gConnect()

			# Set the end times
			sleepEnd = sleepTime + timedelta(minutes=duration)
			wakeEnd = wakeTime +  timedelta(minutes=duration)		

			# Check if we are waking up or sleeping
			if currentTime > wakeTime.time() and currentTime < wakeEnd.time():
			
				# Start the music with the volume for the waking up
				startMusic(str(currVol))
				gDocsPlaying = True	
	
			elif currentTime > sleepTime.time() and currentTime < sleepEnd.time():

				# Start the music with the volume for sleeping

				# Make sure the sleep volume isn't below 0
				if currVol < volDiff:
					sleepVol = 0
				else:
					sleepVol = currVol

				startMusic(str(sleepVol))
				gDocsPlaying = True
				
		
			# Sleep for 5 minutes
			for i in range(60*5):
		
				# If the button is pressed, then exit sleep and go into the "isPlaying" loop
				if isPlaying:
					break
				
				gDocsPlaying = False
				#sleep(1)
		else:
			sleep(1)

	except KeyboardInterrupt:
		running = False


GPIO.cleanup()
