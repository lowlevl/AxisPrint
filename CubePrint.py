#!/usr/bin/python

print("\033[1;30;40m[CubePrint]Loading libraries...\033[m"), #Importing all libs
import os
import time
import RPi.GPIO as GPIO
import ConfigParser
import cherrypy
import serial
print("\033[1;32;40mOk\033[m")

class Log:
    def __init__(self):
        self.none = None
    
    def Warning(self, Text, NoOEL = False):
        if NoOEL:
            print('\033[1;33;40m' + Text + '\033[m'),
        else:
            print('\033[1;33;40m' + Text + '\033[m')
        
    def Fail(self, Text, NoOEL = False):
        if NoOEL:
            print('\033[1;31;40m' + Text + '\033[m'),
        else:
            print('\033[1;31;40m' + Text + '\033[m')

    def Critical(self, Text, NoOEL = False):
        if NoOEL:
            print('\033[1;37;41m' + Text + '\033[m'),
        else:
            print('\033[1;37;41m' + Text + '\033[m')

    def Info(self, Text, NoOEL = False):
        if NoOEL:
            print('\033[1;30;40m' + Text + '\033[m'),
        else:
            print('\033[1;30;40m' + Text + '\033[m')     
    
    def Success(self, Text, NoOEL = False):
        if NoOEL:
            print('\033[1;32;40m' + Text + '\033[m'),
        else:
            print('\033[1;32;40m' + Text + '\033[m')
        
Log = Log()

Config = ConfigParser.ConfigParser()
Config.read('config.conf')

#Gpio config
UseGpio = Config.getboolean("Gpio", "Enabled")
GpioPin = int(Config.get("Gpio", "GpioPin"))
PowerOffConnect = Config.getboolean("Gpio", "PowerOffConnect")

if UseGpio:
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(GpioPin, GPIO.OUT, initial=GPIO.HIGH)
else:
    GpioPin = -1
    PowerOffConnect = False


#Server config
ServerPort = int(Config.get("Server", "Port"))
cherrypy.config.update({'server.socket_port': ServerPort})

ServerHost = Config.get("Server", "Host")
cherrypy.config.update({'server.socket_host': ServerHost})


SerialArray = None
SelectedSerial = None

if not os.geteuid() == 0:
    sys.exit('Must be run as root')

def SerialRefresh(): #List serial ports
    global Log
    global SerialArray
    SerialArray = str(os.popen("ls /dev/tty* | sed '/tty[0-9]*$/d'").read()) #Getting list of serial ports
    SerialArray = SerialArray.split('\n') #Creating string list
    Log.Info("[CubePrint]Identified Usables serials.. : " + str(SerialArray))
    
def PlugUnplug():
    if UseGpio:
        return '''
        <a href="/PrinterPlug">Plug</a>
        <a href="/PrinterUnplug">Unplug</a>'''
    else: return ''
    
    
def SerialHtmlList(): #Create the select list of serials
    global SelectedSerial
    x = 0
    code = ""
    while True:
        if SerialArray[x] == "":
            break;
        if SerialArray[x] == SelectedSerial:
            code = code + "<option selected>" + SerialArray[x] + "</option>\n"
        else:
            code = code + "<option>" + SerialArray[x] + "</option>\n"
        x = x+1
    return code


class CubePrint(object): #Main server
    @cherrypy.expose
    def index(self): #Dynamic index
        return '''\
			<!DOCTYPE html>
			<html lang="fr">
				<head>
					<meta charset="utf-8">
					<title>CubePrint</title> <!-- Set the title -->
					<link rel="stylesheet" href="css/style.css"> <!-- Link to css file -->
					<link rel="icon" type="image/png" href="icon.png" /> <!-- Link to js main file -->
					<script src="http://code.jquery.com/jquery-2.1.3.min.js"></script> <!-- Link to jQuery library -->
					<script src="js/main.js"></script>
				</head>
				<body> <!-- Content -->
					Serial:<br>
					<form method="post" action="ConnectPrinter">
						<select name="_Serial" size="1"> ''' + str(SerialHtmlList()) + '''
						</select><br>
						BaudSpeed:<br>
						<select name="_BaudSpeed" size="1">
							<option>9600</option>
							<option>14400</option>
							<option>19200</option>
							<option>28800</option>
							<option>38400</option>
							<option>56000</option>
							<option>57600</option>
							<option>76800</option>
							<option>111112</option>
							<option>115200</option>
							<option>128000</option>
							<option>230400</option>
							<option>250000</option>
							<option>256000</option>
							<option>460800</option>
							<option>500000</option>
							<option>921600</option>
							<option>1000000</option>
							<option>1500000</option>
						</select><br>
						<input type="submit" text="Connect"></input>
					</form>
					<a href="/ReFreshSerials">ReFresh</a>
					<br><br>
					Pi :
					<a href="/ReBootPi">ReBoot</a>
					<a href="/DownPi">PowerOff</a>
					<br><br>
					Printing:
					<a href="/StartPrint">Start</a>
					<a href="/PausePrint">Pause</a>
					<a href="/CancelPrint">Cancel</a>
					<a href="/EmergencyStop">Emergency Stop</a>''' + str(PlugUnplug()) + '''
				</body> <!-- End of Content -->
			</html>     
			'''
    
    # Serial Functions
    @cherrypy.expose
    def ConnectPrinter(self,_Serial,_BaudSpeed):
        global Printer
        SelectedSerial = _Serial
        Log.Info("[CubePrint]Selected serial port : " + _Serial + "   Baud Speed : " + _BaudSpeed + "")
        Printer = serial.Serial()
        Printer.port = _Serial #Set serial port
        Printer.baudrate = _BaudSpeed #Set baudrate
        Printer.bytesize = serial.EIGHTBITS #number of bits per bytes
        Printer.parity = serial.PARITY_NONE #set parity check: no parity
        Printer.stopbits = serial.STOPBITS_ONE #number of stopp bits
        Printer.timeout = 0 #block read
        Printer.xonxoff = True #disable software flow control
        
		#Trying to connect to the printer
        Log.Info("[CubePrint]Trying to connect...", True)
        if PowerOffConnect: 
            GPIO.output(GpioPin, GPIO.LOW)
            time.sleep(0.5)
        try: 
            Printer.open()
        except Exception, e:
            Log.Fail("Failed !")

        if Printer.isOpen():
            Log.Success("Done.")
            Printer.flushInput()
            Printer.flushOutput()
        else:
            Log.Fail("Failed !")
		
        if PowerOffConnect: 
            GPIO.output(GpioPin, GPIO.HIGH)
            time.sleep(1)
			
        #Ok. Connected trying ton send a test command
        Log.Info("[CubePrint]Sending an M105 request..", True)
        if Printer.write("M105"):
		    Log.Success("Ok.")
        
		#Waiting for response a bit
        time.sleep(0.1)
        out = ""
        while True:
            if Printer.inWaiting() > 0:
                out += Printer.read(1) #Reading bytes from printer
            else: break
        
        out.split('\n')
        
        Log.Info(out)
        Printer.close() #Closing serial
        raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def ReFreshSerials(self):
        SerialRefresh()
        raise cherrypy.HTTPRedirect("/")
    
    # Pi Fucntions
    @cherrypy.expose
    def DownPi(self):
        Log.Info("[CubePrint]User requested a Pi shutdown !")
        os.system("sudo poweroff")
        raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def ReBootPi(self):
        Log.Info("[CubePrint]User requested a Pi reboot !")
        os.system("sudo reboot")    
        raise cherrypy.HTTPRedirect("/")
    
    # Print Functions
    @cherrypy.expose
    def StartPrint(self):
        Log.Info("[CubePrint]Starting print")
        raise cherrypy.HTTPRedirect("/")
    
    @cherrypy.expose
    def PausePrint(self):
        Log.Info("[CubePrint]Pausing print")    
        raise cherrypy.HTTPRedirect("/")
    
    @cherrypy.expose
    def ResumePrint(self):
        Log.Info("[CubePrint]Resuming print")    
        raise cherrypy.HTTPRedirect("/")
        
    @cherrypy.expose
    def CancelPrint(self):
        Log.Info("[CubePrint]Cancelling print")    
        raise cherrypy.HTTPRedirect("/")
        
    @cherrypy.expose
    def EmergencyStop(self):
        Log.Info("[CubePrint]Emergency stop launched !")
        raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def PrinterUnplug(self):
        Log.Info("[CubePrint]Removing printer alimentation !")
        if UseGpio:
            GPIO.output(GpioPin, GPIO.LOW)
        raise cherrypy.HTTPRedirect("/")
		
    @cherrypy.expose
    def PrinterPlug(self):
        Log.Info("[CubePrint]Powering on alimentation !")
        if UseGpio:
            GPIO.output(GpioPin, GPIO.HIGH)
        raise cherrypy.HTTPRedirect("/")

#Final Launch
if __name__ == '__main__':
    SerialRefresh()
    Log.Info("[CubePrint]Starting server.")
    cherrypy.quickstart(CubePrint(), '/', "server.conf") #Launching server !

