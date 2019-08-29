UNAME := $(shell uname)

# clean is different for each distro
ifeq ($(OS),Windows_NT)
	CLEAN_CMD := @echo "no need to clean" 
else ifeq ($(UNAME),Darwin)
	CLEAN_CMD := rm -rf build/ dist/
else
	CLEAN_CMD := sudo rm -rf build/ dist/
endif

clean:
	$(CLEAN_CMD)

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
	pyinstaller main.py --onefile --name SumoManager --windowed --icon res\sumologo.ico --add-data res;res --add-data "%USERPROFILE%\AppData\Local\Programs\Python\Python37-32\Lib\site-packages\PyQt5\Qt\bin\Qt5Core.dll";. --add-data "%USERPROFILE%\AppData\Local\Programs\Python\Python37-32\Lib\site-packages\PyQt5\Qt\bin\Qt5Gui.dll";. --add-data "%USERPROFILE%\AppData\Local\Programs\Python\Python37-32\Lib\site-packages\PyQt5\Qt\bin\Qt5Widgets.dll";.

macos: clean
	pyinstaller main.py --name SumoManager --windowed --icon res/sumologo.icns --add-data res:res
	cp res/Info.plist dist/SumoManager.app/Contents/
	cd dist/ && create-dmg SumoManager.app
