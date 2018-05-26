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
import serial.tools.list_ports

# pyqt imports
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# define the resource path
RESOURCE_PATH = 'resources'
if hasattr(sys, '_MEIPASS'):
    RESOURCE_PATH = os.path.join(sys._MEIPASS, RESOURCE_PATH)

class SumoManager(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        QFontDatabase.addApplicationFont(os.path.join(RESOURCE_PATH, 'orbitron.ttf'))
        # message
        self.messageLabel = QLabel()
        # logo
        logoLabel = QLabel()
        logoLabel.setPixmap(QPixmap(os.path.join(RESOURCE_PATH, 'sumologo.svg')))
        logoLabel.setAlignment(Qt.AlignCenter)

        # serial port selection field
        serialLabel = QLabel('1. Select serial port')
        serialLabel.setStyleSheet('QLabel {color: white;}')
        serialLabel.setFont(QFont('Orbitron', 15))
        self.serialBox = QComboBox()
        # scan the serial ports and add them to the combobox
        for port in serial.tools.list_ports.comports():
            self.serialBox.addItem(port.device)
        self.serialBox.setFont(QFont('Orbitron', 15))

        # WiFi credentials fields
        wifiLabel = QLabel('2. Enter WiFi credentials')
        wifiLabel.setStyleSheet('QLabel {color: white;}')
        wifiLabel.setFont(QFont('Orbitron', 15))
        self.wifiNameEdit = QLineEdit()
        self.wifiNameEdit.setPlaceholderText("WiFi SSID")
        self.wifiNameEdit.setFont(QFont('Orbitron', 15))
        self.wifiPwdEdit = QLineEdit()
        self.wifiPwdEdit.setPlaceholderText("WiFi Password")
        self.wifiPwdEdit.setFont(QFont('Orbitron', 15))

        # WiFi add button
        addWifiLabel = QLabel('3. Click add Wifi network')
        addWifiLabel.setStyleSheet('QLabel {color: white;}')
        addWifiLabel.setFont(QFont('Orbitron', 15))
        addWifiBtn = QPushButton('Add WiFi network', self)
        addWifiBtn.setCursor(QCursor(Qt.PointingHandCursor))
        addWifiBtn.setFont(QFont('Orbitron', 15))
        addWifiBtn.clicked.connect(self.buttonClicked)

        # app layout
        vbox = QVBoxLayout()
        vbox.addWidget(self.messageLabel)
        vbox.addWidget(logoLabel)
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

    # button clicked event
    def buttonClicked(self):
        ssid = self.wifiNameEdit.text()
        pwd = self.wifiPwdEdit.text()
        port = self.serialBox.currentText()
        if os.system('ampy -p ' + port + ' get config.json > /tmp/config.json') != 0:
            print('ampy failed to execute')
            return
        with open('/tmp/config.json', 'r') as file:
            config = json.load(file)
        config['wifis'][ssid] = pwd
        with open('/tmp/config.json', 'w') as file:
            json.dump(config, file, indent = 8)
        os.system('ampy -p ' + port + ' put /tmp/config.json')
        self.messageLabel.setText("WiFi credentials successfully added")


    def mousePressEvent(self, event):
        focused_widget = QApplication.focusWidget()
        if isinstance(focused_widget, QLineEdit):
            self.wifiNameEdit.clearFocus()
            self.wifiPwdEdit.clearFocus()
        QMainWindow.mousePressEvent(self, event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SumoManager()
    sys.exit(app.exec_())
