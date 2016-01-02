#!/usr/bin/python

print("\033[1;30;40mLoading libs...\033[m"), #Importing all libs
import os
import sys  
import time
import simplejson
import RPi.GPIO as GPIO
import ConfigParser
import cherrypy
import serial
print("\033[1;32;40mOk\033[m") 

if not os.geteuid() == 0: #Check if is started as root
    sys.exit('Must be run as root')

class Log: #Colored logs !
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
            print('\033[0;37;40m' + Text + '\033[m'),
        else:
            print('\033[0;37;40m' + Text + '\033[m')     
    
    def Success(self, Text, NoOEL = False):
        if NoOEL:
            print('\033[1;32;40m' + Text + '\033[m'),
        else:
            print('\033[1;32;40m' + Text + '\033[m')

class Printer: #Printer class
    def __init__(self):
        self.port = None
        self.baudrate = None
        self.InstructionNumber = 0
        self.ConsoleLog = """
             """

    def Connect(self, _SerialPort, _BaudSpeed):
        global ConsoleTemp
        global PrinterInterface
        self.port = _SerialPort
        self.baudrate = _BaudSpeed
        PrinterInterface = serial.Serial()
        PrinterInterface.port = _SerialPort #Set serial port
        PrinterInterface.baudrate = _BaudSpeed #Set baudrate
        PrinterInterface.bytesize = serial.EIGHTBITS #number of bits per bytes
        PrinterInterface.parity = serial.PARITY_NONE #set parity check: no parity
        PrinterInterface.stopbits = serial.STOPBITS_ONE #number of stop bits
        PrinterInterface.timeout = None #block read
        PrinterInterface.xonxoff = False #disable software flow control
        
        #Trying to connect to the printer
        Log.Info("Trying to connect...", True)
        try: 
            PrinterInterface.open()
        except Exception, e:
            Log.Fail("Failed !")
            raise cherrypy.HTTPRedirect("/")

        if PrinterInterface.isOpen():
            Log.Success("Done.")
            PrinterInterface.flushInput()
            PrinterInterface.flushOutput()
            ConsoleTemp = ConsoleTemp + "[!] Connected to " + _SerialPort + "\n"
            Printer.Send("M110 N0")
    
    def Disconnect(self):
        global ConsoleTemp
        global PrinterInterface
        self.InstructionNumber = 0
        if PrinterInterface.isOpen():
            PrinterInterface.close() #Closing serial
            ConsoleTemp = ConsoleTemp + "[!] Diconnected\n"
            Log.Warning("Printer disconnected.")
        else:
            Log.Failed("Can't disconnect not connected !")
    
    def EmergencyStop(self):
        global PrinterInterface
        global EmergencyMode
        if PrinterInterface.isOpen() and EmergencyMode == 0:
            Log.Warning("Emergency ! Mode:" + str(EmergencyMode))
            self.Send("M112")
            
        if PrinterInterface.isOpen() and EmergencyMode == 1:
            Log.Warning("Emergency ! Mode:" + str(EmergencyMode))
            self.Send("M112")
            Log.Warning("DTR: On")
            PrinterInterface.setDTR(1)
            time.sleep(1)
            Log.Warning("DTR: Off")
            PrinterInterface.setDTR(0)
            
        if PrinterInterface.isOpen() and EmergencyMode == 2:
            Log.Warning("Emergency ! Mode:" + str(EmergencyMode))
            self.Send("M112")
            self.Disconnect()
            self.Connect(self.port, self.baudrate)
            
            
    def Send(self, _Command):
        global PrinterInterface
        global ConsoleTemp
        ToSend = ""
        if PrinterInterface.isOpen():
            ToSend = ("N" + str(self.InstructionNumber) + " " + (str(_Command)).rstrip() + "\r\n") #Creating full command to sent to printer
            
            #Printer vars(Including a Console log if printer request a resend)
            self.ConsoleLog += ToSend
            self.InstructionNumber += 1
            
            #Sending command
            PrinterInterface.write(ToSend)
            
            #Log the user
            ConsoleTemp = ConsoleTemp + "[] " + str(ToSend) + "\r\n"
            Log.Info("Command sent : " + ToSend)
            
            time.sleep(0.3)
            out = ""
            tmp = ""
            waitcount = 0
            while PrinterInterface.inWaiting() > 0:
                tmp = PrinterInterface.readline()
                out += tmp
                ConsoleTemp = ConsoleTemp + tmp
            return out
        else:
            Log.Fail("Not oppened !")
            return None

class PiPrintr(object): #Main server
    @cherrypy.expose
    def index(self): #Dynamic index
        global CamURL
        return '''
            <!DOCTYPE html>
                <html lang="fr">
                    <head>
                        <meta charset="ascii">
                        <title>PiPrintr</title> <!-- Set the title -->
                        <link rel="stylesheet" href="css/style.css"> <!-- Link to css file -->
                        <link rel="icon" type="image/png" href="icon.png" /> <!-- Link to js main file -->
                        <script src="http://code.jquery.com/jquery-2.1.3.min.js"></script> <!-- Link to jQuery library -->
                        <script src="js/main.js"></script>
                    </head>
                    <body> <!-- Content 
                    
                        <!-- If no Javascript -->
                        <noscript class="noscript">
                            <div>
                                <h4><img src="jsError.png"></img>Javascript is not enabled, PiPrintr will not work properly !</h4>
                            </div>
                        </noscript>
                        <!-- Endif no Javascript -->
                        
                        <!-- Printer connect module -->
                        Serial:<br>
                            <select id="SerialPort" size="1"> ''' + str(SerialHtmlList()) + '''
                            </select><br>
                            BaudSpeed:<br>
                            <select id="BaudSpeed" size="1">
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
                            <button id="ConnectRequest">Connect</button> <button id="DscnctPrtr">DisconnectPrinter</button>
                        <button id="RfrshSer">ReFresh</button>
                        <!-- End Printer connect module -->
                        
                        <br><br>
                        Pi :
                        <button id="RbootPi">ReBoot</button>
                        <button id="ShutPi">PowerOff</button>
                        <br><br>
                        Printing:
                        <button id="StartPrt">Start</button>
                        <button id="PausePrt">Pause</button>
                        <button id="CancelPrt">Cancel</button>
                        <button id="EmerStop">Emergency Stop</button>''' + str(PlugUnplug()) + '''<br>
                        
                        <!-- Console -->
                            <textarea id="Console" cols="50" rows="15" style="resize: none;" disabled>
                            </textarea><br>
                            <input type="text" id="CommandInput"></input>
                            <button id="ConsoleSender">Send Command</button>
                            <input type="checkbox" id="AutoDefil"></input>Auto-Defil
                            <button id="ClrConsole">Clear</button>
                        <!-- End Console -->
                        
                        <!-- Camera module --><br>
                            Camera: <br>
                            <img src="''' + CamURL + '''"></img>
                        <!-- End Camera module -->
                        
                        </body> <!-- End of Content -->
                </html>     
            '''
            
    # Printer Functions
    @cherrypy.expose
    def ConnectPrinter(self, _SerialPort, _BaudSpeed):
        Log.Info("Selected serial port : " + _SerialPort + "   Baud Speed : " + _BaudSpeed)
        Printer.Connect(_SerialPort, _BaudSpeed)

    @cherrypy.expose
    def DisconnectPrinter(self):
        Printer.Disconnect()
    
    # Serial Functions
    @cherrypy.expose
    def ReFreshSerials(self):
        SerialRefresh()
    
    @cherrypy.expose
    def Console(self, cmd):
        Printer.Send(cmd.splitlines()[0])     
    
    # Pi Fucntions
    @cherrypy.expose
    def DownPi(self):
        Log.Critical("Shuting down !")
        os.system("sudo poweroff")

    @cherrypy.expose
    def ReBootPi(self):
        Log.Critical("Rebooting !")
        os.system("sudo reboot")    
    
    # Print Functions
    @cherrypy.expose
    def StartPrint(self):
        raise cherrypy.HTTPRedirect("/")
    
    @cherrypy.expose
    def PausePrint(self):  
        raise cherrypy.HTTPRedirect("/")
    
    @cherrypy.expose
    def ResumePrint(self): 
        raise cherrypy.HTTPRedirect("/")
        
    @cherrypy.expose
    def CancelPrint(self):   
        raise cherrypy.HTTPRedirect("/")
        
    @cherrypy.expose
    def EmergencyStop(self):
        Printer.EmergencyStop()

    @cherrypy.expose
    def ATXoff(self):
        if UseGpio:
            GPIO.output(GpioPin, GPIO.LOW)
            Log.Info("ATX Alimentation off")
        else:
            Log.Warning("Disabled GPIO an trying to use it !")
        
    @cherrypy.expose
    def ATXon(self):
        if UseGpio:
            GPIO.output(GpioPin, GPIO.HIGH)
            Log.Info("ATX Alimentation on")
        else:
            Log.Warning("Disabled GPIO an trying to use it !")
        
    @cherrypy.expose
    def GetConsole(self):
        global ConsoleTemp
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return simplejson.dumps(dict(ConsoleText=ConsoleTemp))
    
    @cherrypy.expose
    def ClearConsole(self):
        Log.Warning("Cleared console !")
        global ConsoleTemp
        ConsoleTemp = ""
        return ""

#Define Global vars#            
Log = Log()
Printer = Printer()
PrinterInterface = serial.Serial()
SerialArray = None
ConsoleTemp = ""

############################
#----------Config----------#
############################
Config = ConfigParser.ConfigParser() #Loading config file
Config.read('config.conf')

#---Camera Config---#
CamURL = Config.get("LiveCamera", "Url")
EnabledCam = Config.getboolean("LiveCamera", "Enabled")
if not EnabledCam:
    CamURL = ""
#---End Camera Config---#

#---Printer Config---#
EmergencyMode = int(Config.get("Other", "EmergencyMode"))
#---End of Printer Config---#

#---GPIO Config---#
UseGpio = Config.getboolean("Gpio", "Enabled")
GpioPin = int(Config.get("Gpio", "GpioPin"))

if UseGpio:
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(GpioPin, GPIO.OUT, initial=GPIO.HIGH)
else:
    GpioPin = -1

def PlugUnplug(): #Add or remove functions in panel
    if UseGpio:
        return '''
        <button id="ATXon">ATXon</button>
        <button id="ATXoff">ATXoff</button>'''
    else: return ''
#---End of GPIO Config---#

#---Server Config---#
ServerPort = int(Config.get("Server", "Port"))
cherrypy.config.update({'server.socket_port': ServerPort})

ServerHost = Config.get("Server", "Host")
cherrypy.config.update({'server.socket_host': ServerHost})
#---End of Server Config---#

###################################
#----------End of Config----------#
###################################

def SerialRefresh(): #List serial ports
    global Log
    global SerialArray
    SerialArray = str(os.popen("ls /dev/tty* | sed '/tty[0-9]*$/d'").read()) #Getting list of serial ports
    SerialArray = SerialArray.split('\n') #Creating string list
    Log.Info("Identified Usables serials.. : " + str(SerialArray))
        
def SerialHtmlList(): #Create the select list of serials
    x = 0
    code = ""
    while True:
        if SerialArray[x] == "":
            break;
        code = code + "<option>" + SerialArray[x] + "</option>\n"
        x = x+1
    return code
    

#Final Launch
if __name__ == '__main__':
    SerialRefresh()
    Log.Info("Starting server at : " + str(ServerHost) + ":" + str(ServerPort))
    cherrypy.quickstart(PiPrintr(), '/', "server.conf") #Launching server !

