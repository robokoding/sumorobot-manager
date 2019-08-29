#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
SumoManager

Manage different functions on the
RoboKoding SumoRobots.

Author: RoboKoding LTD
Website: https://www.robokoding.com
Contact: silver@robokoding.com
"""

# python imports
import os
import sys
import time
import argparse
import traceback
import urllib.request
import serial.tools.list_ports

# Local lib imports
from lib.esptool import *

# App versioning
APP_VERSION = '0.9.0'
APP_TIMESTAMP = '2019.08.14 14:20'

# App name
APP_NAME = 'SumoManager v' + APP_VERSION

# Ignore SSL
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# SumoFirmware and SumoManager repository URLs
SUMOMANAGER_URL = 'https://github.com/robokoding/sumorobot-manager/releases/latest/'
SUMOFIRMWARE_URL = 'https://github.com/robokoding/sumorobot-firmware/releases/latest/download/'

# Define the resource path
RESOURCE_PATH = 'res'
if hasattr(sys, '_MEIPASS'):
    RESOURCE_PATH = os.path.join(sys._MEIPASS, RESOURCE_PATH)
    os.environ['PATH'] = sys._MEIPASS + '\;' + os.environ.get('PATH', '')

# pyqt imports
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

# Resource URLs
SUMO_IMG = os.path.join(RESOURCE_PATH, 'sumologo.svg')
USB_CON_IMG = os.path.join(RESOURCE_PATH, 'usb_con.png')
USB_DCON_IMG = os.path.join(RESOURCE_PATH, 'usb_dcon.png')
ORBITRON_FONT = os.path.join(RESOURCE_PATH, 'orbitron.ttf')
BOOT_APP0_BIN = os.path.join(RESOURCE_PATH, 'boot_app0.bin')
BOOTLOADER_DIO_40M_BIN = os.path.join(RESOURCE_PATH, 'bootloader_dio_40m.bin')

class SumoManager(QMainWindow):
    usb_dcon = pyqtSignal()
    usb_con = pyqtSignal(str)
    message = pyqtSignal(str, str)
    dialog = pyqtSignal(str, str, str)

    def __init__(self):
        super().__init__()
        self.initUI()

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

        # SumoFirmware update label
        update_label = QLabel('2. Update SumoFirmware')
        update_label.setStyleSheet('margin-top: 20px;')

        # SumoFirmware update button
        self.update_btn = QPushButton('Update SumoFirmware', self)
        self.update_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.update_btn.clicked.connect(self.button_clicked)

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
        vbox.addWidget(update_label)
        vbox.addWidget(self.update_btn)
        # Wrap the layout into a widget
        main_widget = QWidget()
        main_widget.setLayout(vbox)

        # Add menubar items
        menubar = self.menuBar()
        file_menu = menubar.addMenu('SumoManager')
        # App info item
        app_info = QAction('About SumoManager', self)
        app_info.triggered.connect(self.app_info)
        file_menu.addAction(app_info)

        # Main window style, layout and position
        with open(os.path.join(RESOURCE_PATH, 'main.qss'), 'r') as file:
            self.setStyleSheet(file.read())
        self.setWindowTitle(APP_NAME)
        self.setCentralWidget(main_widget)
        self.setMinimumSize(400, 310)
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
    def usb_action(self, data = None):
        if data:
            self.serial_image.setPixmap(QPixmap(USB_CON_IMG))
            self.show_message('info', 'Successfully connected SumoRobot')
        else:
            self.connected_port = None
            self.serial_image.setPixmap(QPixmap(USB_DCON_IMG))
            self.show_message('warning', 'Please connect your SumoRobot')

    @pyqtSlot(str, str, str)
    def show_dialog(self, title, message, details):
        msg_box = QMessageBox()
        with open(os.path.join(RESOURCE_PATH, 'main.qss'), 'r') as file:
            msg_box.setStyleSheet(file.read())
        msg_box.setDetailedText(details)
        msg_box.setWindowTitle('Message')
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setStandardButtons(QMessageBox.Close)
        msg_box.setText(title)
        msg_box.setInformativeText('<font face=Arial>' + message + '</font>')
        horizontalSpacer = QSpacerItem(550, 0, QSizePolicy.Minimum, QSizePolicy.Expanding);
        layout = msg_box.layout();
        layout.addItem(horizontalSpacer, layout.rowCount(), 0, 1, layout.columnCount());
        msg_box.exec_()

    # Button clicked event
    def button_clicked(self):
        # When some thread is already processing SumoRobot is not connected
        if self.processing or not self.connected_port:
            return

        # Indicates a background thread process
        self.processing = 'update_firmware'

    def app_info(self, event):
        # Show app info dialog
        self.show_dialog('App info', 'Version: ' + APP_VERSION + '<br>' +
            'Timestamp: ' + APP_TIMESTAMP + '<br><br>' +
            'This is the SumoManager app. You can update the SumoFirmware of your ' +
            'SumoRobot with it. Please keep this app up to the date for the best possible experience.<br>', '')

    def update_firmware(self, event):
        # When SumoRobot is connected and update firmware is not running
        if self.connected_port and not self.processing:
            # Start the update firmware process
            self.processing = 'update_firmware'

class UpdateFirmware(QThread):
    def run(self):
        while True:
            # Wait until update firmware process is triggered
            if window.processing != 'update_firmware':
                time.sleep(1)
                continue

            window.message.emit('warning', 'Downloading SumoFirmware ...')
            try:
                # Open the firmware and parition binary URLs
                firmware_response = urllib.request.urlopen(SUMOFIRMWARE_URL + 'sumofirmware.bin')
                partitions_response = urllib.request.urlopen(SUMOFIRMWARE_URL + 'partitions.bin')

                # Write the firmware binary into a file
                firmware_file = QTemporaryFile()
                firmware_file.open()
                firmware_file.writeData(firmware_response.read())
                firmware_file.flush()

                # Write the parition binary into a file
                partitions_file = QTemporaryFile()
                partitions_file.open()
                partitions_file.writeData(partitions_response.read())
                partitions_file.flush()

                # Detect the ESP version
                esp = ESPLoader.detect_chip(window.connected_port)

                # Prepare for flashing
                esp.run_stub()
                esp.IS_STUB = True
                esp.change_baud(460800)
                esp.STATUS_BYTES_LENGTH = 2
                esp.flash_set_parameters(flash_size_bytes('4MB'))
                esp.FLASH_WRITE_SIZE = 0x4000
                esp.ESP_FLASH_DEFL_BEGIN = 0x10

                # Flash the latest MicroPython
                window.message.emit('warning', 'Flashing SumoFirmware ...')
                write_flash(esp, argparse.Namespace(
                    addr_filename=[(0x1000, open(BOOTLOADER_DIO_40M_BIN, 'rb'))],
                    verify=False,
                    compress=None,
                    no_stub=False,
                    erase_all=False,
                    flash_mode='dio',
                    flash_size='4MB',
                    flash_freq='keep',
                    no_compress=False))
                write_flash(esp, argparse.Namespace(
                    addr_filename=[(0x8000, open(partitions_file.fileName(), 'rb'))],
                    verify=False,
                    compress=None,
                    no_stub=False,
                    erase_all=False,
                    flash_mode='dio',
                    flash_size='4MB',
                    flash_freq='keep',
                    no_compress=False))
                write_flash(esp, argparse.Namespace(
                    addr_filename=[(0xe000, open(BOOT_APP0_BIN, 'rb'))],
                    verify=False,
                    compress=None,
                    no_stub=False,
                    erase_all=False,
                    flash_mode='dio',
                    flash_size='4MB',
                    flash_freq='keep',
                    no_compress=False))
                write_flash(esp, argparse.Namespace(
                    addr_filename=[(0x10000, open(firmware_file.fileName(), 'rb'))],
                    verify=False,
                    compress=None,
                    no_stub=False,
                    erase_all=False,
                    flash_mode='dio',
                    flash_size='4MB',
                    flash_freq='keep',
                    no_compress=False))
                esp.hard_reset()
                esp._port.close()

                # All done
                window.message.emit('info', 'Successfully updated SumoFirmware')
            except:
                window.dialog.emit('Error updating SumoFirmware',
                    '* Check your Internet connection<br>' +
                    '* Try reconnecting the SumoRobot USB cable<br>' +
                    '* Finally try Update SumoFirmware again',
                    traceback.format_exc())
                window.message.emit('error', 'Error updating SumoFirmware')

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
                # Different SumoRobot versions have a
                # different USB to UART IC hardware ID
                # Jiangsu Haoheng CH304 IC
                if '1A86:' in p.hwid or '10C4:' in p.hwid:
                    port = p.device
                    break

            # When specific vendor ID was found and it's a new port
            if port and port != window.connected_port:
                # Emit connection event
                window.usb_con.emit(port)

                window.connected_port = port
            # When no serial port with the specific vendor ID was found
            elif not port:
                window.usb_dcon.emit()

if __name__ == '__main__':
    # Initiate application
    app = QApplication(sys.argv)

    # Create the app main window
    window = SumoManager()
    # Connect signals to slots
    window.dialog.connect(window.show_dialog)
    window.usb_con.connect(window.usb_action)
    window.usb_dcon.connect(window.usb_action)
    window.message.connect(window.show_message)

    # Start port update thread
    port_update = PortUpdate()
    port_update.start()

    # Start the update firmware thread
    update_firmware = UpdateFirmware()
    update_firmware.start()

    # Check for a newer version of this application
    response = urllib.request.urlopen(SUMOMANAGER_URL)
    if APP_VERSION.encode() not in response.read():
        window.dialog.emit('Update SumoManager',
            'Please download the latest SumoManager application under the following link:<br>' +
            '<a style="color:white;cursor:pointer;" href="https://www.robokoding.com/kits/' +
            'sumorobot/sumomanager">https://www.robokoding.com/kits/sumorobot/sumomanager</a>', '')

    # Launch application
    sys.exit(app.exec_())
