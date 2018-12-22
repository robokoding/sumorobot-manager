linux:
	pyinstaller main.py --onefile --name SumoManager --add-data 'res:res'
windows:
	pyinstaller main.py --onefile --name SumoManager --windowed --icon res/sumologo.ico --add-data 'res;res'
macos:
	rm -rf dist/ build/
	pyinstaller main.py --name SumoManager --windowed --icon res/sumologo.icns --add-data 'res:res'
