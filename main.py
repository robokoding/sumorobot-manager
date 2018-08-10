#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

"""
SumoManager

Manager different functions on the
RoboKoding SumoRobots.

Author: RoboKoding LTD
Website: https://www.robokoding.com
Contact: info@robokoding.com
"""

# python imports
import os
import sys
import json
import time
import argparse
import urllib.request
import serial.tools.list_ports

# Local lib imports
from lib.files import Files
from lib.pyboard import Pyboard
from lib.esptool import ESPLoader
from lib.esptool import write_flash
from lib.esptool import flash_size_bytes

# pyqt imports
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# App name
APP_NAME = 'SumoManager v0.5'

# Firmware URLs
MICROPYTHON_URL = 'https://micropython.org/download'
SUMOFIRMWARE_URL = 'https://raw.githubusercontent.com/robokoding/sumorobot-firmware/master/'

# Define the resource path
RESOURCE_PATH = 'res'
if hasattr(sys, '_MEIPASS'):
    RESOURCE_PATH = os.path.join(sys._MEIPASS, RESOURCE_PATH)

# Resource URLs
USB_IMG = os.path.join(RESOURCE_PATH, 'usb.png')
SUMO_IMG = os.path.join(RESOURCE_PATH, 'sumologo.svg')
ORBITRON_FONT = os.path.join(RESOURCE_PATH, 'orbitron.ttf')
USB_CONNECTED_IMG = os.path.join(RESOURCE_PATH, 'usb_connected.png')

class SumoManager(QMainWindow):
    usb_dcon = pyqtSignal()
    usb_con = pyqtSignal(str)
    usb_list = pyqtSignal(list)
    message = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.initUI()

        self.connected_port = None
        self.update_firmware = False
        self.update_config = False

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
        self.serial_image.setPixmap(QPixmap(USB_IMG))

        # WiFi credentials fields
        wifi_label = QLabel('2. Enter WiFi credentials')
        wifi_label.setStyleSheet('margin-top: 20px;')
        self.wifi_select = QComboBox()
        self.wifi_select.addItems(['Network name'])
        self.wifi_select.setEnabled(False)
        self.wifi_pwd_edit = QLineEdit()
        self.wifi_pwd_edit.setPlaceholderText("Password")

        # WiFi add button
        self.add_wifi_btn = QPushButton('Add WiFi network', self)
        self.add_wifi_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.add_wifi_btn.clicked.connect(self.button_clicked)

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
        # Update firmware menu
        update_firmware = QAction('Update Firmware', self)
        update_firmware.triggered.connect(self.update_firmware)
        file_menu.addAction(update_firmware)

        # Add the statusbar into a toolbar
        toolbar = self.addToolBar("Main")
        self.statusBar = QStatusBar()
        toolbar.addWidget(self.statusBar)
        self.show_message('warning', 'Please connect your SumoRobot')

        # Main window style, layout and position
        with open(os.path.join(RESOURCE_PATH, 'main.qss'), 'r') as file:
            self.setStyleSheet(file.read())
        self.setWindowTitle(APP_NAME)
        self.setCentralWidget(main_widget)
        self.show()
        self.center()

    # Function to center the mainwindow on the screen
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        print(qr.topLeft())
        self.move(qr.topLeft())

    @pyqtSlot(str, str)
    def show_message(self, type, message):
        if type == 'error':
            style = 'color: #d9534f;'
        elif type == 'warning':
            style = 'color: #f0ad4e;'
        elif type == 'info':
            style = 'color: #5cb85c;'
        else: # Unrecognized message type
            return

        self.statusBar.setStyleSheet(style)
        self.statusBar.showMessage(message)

    # Button clicked event
    def button_clicked(self):
        # When button disabled or SumoRobot is not connected
        if self.update_config or not self.connected_port:
            return

        # When the network name is not valid
        if self.wifi_select.currentText() == 'Network name':
            # Show the error
            self.wifi_select.setStyleSheet('background-color: #d9534f;')
            return
        else: # When the network name is valid, remove the error
            self.wifi_select.setStyleSheet('background: rgba(212,212,255,0.035);')

        # Disable adding another network until the current one is added
        self.update_config = True

    # When mouse clicked clear the focus on the input fields
    def mousePressEvent(self, event):
        self.wifi_select.clearFocus()
        self.wifi_pwd_edit.clearFocus()

    @pyqtSlot()
    @pyqtSlot(str)
    @pyqtSlot(list)
    def usb_action(self, data = None):
        if isinstance(data, list):
            self.wifi_select.clear()
            self.wifi_select.addItems(data)
            self.wifi_select.setEnabled(True)
            self.show_message('info', 'Successfuly loaded WiFi networks')
            self.wifi_select.setStyleSheet('background: #2d3252;')
        elif isinstance(data, str):
            self.serial_image.setPixmap(QPixmap(USB_CONNECTED_IMG))
            self.show_message('warning', 'Loading Wifi netwroks...')
        else:
            self.connected_port = None
            self.serial_image.setPixmap(QPixmap(USB_IMG))
            self.show_message('warning', 'Please connect your SumoRobot')

    def update_firmware(self, event):
        # When SumoRobot is connected and update config is not running
        if window.connected_port and not window.update_config:
            # Start the update firmware process
            self.update_firmware = True

class UpdateFirmware(QThread):
    def run(self):
        while True:
            # Wait until update firmware is triggered
            if not window.update_firmware:
                time.sleep(1)
                continue

            window.message.emit('warning', 'Updating firmware...')
            try:
                # Open and parse the MicroPython URL
                response = urllib.request.urlopen(MICROPYTHON_URL)
                line = response.readline()
                while line:
                    # Find the firmware binary URL
                    if b'firmware/esp32' in line:
                        firmware_url = line.split(b'"')[1]
                        break
                    line = response.readline()

                window.message.emit('warning', 'Downloading firmware... esp32.bin')
                # Open the parsed firmware binary URL
                response = urllib.request.urlopen(firmware_url.decode('utf-8'))
                # Write the firmware binary into a local file
                temp_file = QTemporaryFile()
                temp_file.open()
                temp_file.writeData(response.read())
                temp_file.flush()

                # Firmware files to update
                file_names = ['uwebsockets.py', 'config.json', 'hal.py', 'main.py', 'boot.py']
                data = dict.fromkeys(file_names)

                for file in file_names:
                    window.message.emit('warning', 'Downloading firmware... ' + file)
                    # Fetch the file from the Internet
                    response = urllib.request.urlopen(SUMOFIRMWARE_URL + file)
                    data[file] = response.read()

                esp = ESPLoader.detect_chip(window.connected_port)
                esp.run_stub()
                esp.IS_STUB = True
                esp.change_baud(460800)
                esp.STATUS_BYTES_LENGTH = 2
                esp.flash_set_parameters(flash_size_bytes('4MB'))
                esp.FLASH_WRITE_SIZE = 0x4000
                esp.ESP_FLASH_DEFL_BEGIN = 0x10
                window.message.emit('warning', 'Uploading firmware... esp32.bin')
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
                print("Closing port")
                esp._port.close()

                # Open the serial port
                board = Files(Pyboard(window.connected_port, rawdelay=0.5))

                for file in file_names:
                    window.message.emit('warning', 'Uploading firmware... ' + file)
                    # Update file
                    board.put(file, data[file])

                # Close serial port
                board.close()

                window.message.emit('info', 'Successfully updated firmware')
            except:
                window.message.emit('error', 'Failed to update firmware')

            # Stop the update thread
            window.update_firmware = False

class UpdateConfig(QThread):
    def run(self):
        while True:
            # Wait until update config is triggered
            if not window.update_config:
                time.sleep(1)
                continue

            window.message.emit('warning', 'Adding WiFi credentials...')
            try:
                # Get the text from the input fields
                ssid = window.wifi_select.currentText()
                pwd = window.wifi_pwd_edit.text()
                # Open the serial port
                board = Files(Pyboard(window.connected_port, rawdelay=0.5))
                # Try to read and parse config file
                config = json.loads(board.get('config.json'))
                # Add the WiFi credentials
                config['wifis'][ssid] = pwd
                # Convert the json object into a string
                config = json.dumps(config, indent = 8)
                # Write the updates config file
                board.put('config.json', config)
                # Close serial
                board.close()
                # Initiate another connection to reset the board
                # TODO: implement more elegantly
                board = Files(Pyboard(window.connected_port, rawdelay=0.5))
                board.close()
                window.message.emit('info', 'Successfully added WiFi credentials')
            except:
                window.message.emit('error', 'Failed to read config file')

            # Enable the WiFi add button
            window.update_config = False

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
                if '1A86:' in p.hwid:
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
                    # Close the serial connection
                    board.close()
                    # Emit a signal to populate networks
                    window.usb_list.emit(networks)
                except:
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
    window.usb_con.connect(window.usb_action)
    window.usb_dcon.connect(window.usb_action)
    window.usb_list.connect(window.usb_action)
    window.message.connect(window.show_message)

    # Start port update thread
    port_update = PortUpdate()
    port_update.start()

    # Start the update config thread
    update_config = UpdateConfig()
    update_config.start()

    # Start the update firmware thread
    update_firmware = UpdateFirmware()
    update_firmware.start()

    # Launch application
    sys.exit(app.exec_())
