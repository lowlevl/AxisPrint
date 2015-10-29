#!/usr/bin/python

print("[CubePrint]Loading libraries..."), 
import os
import cherrypy
import printrun
print("Ok")



def SerialCheck():
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
<html>
    <head>	
	<title>CubePrint</title>
	<link rel="icon" type="image/png" href="/htdocs/logo.png" />
    </head>
    <body>
	<img src="/htdocs/logo.png" />
	<form method="post" action="SelectSerial">
	    <select name="Serial" size="1"> ''' + str(SerialHtmlList()) + '''
	    </select>
	    <input type="submit" label="Connect"></input>
	</form>		
    </body>
</html>
'''
    
    @cherrypy.expose
    def SelectSerial(self,Serial):
	global SelectedSerial
	SelectedSerial = Serial
	print("[CubePrint]Selected serial port : " + SelectedSerial)
	raise cherrypy.HTTPRedirect("/")	

if __name__ == '__main__':
    print("[CubePrint]Starting server..")
    SerialCheck()
    cherrypy.quickstart(CubePrint(), '/', "Server.conf") #Launching server !

