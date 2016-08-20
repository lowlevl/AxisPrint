#!/usr/bin/python

print("Loading libs..."), #Importing all libs
import os
import sys
import time
import simplejson
from threading import Thread
import ConfigParser
import cherrypy
import serial
print("Ok")

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
        self.ConsoleLog = """
             """
        self.PrinterInterface = serial.Serial()

        self.SendLocked = False

        QueueThread = PrintingThread()
        QueueThread.start()

    def Connect(self, _SerialPort, _BaudSpeed):
        global NewConsoleLines
        global GCodeQueue
        global InstructionNumber
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

        InstructionNumber = 0

        #Trying to connect to the printer
        Log.Info("Trying to connect...", True)
        try:
            self.PrinterInterface.open()
        except Exception, e:
            Log.Fail("Failed !")

        if self.PrinterInterface.isOpen():
            Log.Success("Done.")
            self.PrinterInterface.flushInput()
            self.PrinterInterface.flushOutput()
            NewConsoleLines = NewConsoleLines + "[!] Connected to " + _SerialPort + "\n"
            GCodeQueue.insert(0, "M110 N0")

    def Disconnect(self):
        global NewConsoleLines
        global InstructionNumber

        InstructionNumber = 0

        if self.PrinterInterface.isOpen():
            self.PrinterInterface.close() #Closing serial
            NewConsoleLines = NewConsoleLines + "[!] Diconnected\n"
            Log.Warning("Printer disconnected.")
        else:
            Log.Failed("Can't disconnect not connected !")

    def EmergencyStop(self):
        global EmergencyMode
        global GCodeQueue
        global InstructionNumber

        InstructionNumber = 0

        if self.PrinterInterface.isOpen() and EmergencyMode == 0:
            Log.Warning("Emergency ! Mode:" + str(EmergencyMode))
            GCodeQueue.insert(0, "M112")

        if self.PrinterInterface.isOpen() and EmergencyMode == 1:
            Log.Warning("Emergency ! Mode:" + str(EmergencyMode))
            GCodeQueue.insert(0, "M112")
            Log.Warning("DTR: On")
            self.PrinterInterface.setDTR(1)
            time.sleep(1)
            Log.Warning("DTR: Off")
            self.PrinterInterface.setDTR(0)

        if self.PrinterInterface.isOpen() and EmergencyMode == 2:
            Log.Warning("Emergency ! Mode:" + str(EmergencyMode))
            GCodeQueue.insert(0, "M112")
            self.Disconnect()
            self.Connect(self.port, self.baudrate)

    def Send(self, _Command):
        global NewConsoleLines
        ToSend = ""
        if self.PrinterInterface.isOpen():
            ToSend = ((str(_Command)).rstrip() + "\r\n") #Creating full command to sent to printer

            #Sending command
            self.PrinterInterface.write(ToSend)

            #Log the user
            NewConsoleLines = NewConsoleLines + "[] " + str(ToSend) + "\r\n"
        else:
            Log.Fail("Not oppened !")

    def Read(self):
        global NewConsoleLines
        Text = self.PrinterInterface.read(self.PrinterInterface.inWaiting())
        NewConsoleLines = NewConsoleLines + Text
        return Text

    def LoadFile(self, _FileName):
        global GCodeQueue
        GCode = ""
        with open(_FileName, 'r') as File:
            GCode = File.readlines()
            GCodeQueue = GCodeQueue + GCode
            Log.Info("Done loading GCode !")

    def Pause(self):
        global PausedPrint
        global NewConsoleLines
        if PausedPrint == True:
            PausedPrint = False
            NewConsoleLines = NewConsoleLines + "[!] Resumed print !\n"
        else:
            if PausedPrint == False:
                PausedPrint = True
                NewConsoleLines = NewConsoleLines + "[!] Paused print !\n"

    def Cancel(self):
        global GCodeQueue
        global NewConsoleLines
        GCodeQueue = ['']
        NewConsoleLines = NewConsoleLines + "[!] Canceled print !\n"
        Log.Warning("Canceled print !")

class PrintingThread(Thread): # Send the queue to the printer
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        global PausedPrint
        global GCodeQueue
        global InstructionNumber
        PausedPrint = False
        while True:
            if len(GCodeQueue) > 1 and not PausedPrint:
                Log.Info("Queue : " + str(len(GCodeQueue)))
                Line = GCodeQueue[0]
                if (Line == None or Line == "" or Line == "\r" or Line == "\n" or Line == "\r\n" or Line == "\n\r" or list(Line)[0] == ";"):
                    del GCodeQueue[0]
                else:
                    Printer.Send("N" + str(InstructionNumber) + " " + Line)
                    InstructionNumber = InstructionNumber + 1
                    while True:
                        if "ok" in Printer.Read():
                            break
                        time.sleep(0.01)
                    del GCodeQueue[0]

class AxisPrint(object): #Main server
    @cherrypy.expose
    def index(self): #Dynamic index
        global CamURL
        return '''
            <!DOCTYPE html>
                <html lang="fr">
                    <head>
                        <meta charset="UTF-8">
                        <title>AxisPrint :: 3D Printer server</title>

                        <link rel="stylesheet" href="css/style.css"> <!-- Link to css file -->
                        <link rel="icon" type="image/png" href="icon.png" /> <!-- Link to icon -->
                        <script src="http://code.jquery.com/jquery-2.1.3.min.js"></script> <!-- Link to jQuery library -->
                        <script src="js/main.js"></script> <!-- Link to Main.js file -->

                        <!-- BootStrap include -->
                        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css" integrity="sha384-1q8mTJOASx8j1Au+a5WDVnPi2lkFfwwEAa8hDDdjZlpLegxhjVME1fgjWPGmkzs7" crossorigin="anonymous">
                        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/js/bootstrap.min.js" integrity="sha384-0mSbJDEHialfmuBBQP6A4Qrprq5OVfW37PRR3j5ELqxss1yVqOtnepnHVP9aJ7xS" crossorigin="anonymous"></script>
                        <!-- End of BootStrap -->
                    </head>
                    <body> <!-- Content -->

                        <div class="container-fluid">
                            <h2 class="pull-right">Bienvenue sur PiPrintr</h2>
                        </div>

                        <!-- If no Javascript -->
                        <noscript class="noscript">
                            <div>
                                <h4><img src="jsError.png"></img>Javascript is not enabled, PiPrintr will not work properly !</h4>
                            </div>
                        </noscript>
                        <!-- Endif no Javascript -->

                        <div class="container">
                            <!-- Printer connect module -->
                                <legend>Printer connection</legend>
                                <div class="form-horizontal">
                                    <div class="form-group">
                                        <label class="col-md-4 control-label" for="SerialPort">Serial : </label>
                                        <div class="col-md-4">
                                            <select id="SerialPort" size="1" class="form-control"> ''' + str(SerialHtmlList()) + '''
                                            </select>
                                        </div>
                                    </div>

                                    <div class="form-group">
                                        <label class="col-md-4 control-label" for="BaudSpeed">BaudSpeed : </label>
                                        <div class="col-md-4">
                                            <select id="BaudSpeed" size="1" class="form-control">
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
                                            </select>
                                        </div>
                                    </div>
                                    <div class="form-group">
                                        <div class="col-md-4"></div>
                                        <div class="col-md-2"><button id="ConnectRequest" class="btn btn-success"><i class="glyphicon glyphicon-log-in"></i> Connect</button></div>
                                        <button id="DscnctPrtr" class="btn btn-danger"><i class="glyphicon glyphicon-log-out"></i> DisconnectPrinter</button>
                                        <button id="RfrshSer" class="btn btn-warning"><i class="glyphicon glyphicon-refresh"></i> ReFresh</button>
                                    </div>
                                </div>
                            <!-- End Printer connect module -->

                            <!-- Host module -->
                                <legend>Host</legend>
                                <center>
                                    <div class="form-group">
                                        <button id="RbootHost" class="btn btn-warning"><i class="glyphicon glyphicon-refresh"></i> ReBoot</button>
                                        <button id="ShutHost" class="btn btn-danger"><i class="glyphicon glyphicon-off"></i> PowerOff</button>
                                    </div>
                                </center>
                            <!-- End of Host module -->

                            <!-- Printing control module -->
                                <legend>Printing control</legend>
                                <button id="StartPrt" class="btn btn-primary"><i class="glyphicon glyphicon-play"></i> Start</button>
                                <button id="PausePrt" class="btn btn-primary"><i class="glyphicon glyphicon-pause"></i> Pause</button>
                                <button id="CancelPrt" class="btn btn-warning"><i class="glyphicon glyphicon-stop"></i> Cancel</button>
                                <button id="EmerStop" class="btn btn-danger"><i class="glyphicon glyphicon-alert"></i> Emergency Stop</button><br>
                                <br>
                            <!-- End Printing control module -->

                            <!-- Console -->
                                <div class="row">
                                    <textarea id="Console" rows="15" style="resize: none;" class="form-control" disabled></textarea><br>
                                    <div class="col-md-6">
                                        <input id="CommandInput" class="form-control input-md" type="text"/>
                                    </div>

                                    <div class="col-md-4">
                                        <div class="row">
                                            <button id="ConsoleSender" class="btn btn-primary"><i class="glyphicon glyphicon-console"></i> Send Command</button>
                                            <button id="ClrConsole" class="btn btn-warning"><i class="glyphicon glyphicon-ban-circle"></i> Clear</button>
                                        </div>
                                    </div>

                                    <span class="label label-default" style="padding:10px"><i class="glyphicon glyphicon-sort"></i> Auto-Defil <input type="checkbox" id="AutoDefil"/></span>
                                </div><br>
                            <!-- End Console -->

                            <!-- Upload -->
                                <legend>File</legend>
                                <div class="form-horizontal">
                                    <div class="col-md-3">
                                        <center>
                                            <h5><label>File list :</label></h4>
                                            <div id="FileList"></div>
                                        </center>
                                    </div>
                                    <div class="col-md-9">
                                        <div class="row">
                                            <div id="FileButton" class="fileUpload btn btn-primary" style="margin:0px; margin-left:15px">
                                                <i class="glyphicon glyphicon-upload"></i> Upload
                                                <input id="File2Up" type="file" accept=".gcode" class="Upload"/>
                                            </div>
                                            <button id="CancelUp" class="btn btn-danger disabled" style="margin:0px"><i class="glyphicon glyphicon-remove"></i> Cancel</button>
                                        </div>
                                        <div class="progress" style="margin:0px; margin-top:10px">
                                            <div class="progress-bar progress-bar-info" id="UpBar" role="progressbar" style="width:0%">
                                                <div id="UpSuccess"></div>
                                            </div>
                                        </div>
                                    </div>
                                </div><br><br>
                            <!-- End Upload -->

                            <!-- Camera module -->
                                <legend>Camera</legend>
                                <img src="''' + CamURL + '''"></img>
                            <!-- End Camera module -->

                            <!-- ConnErrorPopUp module -->
                                <div id="ConnErrorPopUp"></div>
                            <!-- End ConnErrorPopUp module -->
                        </div>
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
        global GCodeQueue
        GCodeQueue.insert(0, cmd.splitlines()[0])

    # Pi Fucntions
    @cherrypy.expose
    def DownHost(self):
        Log.Critical("Shuting down !")
        os.system("sudo poweroff")

    @cherrypy.expose
    def ReBootHost(self):
        Log.Critical("Rebooting !")
        os.system("sudo reboot")

    # Print Functions
    @cherrypy.expose
    def StartPrint(self):
        Printer.LoadFile("models/composition.gcode")

    @cherrypy.expose
    def PausePrint(self):
        Printer.Pause()

    @cherrypy.expose
    def CancelPrint(self):
        Printer.Cancel()

    @cherrypy.expose
    def EmergencyStop(self):
        Printer.EmergencyStop()

    @cherrypy.expose
    def Get(self):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        global NewConsoleLines
        NewConsoleLines_tmp = ""
        NewConsoleLines_tmp = NewConsoleLines
        NewConsoleLines = ""
        return simplejson.dumps(dict(NewLines=NewConsoleLines_tmp, FileList=str(os.popen("ls models").read())))

    # File Functions
    @cherrypy.expose
    def UpLoad(self, _UploadedFile, FileName, Size):
        Log.Success("Done upload of " + FileName + " (" + Size + " octets)")
        Log.Info("Starting processing...", True)
        Path2Save = "models/" + FileName;
        FileData = ""

        while True:
            datatmp = _UploadedFile.file.read(8192)
            FileData += datatmp
            if not datatmp:
                break


        if not os.path.exists(os.path.dirname(Path2Save)):
            os.makedirs(os.path.dirname(Path2Save))

        File2Write = open(Path2Save, 'w')
        File2Write.write(FileData)
        File2Write.close()

        uid = os.environ.get('SUDO_UID')
        gid = os.environ.get('SUDO_GID')
        if uid is not None:
            os.chown(Path2Save, int(uid), int(gid))

        Log.Success("Done !")

#Define Global vars#
Log = Log()
Printer = Printer()
SerialArray = None
PausedPrint = False
GCodeQueue = ['']
NewConsoleLines = ""
InstructionNumber = 0

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
    cherrypy.quickstart(AxisPrint(), '/', "server.conf") #Launching server !

