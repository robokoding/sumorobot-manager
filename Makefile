linux:
	pyinstaller main.py --onefile --name SumoManager --add-data 'res:res'
windows:
	pyinstaller main.py --onefile --name SumoManager --windowed --icon res/sumologo.ico --add-data 'res;res'
mac:
	pyinstaller main.py --onefile --name SumoManager --windowed --icon res/sumologo.icns --add-data 'res:res'
