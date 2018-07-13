#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

"""
This program manages robokoding
SumoRobots.

Author: RoboKoding LTD
Website: https://www.robokoding.com
Last edited: 18th May 2018
"""

# python imports
import os
import sys
import json
import time
import serial
import _thread
import serial.tools.list_ports

# Local imports
from lib.files import Files
from lib.pyboard import Pyboard

# pyqt imports
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Version
VERSION = " v0.3"

# Define the resource path
RESOURCE_PATH = 'res'
if hasattr(sys, '_MEIPASS'):
    RESOURCE_PATH = os.path.join(sys._MEIPASS, RESOURCE_PATH)

class SumoManager(QMainWindow):
    selected_port = ''
    add_wifi_disabled = False

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Load the Orbitron font
        QFontDatabase.addApplicationFont(os.path.join(RESOURCE_PATH, 'orbitron.ttf'))

        # SumoRobot Logo
        logo_label = QLabel()
        logo_label.setPixmap(QPixmap(os.path.join(RESOURCE_PATH, 'sumologo.svg')))
        logo_label.setAlignment(Qt.AlignCenter)

        # Serial port connection indication
        serial_label = QLabel('1. Connect SumoRobot via USB')
        serial_label.setStyleSheet('margin-top: 20px;')
        self.serial_image = QLabel()
        self.serial_image.setPixmap(QPixmap(os.path.join(RESOURCE_PATH, 'usb.png')))

        # WiFi credentials fields
        wifi_label = QLabel('2. Enter WiFi credentials')
        wifi_label.setStyleSheet('margin-top: 20px;')
        self.wifi_select = QComboBox()
        self.wifi_select.addItems(['Network name'])
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

        # Show a blank message to expand the window
        self.show_message('info', '')

        # Main window style, layout and position
        with open(os.path.join(RESOURCE_PATH, 'main.qss'), 'r') as file:
            self.setStyleSheet(file.read())
        self.setWindowTitle('SumoManager' + VERSION)
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

    def show_message(self, type, message):
        if type == 'error':
            self.statusBar().setStyleSheet('color: #d9534f; background: rgba(212,212,255,0.035); font-family: Orbitron;')
        elif type == 'warning':
            self.statusBar().setStyleSheet('color: #f0ad4e; background: rgba(212,212,255,0.035); font-family: Orbitron;')
        elif type == 'info':
            self.statusBar().setStyleSheet('color: #5cb85c; background: rgba(212,212,255,0.035); font-family: Orbitron;')
        else:
            # Unrecognized message type
            return
        self.statusBar().showMessage(message)

    # Button clicked event
    def button_clicked(self):
        ssid = self.wifi_select.currentText()
        pwd = self.wifi_pwd_edit.text()

        # When button disabled or SumoRobot is not connected
        if self.add_wifi_disabled or self.selected_port == '':
            return
        # When the network name is not valid
        if ssid == 'Network name':
            # Show the error
            self.wifi_select.setStyleSheet('background-color: #d9534f;')
            return
        # When the network name is valid
        else:
            # Remove the error
            self.wifi_select.setStyleSheet('background: rgba(212,212,255,0.035);')

        # Disable the button
        self.add_wifi_disabled = True
        # Show the user feedback that we started to add the network
        self.show_message('info', 'Adding WiFi credentials ...')

        # Function to update the config file on the ESP
        def update_config():
            # Open the serial port
            board = Files(Pyboard(self.selected_port))

            tries = 3
            # While we have tries left
            while True:
                # Try to read and parse config file
                try:
                    config = json.loads(board.get('config.json'))
                    if config:
                        # Add the WiFi credentials
                        config['wifis'][ssid] = pwd
                        # Convert the json object into a string
                        config = json.dumps(config, indent = 8)
                        # Write the updates config file
                        board.put('config.json', config)
                        # Reset to try to connect to WiFi
                        board.reset()
                        break
                except:
                    pass
                # One less try
                tries -= 1
                # When we run out of tries
                if tries == 0:
                    self.show_message('error', 'Failed to read config file')
                    return

            # Enable the button
            self.add_wifi_disabled = False
            # TODO: improve to signals and slots
            self.show_message('info', 'WiFi credentials successfully added')

        # Start the config update thread
        _thread.start_new_thread(update_config, ())

    # When mouse clicked clear the focus on the input fields
    def mousePressEvent(self, event):
        self.wifi_select.clearFocus()
        self.wifi_pwd_edit.clearFocus()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # For high dpi displays
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    # Create the app main window
    window = SumoManager()

    # To update serialport status
    def update_port():
        # Scan the serialports with specific vendor ID
        for port in serial.tools.list_ports.comports():
            if '1A86:' in port.hwid:
                # Only update if port has changed
                if window.selected_port != port.device:
                    window.selected_port = port.device
                    window.serial_image.setPixmap(QPixmap(os.path.join(RESOURCE_PATH, 'usb_connected.png')))
                    window.show_message('info', 'Loading WiFi networks...')
                    def update_networks():
                        board = Files(Pyboard(port.device, rawdelay=0.5))
                        networks = board.get_networks()
                        window.wifi_select.clear()
                        window.wifi_select.addItems(networks)
                        #window.show_message('info', 'WiFi networks loaded')
                    _thread.start_new_thread(update_networks, ())
                # Only add the first found serialport
                return

        # When no serial port with the specific vendor ID was found
        window.selected_port = ''
        window.serial_image.setPixmap(QPixmap(os.path.join(RESOURCE_PATH, 'usb.png')))
        window.show_message('warning', 'Please connect your SumoRobot')

    # Update serial port status every X second
    timer = QTimer()
    timer.timeout.connect(update_port)
    timer.start(1000)

    sys.exit(app.exec_())
