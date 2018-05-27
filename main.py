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

# define the resource path
RESOURCE_PATH = 'res'
if hasattr(sys, '_MEIPASS'):
    RESOURCE_PATH = os.path.join(sys._MEIPASS, RESOURCE_PATH)

class SumoManager(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # load the Orbitron font
        QFontDatabase.addApplicationFont(os.path.join(RESOURCE_PATH, 'orbitron.ttf'))
        # message label
        self.messageLabel = QLabel()
        # logo
        logoLabel = QLabel()
        logoLabel.setPixmap(QPixmap(os.path.join(RESOURCE_PATH, 'sumologo.svg')))
        logoLabel.setAlignment(Qt.AlignCenter)

        # serial port selection field
        serialLabel = QLabel('1. Select serial port')
        # update serial ports every X seconds
        self.serialBox = QComboBox()

        # WiFi credentials fields
        wifiLabel = QLabel('2. Enter WiFi credentials')
        self.wifiNameEdit = QLineEdit()
        self.wifiNameEdit.setPlaceholderText("WiFi SSID")
        self.wifiPwdEdit = QLineEdit()
        self.wifiPwdEdit.setPlaceholderText("WiFi Password")

        # WiFi add button
        addWifiLabel = QLabel('3. Click add Wifi network')
        addWifiBtn = QPushButton('Add WiFi network', self)
        addWifiBtn.setCursor(QCursor(Qt.PointingHandCursor))
        addWifiBtn.clicked.connect(self.buttonClicked)

        # app layout
        vbox = QVBoxLayout()
        vbox.addWidget(logoLabel)
        vbox.addWidget(self.messageLabel)
        vbox.addWidget(serialLabel)
        vbox.addWidget(self.serialBox)
        vbox.addWidget(wifiLabel)
        vbox.addWidget(self.wifiNameEdit)
        vbox.addWidget(self.wifiPwdEdit)
        vbox.addWidget(addWifiLabel)
        vbox.addWidget(addWifiBtn)

        # main window style, layout and position
        with open(os.path.join(RESOURCE_PATH, 'main.qss'), 'r') as file:
            self.setStyleSheet(file.read())
        self.setWindowTitle('SumoManager')
        self.setLayout(vbox)
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
            self.messageLabel.setStyleSheet('QLabel {color:#d9534f}')
        elif type == 'warning':
            self.messageLabel.setStyleSheet('QLabel {color:#f0ad4e;}')
        elif type == 'info':
            self.messageLabel.setStyleSheet('QLabel {color:#5cb85c;}')
        else:
            # unrecognized message type
            return
        self.messageLabel.setText(message)

    # button clicked event
    def buttonClicked(self):
        port = self.serialBox.currentText()
        ssid = self.wifiNameEdit.text()
        pwd = self.wifiPwdEdit.text()

        # check the input fields and give the user feedback
        if port == '':
            self.serialBox.setStyleSheet('background-color: #d9534f;')
            return
        else:
            self.serialBox.setStyleSheet('background: rgba(212,212,255,0.035);')
        if ssid == '':
            self.wifiNameEdit.setStyleSheet('background-color: #d9534f;')
            return
        else:
            self.wifiNameEdit.setStyleSheet('background: rgba(212,212,255,0.035);')

        self.showMessage('info', 'Adding WiFi credentials ...')

        def updateConfig():
            # open the serial port
            board = Files(Pyboard(port))
            # get the config file
            config = json.loads(board.get('config.json'))
            # add the WiFi credentials
            config['wifis'][ssid] = pwd
            # convert the json object into a string
            config = json.dumps(config, indent = 8)
            # write the updates config file
            board.put('config.json', config)
            self.showMessage('info', 'WiFi credentials successfully added')
        _thread.start_new_thread(updateConfig, ())

    # when mouse clicked clear the focus on the input fields
    def mousePressEvent(self, event):
        focused_widget = QApplication.focusWidget()
        self.wifiNameEdit.clearFocus()
        self.wifiPwdEdit.clearFocus()
        self.serialBox.clearFocus()
        QMainWindow.mousePressEvent(self, event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SumoManager()

    serialPorts = []
    removeWarning = False
    def updateSerialBox():
        global serialPorts
        global removeWarning
        # clear the serial ports
        ex.serialBox.clear()
        # scan the serial ports and add them to the combobox
        for port in serial.tools.list_ports.comports():
            ex.serialBox.addItem(port.device)
        # when there are no serial ports connected
        if len(serial.tools.list_ports.comports()) == 0:
            ex.showMessage('warning', 'Please connect your SumoRobot')
            removeWarning = True
        elif removeWarning:
            ex.serialBox.setStyleSheet('background: rgba(212,212,255,0.035);')
            ex.showMessage('warning', '')
            removeWarning = False

    # update serial ports every X second
    timer = QTimer()
    timer.timeout.connect(updateSerialBox)
    timer.start(1000)

    sys.exit(app.exec_())
