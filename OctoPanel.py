#!/usr/bin/python
#
# Created by Alan Aufderheide, February 2013
#
# This provides a menu driven application using the LCD Plates
# from Adafruit Electronics.

import commands
import os, threading
from threading import Timer
from string import split
from time import sleep, strftime, localtime
from xml.dom.minidom import *
from Adafruit_I2C import Adafruit_I2C
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
from ListSelector import ListSelector
import smbus
import json, httplib

configfile = 'OctoPanel.xml'
# set DEBUG=1 for print debug statements
DEBUG = 1
# Backlight off timer in seconds
LCDOFF = 900.0
DISPLAY_ROWS = 2
DISPLAY_COLS = 16

# set busnum param to the correct value for your pi
lcd = Adafruit_CharLCDPlate(busnum = 1)
# in case you add custom logic to lcd to check if it is connected (useful)
#if lcd.connected == 0:
#    quit()

lcd.begin(DISPLAY_COLS, DISPLAY_ROWS)
lcd.backlight(lcd.OFF)
#lcd.blink()

#Define Characters
ArrowChar =  [0b00000,0b01000,0b01100,0b01110,0b01100,0b01000,0b00000]
DegreeChar = [0b01100,0b10010,0b10010,0b01100,0b00000,0b00000,0b00000]
TimeChar =   [0b00000,0b01110,0b10101,0b10111,0b10001,0b01110,0b00000]
IdleChar =   [0b00000,0b11011,0b01110,0b00100,0b01110,0b11011,0b00000]
FailedChar = [0b00000,0b01110,0b10001,0b11011,0b10101,0b01010,0b01110]
JobChar =    [0b00000,0b00001,0b00011,0b10110,0b11100,0b01000,0b00000]
ExtrChar =   [0b11111,0b01110,0b01110,0b01110,0b01110,0b01110,0b00100]
BedChar =    [0b00000,0b11111,0b10001,0b10001,0b10001,0b11111,0b00000]
RunningChar =	[[0b00000,0b00000,0b00000,0b00000,0b00000,0b00000,0b00000],
		[0b11111,0b00000,0b00000,0b00000,0b00000,0b00000,0b00000],
		[0b11111,0b11111,0b00000,0b00000,0b00000,0b00000,0b00000],
		[0b11111,0b11111,0b11111,0b00000,0b00000,0b00000,0b00000],
		[0b11111,0b11111,0b11111,0b11111,0b00000,0b00000,0b00000],
		[0b11111,0b11111,0b11111,0b11111,0b11111,0b00000,0b00000],
		[0b11111,0b11111,0b11111,0b11111,0b11111,0b11111,0b00000],
		[0b11111,0b11111,0b11111,0b11111,0b11111,0b11111,0b11111]]

lcd.createChar(0, ArrowChar)
lcd.createChar(1, DegreeChar)
lcd.createChar(2, TimeChar)
lcd.createChar(3, IdleChar)
lcd.createChar(4, JobChar)
lcd.createChar(5, ExtrChar)
lcd.createChar(6, BedChar)

# Turn off Backlight after 120 sec
def LCDBckLightOff():
	if DEBUG:
		print "LCD backlight off"
	lcd.backlight(lcd.OFF)

t = Timer(LCDOFF, LCDBckLightOff)
t.start()

def ResetLCDTimer():
	if DEBUG:
		print "LCDOFF Timer reset"

	global t
	lcd.backlight(lcd.ON)
	t = Timer(LCDOFF, LCDBckLightOff)
	t.start()

# OctoPrint commands
def OctoProcStatus():
	lcd.message(commands.getoutput("/sbin/ifconfig").split("\n")[1].split()[1][5:])
	if DEBUG:
       		print('start OctoProcStatus')

def OctoRestart():
	if DEBUG:
       		print('start OctoRestart')

def WebcamProcStatus():
	if DEBUG:
       		print('start WebcamProcStatus')

def WebcamRestart():
	if DEBUG:
       		print('start WebcamRestart')

def PrintFile():
	if DEBUG:
       		print('start PrintFile')

def DeleteFile():
	if DEBUG:
       		print('start DeleteFile')


def GetRESTpost(RESTcmd, RESTpath, RestHeader):
	jsonObj = []
	RESTstring = []

	conn = httplib.HTTPConnection('octopi.local', 5000, timeout=30)
	conn.connect()

	RESTstring = "%s?apikey=955B35D4B44944B3A414539177E9493F" % RESTpath

	if RESTcmd == 'PUT':
		conn.request(RESTcmd, RESTstring, RestHeader)
		RC = conn.getresponse()
		print RC.status
		print RC.reason
	else:
		conn.request(RESTcmd, RESTstring)

	print RESTstring
	RC = conn.getresponse()
	print RC.status
	print RC.reason

	if RC.status == 204:
		return "OK"
	elif RC.status == 409:
		return "NoJob"

	if RC.status == 200:
		jsonObj = RC.read()
		conn.close()
		return jsonObj
	elif RC.status == 204:
		lcd.message("No content, RC=204")
		conn.close()
		sleep(1)
		return jsonObj
	elif RC.status == 409 and RESTcmd == "/control/job":
		lcd.message("(No) job running ?")
		lcd.message("Job conflicting, RC=409")
		conn.close()
		sleep(1)
		return 0
	else:
		lcd.message("No content\n")
		lcd.message(RC.reason)
		conn.close()
		sleep(1)
		return 0


def DisplayPrinterStatus():
	if DEBUG:
        	print('in DisplayPrinterStatus')
	
	QueryInt = 0
	i = 0
	global RunningChar
   	lcd.clear()
	while not(lcd.buttonPressed(lcd.LEFT)):
		DisplayText = []
		if QueryInt % 20 == 0:
			#Do a query again
			StatusJson = GetRESTpost('GET', "/api/state", None)

			if StatusJson == 0:
				return

			octostatus = json.loads(StatusJson)

			if octostatus['state']['stateString'] == 'Offline':
				lcd.createChar(2, FailedChar)
				DisplayText =  "Printer        \x02\nOffline"
			else:
   				lcd.clear()
				lcd.createChar(2, RunningChar[i])
				DisplayText = "\x04 %s \x02\n\x05:%3.1f\x01 \x06:%2.1f\x01" % (
					octostatus['state']['stateString'], 
					octostatus['temperatures']['extruder']['current'], 
					octostatus['temperatures']['bed']['current'])
        			lcd.message(DisplayText)
			if i == 7:
				i= 0
			else:
				i += 1
			QueryInt = 0

		# Else wait for keayboard buttuns
		QueryInt += 1
       		lcd.home()
		sleep(0.2)

def DisplayCurJob():
	if DEBUG:
        	print('in DisplayCurJob')
	
	QueryInt = 0
	displayType = 0
   	lcd.clear()

	while not(lcd.buttonPressed(lcd.LEFT)):
		if QueryInt % 50 == 0:
			DisplayText = []
			QueryInt = 0
			lcd.clear()

			StatusJson = GetRESTpost('GET', '/api/state', None)
	
			if StatusJson == 0:
				return
	
			lcd.blink()
			octostatus = json.loads(StatusJson)
			print octostatus['state']['flags']['printing']
			if octostatus['state']['flags']['printing'] == False:
				lcd.message("\x05 No job running")
				sleep(2)
				return
	
			if displayType == 0:
				lcd.createChar(2, TimeChar)
				PercentDone = octostatus['progress']['progress'] * 100
				DisplayText = ("\x04 %d%% Complete\n\x02 %s Left" % (int(PercentDone), 
								octostatus['progress']['printTimeLeft']))
        			lcd.message(DisplayText)
				lcd.home()
				displayType = 1
				QueryInt = 0

			elif displayType == 1:
				DisplayText = ("\x04 %d%% Complete\n\x05 Z = %s" % (int(PercentDone), 
								octostatus['currentZ']))
        			lcd.message(DisplayText)
				lcd.home()
				displayType = 2
				QueryInt = 0
			elif displayType == 2:
				lcd.createChar(2, TimeChar)
				DisplayText = ("\x04 %d%% Complete\n\x02 %s Spent" % (int(PercentDone), 
								octostatus['progress']['printTime']))
        			lcd.message(DisplayText)
				lcd.home()
				displayType = 3
				QueryInt = 0
			elif displayType == 3:
				PercentDone = octostatus['progress']['progress'] * 100
				DisplayText = ("\x04 %d%% Complete\n\x02 %s Spent" % (int(PercentDone), 
								octostatus['progress']['printTime']))
				DisplayText = "\x04 %d%% Complete\n\x05:%3.1f\x01 \x06:%2.1f\x01" % (int(PercentDone),
					octostatus['temperatures']['extruder']['current'], 
					octostatus['temperatures']['bed']['current'])
        			lcd.message(DisplayText)
				lcd.home()
				displayType = 4
				QueryInt = 0
			elif displayType == 4:
				DisplayText = ("\x04 %d%% Complete\n\x05%s > %s" % (int(PercentDone), 
								octostatus['progress']['filepos'],
								octostatus['job']['filesize']))
        			lcd.message(DisplayText)
				lcd.home()
				displayType = 0
				QueryInt = 0
		QueryInt += 1
		sleep(0.2)
	lcd.noBlink()
	

def PauseJob():
	if DEBUG:
        	print('in PauseJob')
	
   	lcd.clear()
	DisplayText = []
       	lcd.home()

	RestHeader = "{\n \"command\": \"pause\" \n}"
	StatusJson = GetRESTpost('POST', '/api/control/job', RestHeader)

	if StatusJson == "OK":
       		lcd.message('Job paused')
	elif StatusJson == "NoJob":
       		lcd.message('No Job running')
		sleep(2)
	else:
       		lcd.message('API Error')
		sleep(2)

def CancelJob():
	if DEBUG:
        	print('in CancelJob')
	
   	lcd.clear()
	DisplayText = []
       	lcd.home()

	RestHeader = "{\n \"command\": \"cancel\" \n}"
	StatusJson = GetRESTpost('POST', '/api/control/job', RestHeader)

	if StatusJson == "OK":
       		lcd.message('Job Canceled')
	elif StatusJson == "NoJob":
       		lcd.message('No Job -Cancel')
		sleep(2)
	else:
       		lcd.message('API Error')
		sleep(2)


def RestartJob():
	if DEBUG:
        	print('in RestartJob')
	
   	lcd.clear()
	DisplayText = []
       	lcd.home()

	RestHeader = "{\n \"command\": \"restart\" \n}"
	StatusJson = GetRESTpost('POST', '/api/control/job', RestHeader)

	if StatusJson == "OK":
       		lcd.message('Job Restarted')
	elif StatusJson == "NoJob":
       		lcd.message('No Job -Restart')
		sleep(2)
	else:
       		lcd.message('API Error')
		sleep(2)

def HomeXY():
	if DEBUG:
        	print('in HomeXY')
	
   	lcd.clear()
	DisplayText = []
       	lcd.home()

	RestHeader = "{\n \"command\": \"home\", \"axes\": [\"x\", \"y\"] \n}"
	StatusJson = GetRESTpost('POST', '/api/printer/printhead', RestHeader)

	if StatusJson == "OK":
       		lcd.message('Job Restarted')
	elif StatusJson == "NoJob":
       		lcd.message('No Job -Restart')
		sleep(2)
	else:
       		lcd.message('API Error')
		sleep(2)


# LCDmenu commands
def DoQuit():
    lcd.clear()
    lcd.message('Are you sure?\nPress Sel for Y')
    while 1:
        if lcd.buttonPressed(lcd.LEFT):
            break
        if lcd.buttonPressed(lcd.SELECT):
            lcd.clear()
            lcd.backlight(lcd.OFF)
            quit()
        sleep(0.5)

def DoShutdown():
    lcd.clear()
    lcd.message('Are you sure?\nPress Sel for Y')
    while 1:
        if lcd.buttonPressed(lcd.LEFT):
            break
        if lcd.buttonPressed(lcd.SELECT):
            lcd.clear()
            lcd.backlight(lcd.OFF)
            commands.getoutput("sudo shutdown -h now")
            quit()
        sleep(0.5)

def DoReboot():
    lcd.clear()
    lcd.message('Are you sure?\nPress Sel for Y')
    while 1:
        if lcd.buttonPressed(lcd.LEFT):
            break
        if lcd.buttonPressed(lcd.SELECT):
            lcd.clear()
            lcd.backlight(lcd.OFF)
            commands.getoutput("sudo reboot")
            quit()
        sleep(0.5)

def LcdOff():
    lcd.backlight(lcd.OFF)

def LcdOn():
    lcd.backlight(lcd.ON)

def ShowDateTime():
    if DEBUG:
        print('in ShowDateTime')
    lcd.clear()
    while not(lcd.buttonPressed(lcd.LEFT)):
        sleep(0.5)
        lcd.home()
        lcd.message(strftime('%a %b %d %Y\n%I:%M:%S %p', localtime()))
    
def ValidateDateDigit(current, curval):
    # do validation/wrapping
    if current == 0: # Mm
        if curval < 1:
            curval = 12
        elif curval > 12:
            curval = 1
    elif current == 1: #Dd
        if curval < 1:
            curval = 31
        elif curval > 31:
            curval = 1
    elif current == 2: #Yy
        if curval < 1950:
            curval = 2050
        elif curval > 2050:
            curval = 1950
    elif current == 3: #Hh
        if curval < 0:
            curval = 23
        elif curval > 23:
            curval = 0
    elif current == 4: #Mm
        if curval < 0:
            curval = 59
        elif curval > 59:
            curval = 0
    elif current == 5: #Ss
        if curval < 0:
            curval = 59
        elif curval > 59:
            curval = 0
    return curval

def SetDateTime():
    if DEBUG:
        print('in SetDateTime')
    # M D Y H:M:S AM/PM
    curtime = localtime()
    month = curtime.tm_mon
    day = curtime.tm_mday
    year = curtime.tm_year
    hour = curtime.tm_hour
    minute = curtime.tm_min
    second = curtime.tm_sec
    ampm = 0
    if hour > 11:
        hour -= 12
        ampm = 1
    curr = [0,0,0,1,1,1]
    curc = [2,5,11,1,4,7]
    curvalues = [month, day, year, hour, minute, second]
    current = 0 # start with month, 0..14

    lcd.clear()
    lcd.message(strftime("%b %d, %Y  \n%I:%M:%S %p  ", curtime))
    lcd.blink()
    lcd.setCursor(curc[current], curr[current])
    sleep(0.5)
    while 1:
        curval = curvalues[current]
        if lcd.buttonPressed(lcd.UP):
            curval += 1
            curvalues[current] = ValidateDateDigit(current, curval)
            curtime = (curvalues[2], curvalues[0], curvalues[1], curvalues[3], curvalues[4], curvalues[5], 0, 0, 0)
            lcd.home()
            lcd.message(strftime("%b %d, %Y  \n%I:%M:%S %p  ", curtime))
            lcd.setCursor(curc[current], curr[current])
        if lcd.buttonPressed(lcd.DOWN):
            curval -= 1
            curvalues[current] = ValidateDateDigit(current, curval)
            curtime = (curvalues[2], curvalues[0], curvalues[1], curvalues[3], curvalues[4], curvalues[5], 0, 0, 0)
            lcd.home()
            lcd.message(strftime("%b %d, %Y  \n%I:%M:%S %p  ", curtime))
            lcd.setCursor(curc[current], curr[current])
        if lcd.buttonPressed(lcd.RIGHT):
            current += 1
            if current > 5:
                current = 5
            lcd.setCursor(curc[current], curr[current])
        if lcd.buttonPressed(lcd.LEFT):
            current -= 1
            if current < 0:
                lcd.noBlink()
                return
            lcd.setCursor(curc[current], curr[current])
        if lcd.buttonPressed(lcd.SELECT):
            # set the date time in the system
            lcd.noBlink()
            os.system(strftime('sudo date --set="%d %b %Y %H:%M:%S"', curtime))
            break
        sleep(0.5)

    lcd.noBlink()

def ShowIPAddress():
    if DEBUG:
        print('in ShowIPAddress')
    lcd.clear()
    lcd.message(commands.getoutput("/sbin/ifconfig").split("\n")[1].split()[1][5:])
    while 1:
        if lcd.buttonPressed(lcd.LEFT):
            break
        sleep(0.5)
    
def CameraDetect():
    if DEBUG:
        print('in CameraDetect')
    
def CameraTakePicture():
    if DEBUG:
        print('in CameraTakePicture')

def CameraTimeLapse():
    if DEBUG:
        print('in CameraTimeLapse')

class CommandToRun:
    def __init__(self, myName, theCommand):
        self.text = myName
        self.commandToRun = theCommand
    def Run(self):
        self.clist = split(commands.getoutput(self.commandToRun), '\n')
        if len(self.clist) > 0:
            lcd.clear()
            lcd.message(self.clist[0])
            for i in range(1, len(self.clist)):
                while 1:
                    if lcd.buttonPressed(lcd.DOWN):
                        break
                    sleep(0.5)
                lcd.clear()
                lcd.message(self.clist[i-1]+'\n'+self.clist[i])          
                sleep(0.5)
        while 1:
            if lcd.buttonPressed(lcd.LEFT):
                break

class Widget:
    def __init__(self, myName, myFunction):
        self.text = myName
        self.function = myFunction
        
class Folder:
    def __init__(self, myName, myParent):
        self.text = myName
        self.items = []
        self.parent = myParent

def HandleSettings(node):
    global lcd
    if node.getAttribute('lcdColor').lower() == 'red':
        lcd.backlight(lcd.RED)
    elif node.getAttribute('lcdColor').lower() == 'green':
        lcd.backlight(lcd.GREEN)
    elif node.getAttribute('lcdColor').lower() == 'blue':
        lcd.backlight(lcd.BLUE)
    elif node.getAttribute('lcdColor').lower() == 'yellow':
        lcd.backlight(lcd.YELLOW)
    elif node.getAttribute('lcdColor').lower() == 'teal':
        lcd.backlight(lcd.TEAL)
    elif node.getAttribute('lcdColor').lower() == 'violet':
        lcd.backlight(lcd.VIOLET)
    elif node.getAttribute('lcdColor').lower() == 'white':
        lcd.backlight(lcd.ON)
    if node.getAttribute('lcdBacklight').lower() == 'on':
        lcd.backlight(lcd.ON)
    elif node.getAttribute('lcdBacklight').lower() == 'off':
        lcd.backlight(lcd.OFF)

def ProcessNode(currentNode, currentItem):
    children = currentNode.childNodes

    for child in children:
        if isinstance(child, xml.dom.minidom.Element):
            if child.tagName == 'settings':
                HandleSettings(child)
            elif child.tagName == 'folder':
                thisFolder = Folder(child.getAttribute('text'), currentItem)
                currentItem.items.append(thisFolder)
                ProcessNode(child, thisFolder)
            elif child.tagName == 'widget':
                thisWidget = Widget(child.getAttribute('text'), child.getAttribute('function'))
                currentItem.items.append(thisWidget)
            elif child.tagName == 'run':
                thisCommand = CommandToRun(child.getAttribute('text'), child.firstChild.data)
                currentItem.items.append(thisCommand)

class Display:
    def __init__(self, folder):
        self.curFolder = folder
        self.curTopItem = 0
        self.curSelectedItem = 0
    def display(self):
        if self.curTopItem > len(self.curFolder.items) - DISPLAY_ROWS:
            self.curTopItem = len(self.curFolder.items) - DISPLAY_ROWS
        if self.curTopItem < 0:
            self.curTopItem = 0
        if DEBUG:
            print('------------------')
        str = ''
        for row in range(self.curTopItem, self.curTopItem+DISPLAY_ROWS):
            if row > self.curTopItem:
                str += '\n'
            if row < len(self.curFolder.items):
                if row == self.curSelectedItem:
                    #####cmd = '-'+self.curFolder.items[row].text
                    cmd = '\x00'+self.curFolder.items[row].text
                    if len(cmd) < 16:
                        for row in range(len(cmd), 16):
                            cmd += ' '
                    if DEBUG:
                        print('|'+cmd+'|')
                    str += cmd
                else:
                    cmd = ' '+self.curFolder.items[row].text
                    if len(cmd) < 16:
                        for row in range(len(cmd), 16):
                            cmd += ' '
                    if DEBUG:
                        print('|'+cmd+'|')
                    str += cmd
        if DEBUG:
            print('------------------')
        lcd.home()
        lcd.message(str)

    def update(self, command):
        if DEBUG:
            print('do',command)
	
	# Set LCD Backlight Timer
	ResetLCDTimer()
        if command == 'u':
            self.up()
        elif command == 'd':
            self.down()
        elif command == 'r':
            self.right()
        elif command == 'l':
            self.left()
        elif command == 's':
            self.select()
    def up(self):
        if self.curSelectedItem == 0:
            return
        elif self.curSelectedItem > self.curTopItem:
            self.curSelectedItem -= 1
        else:
            self.curTopItem -= 1
            self.curSelectedItem -= 1
    def down(self):
        if self.curSelectedItem+1 == len(self.curFolder.items):
            return
        elif self.curSelectedItem < self.curTopItem+DISPLAY_ROWS-1:
            self.curSelectedItem += 1
        else:
            self.curTopItem += 1
            self.curSelectedItem += 1
    def left(self):
        if isinstance(self.curFolder.parent, Folder):
            # find the current in the parent
            itemno = 0
            index = 0
            for item in self.curFolder.parent.items:
                if self.curFolder == item:
                    if DEBUG:
                        print('foundit')
                    index = itemno
                else:
                    itemno += 1
            if index < len(self.curFolder.parent.items):
                self.curFolder = self.curFolder.parent
                self.curTopItem = index
                self.curSelectedItem = index
            else:
                self.curFolder = self.curFolder.parent
                self.curTopItem = 0
                self.curSelectedItem = 0
    def right(self):
        if isinstance(self.curFolder.items[self.curSelectedItem], Folder):
            self.curFolder = self.curFolder.items[self.curSelectedItem]
            self.curTopItem = 0
            self.curSelectedItem = 0
        elif isinstance(self.curFolder.items[self.curSelectedItem], Widget):
            if DEBUG:
                print('eval', self.curFolder.items[self.curSelectedItem].function)
            eval(self.curFolder.items[self.curSelectedItem].function+'()')
        elif isinstance(self.curFolder.items[self.curSelectedItem], CommandToRun):
            self.curFolder.items[self.curSelectedItem].Run()

    def select(self):
        if DEBUG:
            print('check widget')
        if isinstance(self.curFolder.items[self.curSelectedItem], Widget):
            if DEBUG:
                print('eval', self.curFolder.items[self.curSelectedItem].function)
            eval(self.curFolder.items[self.curSelectedItem].function+'()')

# now start things up
uiItems = Folder('root','')

dom = parse(configfile) # parse an XML file by name

top = dom.documentElement

ProcessNode(top, uiItems)

display = Display(uiItems)
display.display()

if DEBUG:
	print('start while')

while 1:
	if (lcd.buttonPressed(lcd.LEFT)):
		display.update('l')
		display.display()
		sleep(0.5)

	if (lcd.buttonPressed(lcd.UP)):
		display.update('u')
		display.display()
		sleep(0.5)

	if (lcd.buttonPressed(lcd.DOWN)):
		display.update('d')
		display.display()
		sleep(0.5)

	if (lcd.buttonPressed(lcd.RIGHT)):
		display.update('r')
		display.display()
		sleep(0.5)

	if (lcd.buttonPressed(lcd.SELECT)):
		display.update('s')
		display.display()
		sleep(0.5)
	sleep(0.1)

