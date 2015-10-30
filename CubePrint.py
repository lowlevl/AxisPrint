#!/usr/bin/python

print("[CubePrint]Loading libraries..."), 
import os
import cherrypy
import printrun
print("Ok")
SelectedSerial = " "


def SerialRefresh():
    global Serials
    tmp = str(os.popen("ls /dev/tty* | sed '/tty[0-9]*$/d'").read()) #Getting list of Serials
    Serials = tmp.replace('\n', ' ') 
    Serials = Serials.split(' ') #Creating string list
    print "[CubePrint]Identified Usables serials.. : " + str(Serials)


def SerialHtmlList(): #Create the Serial list
    x = 0
    code = ""
    while True:
        if Serials[x] == "":
            break;
	if Serials[x] == SelectedSerial:
	    code = code + "<option selected>" + Serials[x] + "</option>\n"
        else:
	    code = code + "<option>" + Serials[x] + "</option>\n"
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
        <form method="post" action="SelectSerial">
            <select name="Serial" size="1"> ''' + str(SerialHtmlList()) + '''
            </select>
            <input type="submit" label="Connect"></input>
        </form>
        <a href="/ReFreshSerials">ReFresh</a>
    </body> <!-- End of Content -->
</html>     
'''

    @cherrypy.expose
    def SelectSerial(self,Serial):
	global SelectedSerial
	SelectedSerial = Serial
	print("[CubePrint]Selected serial port : " + SelectedSerial)
	raise cherrypy.HTTPRedirect("/")	

    @cherrypy.expose
    def ReFreshSerials(self):
	SerialRefresh()
	raise cherrypy.HTTPRedirect("/")

#Final Launch
if __name__ == '__main__':
    print("[CubePrint]Starting server..")
    SerialRefresh()
    cherrypy.quickstart(CubePrint(), '/', "server.conf") #Launching server !

