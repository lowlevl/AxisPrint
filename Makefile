all: dependencies install

dependencies:
	@echo "Installing dependencies.."
	sudo apt-get install Slic3r python python-serial
	@echo "Grabbing CherryPy Library.."
	@wget https://pypi.python.org/packages/source/C/CherryPy/CherryPy-3.8.0.tar.gz
	@echo "Unzipping CherryPy.."
	@tar -xzf CherryPy-3.8.0.tar.gz
	@echo "Installing CherryPy.."
	cd ./CherryPy-3.8.0 && sudo python setup.py install
	@echo "Cloning Simplejson repo.."
	git clone https://github.com/simplejson/simplejson.git
	@echo "Installing Simplejson.."
	cd ./simplejson && sudo python setup.py install
	@echo "Removing garbage.."
	sudo rm -f CherryPy-3.8.0.tar.gz
	sudo rm -rf CherryPy-3.8.0
	sudo rm -rf simplejson
	@echo "." > .dependInstalled
	@echo "Done."

install:
	@echo "Installing Cubeprint.."
	