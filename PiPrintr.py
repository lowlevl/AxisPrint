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
        self.GCode = None
        self.PrinterInterface = serial.Serial()
        self.PausedPrint = False
        self.Printing = False

    def Connect(self, _SerialPort, _BaudSpeed):
        global NewConsoleLines
        self.port = _SerialPort
        self.baudrate = _BaudSpeed
        self.PrinterInterface = serial.Serial()
        self.PrinterInterface.port = _SerialPort #Set serial port
        self.PrinterInterface.baudrate = _BaudSpeed #Set baudrate
        self.PrinterInterface.bytesize = serial.EIGHTBITS #number of bits per bytes
        self.PrinterInterface.parity = serial.PARITY_NONE #set parity check: no parity
        self.PrinterInterface.stopbits = serial.STOPBITS_ONE #number of stop bits
        self.PrinterInterface.timeout = None #block read
        self.PrinterInterface.xonxoff = False #disable software flow control
        
        #Trying to connect to the printer
        Log.Info("Trying to connect...", True)
        try: 
            self.PrinterInterface.open()
        except Exception, e:
            Log.Fail("Failed !")
            raise cherrypy.HTTPRedirect("/")

        if self.PrinterInterface.isOpen():
            Log.Success("Done.")
            self.PrinterInterface.flushInput()
            self.PrinterInterface.flushOutput()
            NewConsoleLines = NewConsoleLines + "[!] Connected to " + _SerialPort + "\n"
            Printer.Send("M110 N0")
    
    def Disconnect(self):
        global NewConsoleLines
        self.InstructionNumber = 0
        if self.PrinterInterface.isOpen():
            self.PrinterInterface.close() #Closing serial
            NewConsoleLines = NewConsoleLines + "[!] Diconnected\n"
            Log.Warning("Printer disconnected.")
        else:
            Log.Failed("Can't disconnect not connected !")
    
    def EmergencyStop(self):
        global EmergencyMode
        if self.PrinterInterface.isOpen() and EmergencyMode == 0:
            Log.Warning("Emergency ! Mode:" + str(EmergencyMode))
            self.Send("M112")
            
        if self.PrinterInterface.isOpen() and EmergencyMode == 1:
            Log.Warning("Emergency ! Mode:" + str(EmergencyMode))
            self.Send("M112")
            Log.Warning("DTR: On")
            self.PrinterInterface.setDTR(1)
            time.sleep(1)
            Log.Warning("DTR: Off")
            self.PrinterInterface.setDTR(0)
            
        if self.PrinterInterface.isOpen() and EmergencyMode == 2:
            Log.Warning("Emergency ! Mode:" + str(EmergencyMode))
            self.Send("M112")
            self.Disconnect()
            self.Connect(self.port, self.baudrate)
            
            
    def Send(self, _Command):
        global NewConsoleLines
        ToSend = ""
        if self.PrinterInterface.isOpen() and not (_Command == None or _Command == ""):
            ToSend = ("N" + str(self.InstructionNumber) + " " + (str(_Command)).rstrip() + "\r\n") #Creating full command to sent to printer
            
            #Printer vars(Including a Console log if printer request a resend)
            self.ConsoleLog += ToSend
            self.InstructionNumber += 1
            
            #Sending command
            self.PrinterInterface.write(ToSend)
            
            #Log the user
            NewConsoleLines = NewConsoleLines + "[] " + str(ToSend) + "\r\n"
            #Log.Info("Command sent : " + ToSend)
            
            time.sleep(0.3)
            out = ""
            tmp = ""
            waitcount = 0
            while self.PrinterInterface.inWaiting() > 0:
                tmp = self.PrinterInterface.read()
                out += tmp
                NewConsoleLines = NewConsoleLines + tmp
            return out
        else:
            Log.Fail("Not oppened !")
            return None
        
    def LoadFile(self, _FileName):
        self.GCode = ""
        with open(_FileName, 'r') as File:
            self.GCode = File.readlines()        
            
    def Print(self):
        if not self.Printing and self.PrinterInterface.isOpen():
            self.Printing = True
            self.PausePrint = False
            i = 0
            while True:
                if not self.PausedPrint:
                    Line = self.GCode[i]
                    Log.Info("Sending Line: " + i)
                    i = i+1
                    if not Line:
                        self.Printing = False
                        break
                    if not (Line == "\r\n"  or Line == "\n"  or Line == "\r" or list(Line)[0] == " " or list(Line)[0] == ";"):
                        Printer.Send(Line)
                if not self.Printing:
                    break
    
    def Pause(self):
        global NewConsoleLines
        if self.PausedPrint == True:
            self.PausedPrint = False
            NewConsoleLines = NewConsoleLines + "[!] Resumed print !\n"
        else: 
            if self.PausedPrint == False:
                self.PausedPrint = True
                NewConsoleLines = NewConsoleLines + "[!] Paused print !\n"
            
            

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
                        <script src="js/main.js"></script> <!-- Link to Main.js file -->
                        
                        <!-- BootStrap -->
                        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css" integrity="sha384-1q8mTJOASx8j1Au+a5WDVnPi2lkFfwwEAa8hDDdjZlpLegxhjVME1fgjWPGmkzs7" crossorigin="anonymous">
                        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap-theme.min.css" integrity="sha384-fLW2N01lMqjakBkx3l/M9EahuwpSfeNvV63J5ezn3uZzapT0u7EYsXMjQV+0En5r" crossorigin="anonymous">
                        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/js/bootstrap.min.js" integrity="sha384-0mSbJDEHialfmuBBQP6A4Qrprq5OVfW37PRR3j5ELqxss1yVqOtnepnHVP9aJ7xS" crossorigin="anonymous"></script>
                        <!-- End of BootStrap -->
                    </head>
                    <body> <!-- Content 
                    
                        <!-- If no Javascript -->
                        <noscript class="noscript">
                            <div>
                                <h4><img src="jsError.png"></img>Javascript is not enabled, PiPrintr will not work properly !</h4>
                            </div>
                        </noscript>
                        <!-- Endif no Javascript -->
                        
                        <span class="glyphicon glyphicon-search" aria-hidden="true"></span>
                        
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
                        
                        <!-- Upload -->
                            <br>File: <br>
                            <div class="fileUpload btn btn-info">
                                <span>Upload</span>
                                <input id="File2Up" type="file" accept=".gcode" class="Upload"/>
                            </div>
                            <div class="progress" style="width:300px">
                                <div class="progress-bar progress-bar-info" id="UpBar" role="progressbar" style="width:0%">
                                    <div id="UpSuccess"></div>
                                </div>
                            </div>
                        <!-- End Upload -->
                        
                        <!-- Camera module --><br>
                            Camera: <br>
                            <img src="''' + CamURL + '''"></img>
                        <!-- End Camera module -->
                        
                        <!-- ConnErrorPopUp module -->
							<div id="ConnErrorPopUp"></div>
                        <!-- End ConnErrorPopUp module -->
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
        Printer.LoadFile(os.path.abspath(os.getcwd()) + "/models/composition.gcode")
        Printer.Print()
    
    @cherrypy.expose
    def PausePrint(self):
        Printer.Pause()
    
    @cherrypy.expose
    def ResumePrint(self):
        Log.Info()
        
    @cherrypy.expose
    def CancelPrint(self):   
        Log.Info()
        
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
    def Get(self):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        global NewConsoleLines
        NewConsoleLines_tmp = ""
        NewConsoleLines_tmp = NewConsoleLines
        NewConsoleLines = ""
        return simplejson.dumps(dict(NewLines=NewConsoleLines_tmp))
    
    # File Functions
    @cherrypy.expose
    def UpLoad(self, _UploadedFile, FileName, Size):
        Log.Info("Starting upload of " + FileName + " who has a size of " + Size + "octet(s)..", True)
        Path2Save = "models/" + FileName;
        FileData = ""
        
        while True:
            datatmp = _UploadedFile.file.read(8192)
            FileData += datatmp
            if not datatmp:
                break
            
        File2Write = open(Path2Save, 'w')
        File2Write.write(FileData)
        File2Write.close()
        Log.Success("Ok.")
        

#Define Global vars#            
Log = Log()
Printer = Printer()
SerialArray = None
NewConsoleLines = ""

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

