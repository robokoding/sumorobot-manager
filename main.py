#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

"""
SumoManager

Manage different functions on the
RoboKoding SumoRobots.

Author: RoboKoding LTD
Website: https://www.robokoding.com
Contact: support@robokoding.com
"""

# python imports
import os
import sys
import json
import time
import string
import secrets
import argparse
import traceback
import urllib.request
import serial.tools.list_ports

# Local lib imports
from lib.esptool import *
from lib.files import Files
from lib.pyboard import Pyboard

# pyqt imports
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

# App name
APP_NAME = 'SumoManager v0.6.1'

# Firmware URLs, file names
MICROPYTHON_URL = 'http://micropython.org/download'
FIRMWARE_FILE_NAMES = ['uwebsockets.py', 'config.json', 'hal.py', 'main.py', 'boot.py']
SUMOFIRMWARE_URL = 'https://raw.githubusercontent.com/robokoding/sumorobot-firmware/master/'

# Define the resource path
RESOURCE_PATH = 'res'
if hasattr(sys, '_MEIPASS'):
    RESOURCE_PATH = os.path.join(sys._MEIPASS, RESOURCE_PATH)

# Resource URLs
SUMO_IMG = os.path.join(RESOURCE_PATH, 'sumologo.svg')
USB_CON_IMG = os.path.join(RESOURCE_PATH, 'usb_con.png')
USB_DCON_IMG = os.path.join(RESOURCE_PATH, 'usb_dcon.png')
ORBITRON_FONT = os.path.join(RESOURCE_PATH, 'orbitron.ttf')

class SumoManager(QMainWindow):
    usb_dcon = pyqtSignal()
    usb_con = pyqtSignal(str)
    usb_list = pyqtSignal(list)
    message = pyqtSignal(str, str)
    dialog = pyqtSignal(str, str, str)

    def __init__(self):
        super().__init__()
        self.initUI()

        self.config = None
        self.processing = None
        self.connected_port = None

    def initUI(self):
        # Load the Orbitron font
        QFontDatabase.addApplicationFont(ORBITRON_FONT)

        # SumoRobot Logo
        logo_label = QLabel()
        logo_label.setPixmap(QPixmap(SUMO_IMG))
        logo_label.setAlignment(Qt.AlignCenter)

        # Serial port connection indication
        serial_label = QLabel('1. Connect SumoRobot via USB')
        serial_label.setStyleSheet('margin-top: 20px;')
        self.serial_image = QLabel()
        self.serial_image.setPixmap(QPixmap(USB_DCON_IMG))

        # WiFi credentials fields
        wifi_label = QLabel('2. Enter WiFi credentials')
        wifi_label.setStyleSheet('margin-top: 20px;')
        self.wifi_select = QComboBox()
        self.wifi_select.addItems(['Network name'])
        self.wifi_select.setEnabled(False)
        self.wifi_pwd_edit = QLineEdit()
        self.wifi_pwd_edit.setEchoMode(QLineEdit.Password)
        self.wifi_pwd_edit.setPlaceholderText("Password")

        # WiFi add button
        self.add_wifi_btn = QPushButton('Add WiFi network', self)
        self.add_wifi_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.add_wifi_btn.clicked.connect(self.button_clicked)
        self.wifi_pwd_edit.returnPressed.connect(self.button_clicked)

        # Add the statusbar into a toolbar
        self.tool_bar = self.addToolBar('Main')
        self.status_bar = QStatusBar()
        self.tool_bar.addWidget(self.status_bar)
        self.show_message('warning', 'Please connect your SumoRobot')

        # Vertical app layout
        vbox = QVBoxLayout()
        vbox.addWidget(logo_label)
        vbox.addWidget(serial_label)
        vbox.addWidget(self.serial_image)
        vbox.addWidget(wifi_label)
        vbox.addWidget(self.wifi_select)
        vbox.addWidget(self.wifi_pwd_edit)
        vbox.addWidget(self.add_wifi_btn)
        # Wrap the layout into a widget
        main_widget = QWidget()
        main_widget.setLayout(vbox)

        # Add menubar items
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        # Update robot ID menu item
        update_id = QAction('Update SumoID', self)
        update_id.triggered.connect(self.update_id)
        file_menu.addAction(update_id)
        # Show config menu item
        show_config = QAction('Show SumoConfig', self)
        show_config.triggered.connect(self.show_config)
        file_menu.addAction(show_config)
        # Update firmware menu item
        update_firmware = QAction('Update SumoFirmware', self)
        update_firmware.triggered.connect(self.update_firmware)
        file_menu.addAction(update_firmware)

        # Main window style, layout and position
        with open(os.path.join(RESOURCE_PATH, 'main.qss'), 'r') as file:
            self.setStyleSheet(file.read())
        self.setWindowTitle(APP_NAME)
        self.setCentralWidget(main_widget)
        self.show()
        self.center()
        # To lose focus on the textedit field
        self.setFocus()

    # Function to center the mainwindow on the screen
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    @pyqtSlot(str, str)
    def show_message(self, type, message):
        if type == 'error':
            style = 'color: #d63634;'
        elif type == 'warning':
            style = 'color: #e77e34;'
        elif type == 'info':
            style = 'color: #1cc761;'
        else: # Unrecognized message type
            return

        self.status_bar.setStyleSheet(style)
        self.status_bar.showMessage(message)

    @pyqtSlot()
    @pyqtSlot(str)
    @pyqtSlot(list)
    def usb_action(self, data = None):
        if isinstance(data, list):
            self.wifi_select.clear()
            self.wifi_select.addItems(data)
            self.wifi_select.setEnabled(True)
            self.show_message('info', 'Successfuly loaded WiFi networks')
            self.wifi_select.setStyleSheet('background-color: #2d3252;')
        elif isinstance(data, str):
            self.serial_image.setPixmap(QPixmap(USB_CON_IMG))
            self.show_message('warning', 'Loading Wifi netwroks...')
        else:
            self.connected_port = None
            self.serial_image.setPixmap(QPixmap(USB_DCON_IMG))
            self.show_message('warning', 'Please connect your SumoRobot')

    @pyqtSlot(str, str, str)
    def show_dialog(self, title, message, details):
        msg_box = QMessageBox()
        msg_box.setDetailedText(details)
        msg_box.setWindowTitle('Message')
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setStandardButtons(QMessageBox.Close)
        msg_box.setText("<font face=Orbitron>" + title + "</font>")
        msg_box.setInformativeText("<font size=4>" + message + "</font>")
        horizontalSpacer = QSpacerItem(500, 0, QSizePolicy.Minimum, QSizePolicy.Expanding);
        layout = msg_box.layout();
        layout.addItem(horizontalSpacer, layout.rowCount(), 0, 1, layout.columnCount());
        msg_box.exec_()

    # When mouse clicked clear the focus on the input fields
    def mousePressEvent(self, event):
        # When the status bar is pressed
        self.wifi_pwd_edit.clearFocus()

    # Button clicked event
    def button_clicked(self):
        # When some thread is already processing SumoRobot is not connected
        if self.processing or not self.connected_port:
            return

        # When the network name is not valid
        if self.wifi_select.currentText() == 'Network name':
            # Show the error
            self.wifi_select.setStyleSheet('background-color: #d9534f;')
            return
        else: # When the network name is valid, remove the error
            self.wifi_select.setStyleSheet('background-color: #2d3252;')

        # To lose focus on the text edit field
        self.setFocus()
        # Indicates a background thread process
        self.processing = "update_networks"

    def update_firmware(self, event):
        # When SumoRobot is connected and update config nor update firmware is running
        if self.connected_port and not self.processing:
            # Start the update firmware process
            self.processing = "update_firmware"

    def show_config(self, event):
        if self.connected_port and not self.processing:
            self.show_dialog('SumoConfig',
                'Click Show Details... to see the SumoConfig contents',
                json.dumps(self.config, indent=8))

    def update_id(self, event):
        if self.connected_port and not self.processing:
            # Start the update ID process
            self.processing = "update_id"

class UpdateID(QThread):
    def run(self):
        while True:
            # Wait until update ID process is triggered
            if window.processing != "update_id":
                time.sleep(1)
                continue

            window.message.emit('warning', 'Updating SumoID...')
            try:
                # Save the random ID on the SumoRobot
                board = Files(Pyboard(window.connected_port, rawdelay=0.5))
                # Generate a new random robot ID
                random = ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(8))
                window.config['sumo_id'] = random
                # Save the robot ID
                temp = json.dumps(window.config, indent=8)
                board.put('config.json', temp)
                board.close()
                window.message.emit('info', 'Successfully updated SumoID')
                window.dialog.emit('New SumoID',
                    'Click Show Details... to see your new SumoID. Keep it secret and ' +
                    'change it when it has been exposed.', random)
            except:
                # Close the serial port
                board.close()
                window.dialog.emit('Error updating SumoID',
                    '* Try reconnecting the SumoRobot USB cable<br>' +
                    '* Try updating SumoID again', traceback.format_exc())
                window.message.emit('error', 'Error updating SumoID')

            # Indicate that no process is running
            window.processing = None


class UpdateFirmware(QThread):
    def run(self):
        while True:
            # Wait until update firmware process is triggered
            if window.processing != "update_firmware":
                time.sleep(1)
                continue

            window.message.emit('warning', 'Updating SumoFirmware...')
            try:
                esp = None
                board = None
                # Open and parse the MicroPython URL
                response = urllib.request.urlopen(MICROPYTHON_URL)
                line = response.readline()
                while line:
                    # Find the firmware binary URL
                    if b'firmware/esp32' in line:
                        firmware_url = line.split(b'"')[1]
                        break
                    line = response.readline()

                window.message.emit('warning', 'Downloading SumoFirmware... esp32.bin')
                # Open the parsed firmware binary URL
                response = urllib.request.urlopen(firmware_url.decode('utf-8'))
                # Write the firmware binary into a local file
                temp_file = QTemporaryFile()
                temp_file.open()
                temp_file.writeData(response.read())
                temp_file.flush()

                # Firmware files to update
                data = dict.fromkeys(FIRMWARE_FILE_NAMES)

                # Download all firmware files
                for file_name in FIRMWARE_FILE_NAMES:
                    window.message.emit('warning', 'Downloading SumoFirmware... ' + file_name)
                    # Fetch the file from the Internet
                    response = urllib.request.urlopen(SUMOFIRMWARE_URL + file_name)
                    data[file_name] = response.read()

                # In case the user has a personalized config file
                if window.config:
                    # Transfer the personalized values
                    tmp_config = json.loads(data['config.json'])
                    tmp_config['wifis'] = window.config['wifis']
                    tmp_config['sumo_id'] = window.config['sumo_id']
                    #tmp_config['sumo_server'] = window.config['sumo_server']
                    tmp_config['status_led_pin'] = window.config['status_led_pin']
                    tmp_config['ultrasonic_distance'] = window.config['ultrasonic_distance']
                    data['config.json'] = json.dumps(tmp_config, indent=8)
                # In case it's the default config file
                else:
                    # Generate a random robot ID
                    random = ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(8))
                    window.config = json.loads(data['config.json'])
                    window.config['sumo_id'] = random
                    data['config.json'] = json.dumps(window.config, indent=8)

                esp = ESPLoader.detect_chip(window.connected_port)
                esp.run_stub()
                esp.IS_STUB = True
                esp.change_baud(460800)
                esp.STATUS_BYTES_LENGTH = 2
                erase_flash(esp, None)
                esp.flash_set_parameters(flash_size_bytes('4MB'))
                esp.FLASH_WRITE_SIZE = 0x4000
                esp.ESP_FLASH_DEFL_BEGIN = 0x10
                window.message.emit('warning', 'Uploading SumoFirmware... esp32.bin')
                write_flash(esp, argparse.Namespace(
                    addr_filename=[(4096, open(temp_file.fileName(), 'rb'))],
                    verify=False,
                    compress=None,
                    no_stub=False,
                    flash_mode='dio',
                    flash_size='4MB',
                    flash_freq='keep',
                    no_compress=False))
                esp.hard_reset()
                esp._port.close()

                # Open the serial port
                board = Files(Pyboard(window.connected_port, rawdelay=0.5))

                # Go trough all the files
                for file_name in FIRMWARE_FILE_NAMES:
                    window.message.emit('warning', 'Uploading SumoFirmware... ' + file_name)
                    # Update file
                    board.put(file_name, data[file_name])

                # Close serial port
                board.close()
                window.message.emit('info', 'Successfully updated SumoFirmware')
                # Try to laod WiFi networks again
                window.connected_port = None
            except:
                # Close the serial ports if open
                if esp:
                    esp._port.close()
                if board:
                    board.close()
                window.dialog.emit('Error updating SumoFirmware',
                    '* Try reconnecting the SumoRobot USB cable<br>' +
                    '* Check your Internet connection<br>' +
                    '* Finally try updating SumoFirmware again',
                    traceback.format_exc())
                window.message.emit('error', 'Error updating SumoFirmware')

            # Indicate that no process is running
            window.processing = None

class UpdateNetworks(QThread):
    def run(self):
        while True:
            # Wait until update networks process is triggered
            if window.processing != "update_networks":
                time.sleep(1)
                continue

            window.message.emit('warning', 'Adding WiFi credentials...')
            try:
                # Open the serial port
                board = Files(Pyboard(window.connected_port, rawdelay=0.5))
                # Get the text from the input fields
                ssid = window.wifi_select.currentText()
                pwd = window.wifi_pwd_edit.text()
                # Add the WiFi credentials
                window.config['wifis'][ssid] = pwd
                # Convert the json object into a string
                temp = json.dumps(window.config, indent = 8)
                # Write the updates config file
                board.put('config.json', temp)
                # Close the serial connection
                board.close()
                # Initiate another connection to reset the board
                # TODO: implement more elegantly
                board = Files(Pyboard(window.connected_port, rawdelay=0.5))
                board.close()
                window.message.emit('info', 'Successfully added WiFi credentials')
                window.dialog.emit('Successfully added WiFi credentials',
                    '<p>Now turn the robot on and remove the USB cable. Wait for ' +
                    'the blue LED under the robot to be steady ON (SumoRobot is ' +
                    'successfully connected to the server). To see your SumoID ' +
                    'click Show Details... Keep the SumoID secret and change it ' +
                    'when exposed, from File > Update SumoID. Now you can head' +
                    'over to the SumoInterface:</p>' +
                    '<a href="http://sumo.robokoding.com">sumo.robokoding.com</a>' +
                    '<p>For further info about the SumoInterface head over to:</p>' +
                    '<a href="https://wwww.robokoding.com/kits/sumorobot/sumointerface"' +
                    '>wwww.robokoding.com/kits/sumorobot/sumointerface</a>',
                    window.config['sumo_id'])
            except:
                # Close the serial connection
                board.close()
                window.dialog.emit('Error adding WiFi credentials',
                    '* Try reconnecting the SumoRobot USB cable<br>' +
                    '* Try adding WiFi credentials again<br>', +
                    '* When nothing helped, try File > Update SumoFirmware',
                    traceback.format_exc())
                window.message.emit('error', 'Error adding WiFi credentials')

            # Indicate that no process is running
            window.processing = None

class PortUpdate(QThread):
    # To update serialport status
    def run(self):
        while True:
            # Wait for a second to pass
            time.sleep(1)

            port = None
            # Scan the serialports with specific vendor ID
            # TODO: implement with USB event
            for p in serial.tools.list_ports.comports():
                # When vendor ID was found
                if '1A86:' in p.hwid or '10C4:' in p.hwid:
                    port = p.device
                    break

            # When specific vendor ID was found and it's a new port
            if port and port != window.connected_port:
                window.usb_con.emit(port)
                try:
                    # Initiate a serial connection
                    board = Files(Pyboard(port, rawdelay=0.5))
                    # Get the Wifi networks in range
                    networks = board.get_networks()
                    # Delay before next read
                    time.sleep(0.5)
                    # Get the config file
                    if not window.config:
                        window.config = json.loads(board.get('config.json'))
                    # Close the serial connection
                    board.close()
                    # Emit a signal to populate networks
                    window.usb_list.emit(networks)
                except:
                    # Close the serial connection
                    board.close()
                    window.dialog.emit('Error loading WiFi networks',
                        '* Try reconnecting the SumoRobot USB cable<br>' +
                        '* Try updating SumoFirmware File > Update SumoFirmware (close this dialog first)',
                        traceback.format_exc())
                    window.message.emit('error', 'Error loading WiFi networks')

                window.connected_port = port
            # When no serial port with the specific vendor ID was found
            elif not port:
                window.usb_dcon.emit()

if __name__ == '__main__':
    # Initiate application
    app = QApplication(sys.argv)

    # For high dpi displays
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app.setAttribute(Qt.AA_EnableHighDpiScaling)

    # Create the app main window
    window = SumoManager()
    # Connect signals to slots
    window.dialog.connect(window.show_dialog)
    window.usb_con.connect(window.usb_action)
    window.usb_dcon.connect(window.usb_action)
    window.usb_list.connect(window.usb_action)
    window.message.connect(window.show_message)

    # Start port update thread
    port_update = PortUpdate()
    port_update.start()

    # Start the update config thread
    update_networks = UpdateNetworks()
    update_networks.start()

    # Start the update firmware thread
    update_firmware = UpdateFirmware()
    update_firmware.start()

    # Start update ID thread
    update_id = UpdateID()
    update_id.start()

    # Launch application
    sys.exit(app.exec_())
