#!/usr/bin/python
 
import os
import cherrypy
import printrun

tmp = str(os.popen("ls /dev/tty* | sed 's/[0-9]//g' | uniq").read())
Serials = tmp.replace('\n', ' ')
Serials = Serials.split(' ')
print "[CubePrint]Identified Usables serials.. : " + str(Serials)

class CubePrint(object):
    @cherrypy.expose
    def index(self):
        return """<!DOCTYPE html>
	    <html>
	        <head>	
	            <title>CubePrint</title>
		</head>
		<body>

		</body>
	    </html>
	"""

cherrypy.config.update({'server.socket_host': '0.0.0.0',
                        'server.socket_port': 1234})

cherrypy.config.update({'log.screen': False,
                        'log.access_file': 'acceslog.log',
                        'log.error_file': 'serverlog.log'})

cherrypy.quickstart(CubePrint())
