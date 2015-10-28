all: dependencies

dependencies:
	sudo apt-get install Slic3r python python-serial python-wxgtk2.8 python-pyglet python-numpy cython python-libxml2 python-gobject python-dbus python-psutil
	if [ ! -d "./Printrun" ];then git clone https://github.com/kliment/Printrun.git; fi
	cd ./Printrun && sudo python setup.py build
	cd ./Printrun && sudo python setup.py install		
	sudo cp /usr/lib/python2.7/site-packages/Printrun-2015.03.10-py2.7.egg-info /usr/lib/python2.7/dist-packages/
	sudo cp -avf /usr/lib/python2.7/site-packages/printrun/ /usr/lib/python2.7/dist-packages/

install:

