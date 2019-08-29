UNAME := $(shell uname)

# only linux needs sudo to clean dist dir
ifeq ($(UNAME), Linux)
	SUDO = sudo
endif

clean:
	$(SUDO) rm -rf build/ dist/

linux: clean
	pyinstaller main.py --onefile --name sumomanager --add-data res:res
	mkdir -p dist/SumoManager/DEBIAN
	mkdir -p dist/SumoManager/usr/bin
	mkdir -p dist/SumoManager/usr/share/applications
	mkdir -p dist/SumoManager/usr/share/icons/hicolor/512x512/apps
	cp res/sumologo.png dist/SumoManager/usr/share/icons/hicolor/512x512/apps/
	cp res/sumomanager.desktop dist/SumoManager/usr/share/applications/
	cp dist/sumomanager dist/SumoManager/usr/bin/
	cp res/control dist/SumoManager/DEBIAN/
	sudo chown root:root -R dist/SumoManager
	sudo chmod 0755 dist/SumoManager/usr/bin/sumomanager
	dpkg -b dist/SumoManager

windows: clean
	pyinstaller main.py --onefile --name SumoManager --windowed --icon res\sumologo.ico --add-data res;res

macos: clean
	pyinstaller main.py --name SumoManager --windowed --icon res/sumologo.icns --add-data res:res
