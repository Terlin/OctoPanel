#!/usr/bin/python
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
import json, httplib
from time import sleep

def GetRESTpost(RESTcmd, RESTpath):
	#conn.request('GET', 'api/state?apikey=955B35D4B44944B3A414539177E9493F')
	jsonObj = []
	RESTstring = []

	RESTstring.append("%s%%apikey=955B35D4B44944B3A414539177E9493F", RESTpath)
	conn = httplib.HTTPConnection('octopi.local', 5000)
	conn.connect()
	conn.request(RESTcmd, RESTstring)
	RC = conn.getresponse()

	if RC.status == 200:
		jsonObj = RC.read()
		return jsonObj
	else:
		print "HTTP Get failed " + (RC.reason)
		return jsonObj


def DisplayPrinterStatus():
	if DEBUG:
        	print('in DisplayPrinterStatus')
	
   	lcd.clear()
	while not(lcd.buttonPressed(lcd.LEFT)):
		DisplayText = []
       		lcd.home()
		StatusJson = GetRESTpost("api/state")
		octostatus = json.loads(StatusJson)

		DisplayText.append("%s %s\n" % (octostatus['state']['stateString'], octostatus['progress']['printTimeLeft']))
		#DisplayText =  "Extr:%.3f Bed:%.3f" % (octostatus['temperatures']['extruder']['current'], octostatus['temperatures']['bed']['current'])
		DisplayText.append("E:199C B:50C")
        	lcd.message(DisplayText)
		sleep(5)

def DisplayCurJob():
	if DEBUG:
        	print('in DisplayCurJob')
	
   	lcd.clear()
	while not(lcd.buttonPressed(lcd.LEFT)):
		DisplayText = []
       		lcd.home()
		StatusJson = GetRESTpost(GET', 'api/job')
		octostatus = json.loads(StatusJson)

		DisplayText.append("%s\n" % (octostatus['job']['name']))
		DisplayText.append("%% complete %.f2 %s" % (octostatus['progress']['completion']))
        	lcd.message(DisplayText)
		sleep(5)

def PauseJob():
	if DEBUG:
        	print('in PauseJob')
	
   	lcd.clear()
	while not(lcd.buttonPressed(lcd.LEFT)):
		DisplayText = []
       		lcd.home()
		StatusJson = GetRESTpost('POST', '/api/control/job')
		octostatus = json.loads(StatusJson)

		DisplayText.append("%s\n" % (octostatus['job']['name']))
		DisplayText.append("%% complete %.f2 %s" % (octostatus['progress']['completion']))
        	lcd.message(DisplayText)
		sleep(5)
