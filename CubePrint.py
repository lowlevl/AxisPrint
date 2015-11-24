#!/usr/bin/python

print("\033[1;30;40mCubePrint - Loading libs...\033[m"), #Importing all libs
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
            print('\033[1;30;40m' + Text + '\033[m'),
        else:
            print('\033[1;30;40m' + Text + '\033[m')     
    
    def Success(self, Text, NoOEL = False):
        if NoOEL:
            print('\033[1;32;40m' + Text + '\033[m'),
        else:
            print('\033[1;32;40m' + Text + '\033[m')

class Printer: #Printer class
    def __init__(self):
        self.none = None
        self.port = None
        self.baudrate = None

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
        PrinterInterface.stopbits = serial.STOPBITS_ONE #number of stopp bits
        PrinterInterface.timeout = None #block read
        PrinterInterface.xonxoff = False #disable software flow control
        
        #Trying to connect to the printer
        Log.Info("CubePrint - Trying to connect...", True)
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
    
    def Disconnect(self):
        global ConsoleTemp
        global PrinterInterface
        PrinterInterface.close() #Closing serial
        ConsoleTemp = ConsoleTemp + "[!] Diconnected\n"
    
    def EmergencyStop(self):
        global PrinterInterface
        Log.Info("CubePrint - Emergency stop launched !")
        if PrinterInterface.isOpen() and EmergencyMode == 0:
            PrinterInterface.send("M112")
            
        if PrinterInterface.isOpen() and EmergencyMode == 1:
            PrinterInterface.send("M112")
            PrinterInterface.setDTR(1)
            time.sleep(1)
            PrinterInterface.setDTR(0)
            
        if PrinterInterface.isOpen() and EmergencyMode == 2:
            PrinterInterface.send("M112")
            self.Disconnect()
            self.Connect(self.port, self.baudrate)
            
            
    def Send(self, _Command):
        global PrinterInterface
        global ConsoleTemp
        if PrinterInterface.isOpen():
            Log.Info("Command sent : " + _Command)
            ConsoleTemp = ConsoleTemp + "[] " + str(_Command) + "\r\n"
            PrinterInterface.write((str(_Command)).rstrip() + "\r\n")
            
            time.sleep(1)
            out = ""
            while PrinterInterface.inWaiting() > 0:
                out += PrinterInterface.readline()
            ConsoleTemp = ConsoleTemp + out
            return out
        else:
            Log.Fail("Not oppened !")
            return None

class CubePrint(object): #Main server
    @cherrypy.expose
    def index(self): #Dynamic index
        global CamURL
        return '''
            <!DOCTYPE html>
                <html lang="fr">
                    <head>
                        <meta charset="ascii">
                        <title>CubePrint</title> <!-- Set the title -->
                        <link rel="stylesheet" href="css/style.css"> <!-- Link to css file -->
                        <link rel="icon" type="image/png" href="icon.png" /> <!-- Link to js main file -->
                        <script src="http://code.jquery.com/jquery-2.1.3.min.js"></script> <!-- Link to jQuery library -->
                        <script src="js/main.js"></script>
                    </head>
                    <body> <!-- Content 
                    
                        <!-- If no Javascript -->
                        <noscript class="noscript">
                            <div>
                                <h4><img src="jsError.png"></img>Javascript is not enabled, CubePrint will not work properly !</h4>
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
                            <button id="ConnectBut">Connect</button> <a href="/DisconnectPrinter" id="DscnctPrtr">DisconnectPrinter</a>
                        <a href="/ReFreshSerials" id="RfrshSer">ReFresh</a>
                        <!-- End Printer connect module -->
                        
                        <br><br>
                        Pi :
                        <a href="/ReBootPi" id="RbootPi">ReBoot</a>
                        <a href="/DownPi" id="ShutPi">PowerOff</a>
                        <br><br>
                        Printing:
                        <a href="/StartPrint" id="StartPrt">Start</a>
                        <a href="/PausePrint" id="PausePrt">Pause</a>
                        <a href="/CancelPrint" id="CancelPrt">Cancel</a>
                        <a href="/EmergencyStop" id="EmerStop">Emergency Stop</a>''' + str(PlugUnplug()) + '''<br>
                        
                        <!-- Console -->
                            <textarea id="Console" cols="50" rows="15" style="resize: none;" disabled>
                            </textarea><br>
                            <input type="text" id="CommandInput"></input>
                            <button id="ConsoleSender">Send Command</button>
                            <input type="checkbox" id="AutoDefil"></input>Auto-Defil
                        <!-- End Console -->
                        
                        <!-- Camera module --><br>
                        Camera: <br>
                        <img src="''' + CamURL + '''"></iframe>
                        <!-- End Camera module -->
                    </body> <!-- End of Content -->
                </html>     
            '''
            
    # Printer Functions
    @cherrypy.expose
    def ConnectPrinter(self,_SerialPort,_BaudSpeed):
        global SelectedSerial
        SelectedSerial = _SerialPort
        Log.Info("CubePrint - Selected serial port : " + _SerialPort + "   Baud Speed : " + _BaudSpeed)
        
        Printer.Connect(_SerialPort, _BaudSpeed)
        
        #Ok. Connected trying ton send a test command
        if Printer.Send("M105") != None:
            Log.Success("Ok.")
        else:
            Log.Fail("Failed !")
            raise cherrypy.HTTPRedirect("/")
        raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def DisconnectPrinter(self):
        Printer.Disconnect()
        raise cherrypy.HTTPRedirect("/")
    
    #Serial Functions
    @cherrypy.expose
    def ReFreshSerials(self):
        SerialRefresh()
        raise cherrypy.HTTPRedirect("/")
    
    @cherrypy.expose
    def Console(self, cmd):
        print(cmd)
        print Printer.Send(Command)        
        raise cherrypy.HTTPRedirect("/")
    
    # Pi Fucntions
    @cherrypy.expose
    def DownPi(self):
        Log.Info("CubePrint - User requested a Pi shutdown !")
        os.system("sudo poweroff")
        raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def ReBootPi(self):
        Log.Info("CubePrint - User requested a Pi reboot !")
        os.system("sudo reboot")    
        raise cherrypy.HTTPRedirect("/")
    
    #Print Functions
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
        raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def ATXoff(self):
        Log.Info("CubePrint - ATX Alimentation off")
        if UseGpio:
            GPIO.output(GpioPin, GPIO.LOW)
        raise cherrypy.HTTPRedirect("/")
        
    @cherrypy.expose
    def ATXon(self):
        Log.Info("CubePrint - ATX Alimentation on")
        if UseGpio:
            GPIO.output(GpioPin, GPIO.HIGH)
        raise cherrypy.HTTPRedirect("/")
        
    @cherrypy.expose
    def GetConsole(self):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return simplejson.dumps(dict(ConsoleText=ConsoleTemp))

#Define Global vars#            
Log = Log()
Printer = Printer()
PrinterInterface = serial.Serial()
SerialArray = None
SelectedSerial = None
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
EmergencyMode = Config.get("Other", "EmergencyMode")
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
        <a href="/ATXon">ATXon</a>
        <a href="/ATXoff">ATXoff</a>'''
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
    Log.Info("CubePrint - Identified Usables serials.. : " + str(SerialArray))
        
def SerialHtmlList(): #Create the select list of serials
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
    

#Final Launch
if __name__ == '__main__':
    SerialRefresh()
    Log.Info("CubePrint - Starting server at : " + str(ServerHost) + ":" + str(ServerPort))
    cherrypy.quickstart(CubePrint(), '/', "server.conf") #Launching server !

