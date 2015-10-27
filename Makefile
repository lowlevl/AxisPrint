all: dependencies

dependencies:
	sudo apt-get install Slic3r python python-serial python-wxgtk2.8 python-pyglet python-numpy cython python-libxml2 python-gobject python-dbus python-psutil
	git clone https://github.com/kliment/Printrun.git	
	sudo python Printrun/setup.py build
	sudo python Printrun/setup.py install		

install:
