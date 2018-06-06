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

# local imports
from lib.files import Files
from lib.pyboard import Pyboard

# pyqt imports
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# version
VERSION = " v0.3"

# define the resource path
RESOURCE_PATH = 'res'
if hasattr(sys, '_MEIPASS'):
    RESOURCE_PATH = os.path.join(sys._MEIPASS, RESOURCE_PATH)

class SumoManager(QMainWindow):
    selectedSerialport = ''
    addWifiDisabled = False

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # load the Orbitron font
        QFontDatabase.addApplicationFont(os.path.join(RESOURCE_PATH, 'orbitron.ttf'))

        # logo
        logoLabel = QLabel()
        logoLabel.setPixmap(QPixmap(os.path.join(RESOURCE_PATH, 'sumologo.svg')))
        logoLabel.setAlignment(Qt.AlignCenter)

        # serial port selection field
        serialNoticeLabel = QLabel('1. Connect SumoRobot via USB')
        serialNoticeLabel.setStyleSheet('margin-top: 20px;')
        # update serial ports every X seconds
        self.serialport = QLabel()
        self.serialport.setPixmap(QPixmap(os.path.join(RESOURCE_PATH, 'usb.png')))

        # WiFi credentials fields
        wifiLabel = QLabel('2. Enter WiFi credentials')
        wifiLabel.setStyleSheet('margin-top: 20px;')
        self.wifiNameEdit = QLineEdit()
        self.wifiNameEdit.setPlaceholderText("Network")
        self.wifiPwdEdit = QLineEdit()
        self.wifiPwdEdit.setPlaceholderText("Password")

        # WiFi add button
        addWifiLabel = QLabel('3. Click add Wifi network')
        addWifiLabel.setStyleSheet('margin-top: 20px;')
        self.addWifiBtn = QPushButton('Add WiFi network', self)
        self.addWifiBtn.setCursor(QCursor(Qt.PointingHandCursor))
        self.addWifiBtn.clicked.connect(self.buttonClicked)

        # vertical app layout
        vbox = QVBoxLayout()
        vbox.addWidget(logoLabel)
        vbox.addWidget(serialNoticeLabel)
        vbox.addWidget(self.serialport)
        vbox.addWidget(wifiLabel)
        vbox.addWidget(self.wifiNameEdit)
        vbox.addWidget(self.wifiPwdEdit)
        vbox.addWidget(addWifiLabel)
        vbox.addWidget(self.addWifiBtn)
        # wrap the layout into a widget
        mainWidget = QWidget()
        mainWidget.setLayout(vbox)

        # show a blank message to expand the window
        self.showMessage('info', '')

        # main window style, layout and position
        with open(os.path.join(RESOURCE_PATH, 'main.qss'), 'r') as file:
            self.setStyleSheet(file.read())
        self.setWindowTitle('SumoManager' + VERSION)
        self.setCentralWidget(mainWidget)
        self.show()
        self.center()

    # function to center the mainwindow on the screen
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        print(qr.topLeft())
        self.move(qr.topLeft())

    def showMessage(self, type, message):
        if type == 'error':
            self.statusBar().setStyleSheet('color: #d9534f; background: rgba(212,212,255,0.035); font-family: Orbitron;')
        elif type == 'warning':
            self.statusBar().setStyleSheet('color: #f0ad4e; background: rgba(212,212,255,0.035); font-family: Orbitron;')
        elif type == 'info':
            self.statusBar().setStyleSheet('color: #5cb85c; background: rgba(212,212,255,0.035); font-family: Orbitron;')
        else:
            # unrecognized message type
            return
        self.statusBar().showMessage(message)

    # button clicked event
    def buttonClicked(self):
        port = self.selectedSerialport
        ssid = self.wifiNameEdit.text()
        pwd = self.wifiPwdEdit.text()

        # when button disabled
        if self.addWifiDisabled:
            return
        # when ESP not connected
        if port == '':
            return
        # when the network name is not valid
        if ssid == '':
            # show the error
            self.wifiNameEdit.setStyleSheet('background-color: #d9534f;')
            return
        # when the network name is valid
        else:
            # remove the error
            self.wifiNameEdit.setStyleSheet('background: rgba(212,212,255,0.035);')

        # disable the button
        self.addWifiDisabled = True
        # show the user feedback that we started to add the network
        self.showMessage('info', 'Adding WiFi credentials ...')

        # function to update the config file on the ESP
        def updateConfig():
            # open the serial port
            board = Files(Pyboard(port))

            tries = 5
            config = ''
            # while we have the config
            while not config:
                # only try X times
                if tries == 0:
                    self.showMessage('error', 'Failed to read config file')
                    return
                # try to read and parse config file
                try:
                    config = json.loads(board.get('config.json'))
                    if config:
                        # add the WiFi credentials
                        config['wifis'][ssid] = pwd
                        # convert the json object into a string
                        config = json.dumps(config, indent = 8)
                        # write the updates config file
                        board.put('config.json', config)
                except:
                    pass
                # one less try
                tries -= 1
                # wait before trying again
                time.sleep(1)

            # enable the button
            self.addWifiDisabled = False
            # should improve to signals and slots
            self.statusBar().showMessage('WiFi credentials successfully added')

        # start the config update thread
        _thread.start_new_thread(updateConfig, ())

    # when mouse clicked clear the focus on the input fields
    def mousePressEvent(self, event):
        self.wifiNameEdit.clearFocus()
        self.wifiPwdEdit.clearFocus()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # for high dpi displays
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    # create the app main window
    window = SumoManager()

    # to update serialport status
    def updateSerialport():
        # scan the serialports with specific vendor ID
        for port in serial.tools.list_ports.comports():
            if '1A86:' in port.hwid:
                # only update if port has changed
                if window.selectedSerialport != port.device:
                    window.selectedSerialport = port.device
                    window.showMessage('info', 'SumoRobot connected')
                    window.serialport.setPixmap(QPixmap(os.path.join(RESOURCE_PATH, 'usb_connected.png')))
                # only add the first found serialport
                return

        # when no serial port with the specific vendor ID was found
        window.selectedSerialport = ''
        window.serialport.setPixmap(QPixmap(os.path.join(RESOURCE_PATH, 'usb.png')))
        window.showMessage('warning', 'Please connect your SumoRobot')

    # update serial port status every X second
    timer = QTimer()
    timer.timeout.connect(updateSerialport)
    timer.start(1000)

    sys.exit(app.exec_())
