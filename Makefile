all: dependencies

dependencies:
	@echo "Installing dependencies.."
	sudo apt-get install Slic3r python python-serial git
	@echo "Grabbing CherryPy Library.."
	@wget https://pypi.python.org/packages/source/C/CherryPy/CherryPy-3.8.0.tar.gz
	@echo "Unzipping CherryPy.."
	@tar -xzf CherryPy-3.8.0.tar.gz
	@echo "Installing CherryPy.."
	cd ./CherryPy-3.8.0 && sudo python setup.py install
	@echo "Removing garbage.."
	sudo rm -f CherryPy-3.8.0.tar.gz
	sudo rm -rf CherryPy-3.8.0
	@echo "Done."

install:

