all: dependencies

dependencies:
	sudo apt-get install Slic3r python python-serial python-wxgtk2.8 python-pyglet python-numpy cython python-libxml2 python-gobject python-dbus python-psutil
	git clone https://github.com/kliment/Printrun.git	
	cd Printrun
	sudo python setup.py build
	sudo python setup.py install		

install:
