// This file is required by the index.html file and will
// be executed in the renderer process for that window.
// All of the Node.js APIs are available in this process.

const util = require('util');
const SerialPort = require('serialport');

/* Python code to read a file and output it to the serialport */
var read_config_file_script = 'import sys\r\n' +
'with open(\'config.json\', \'rb\') as infile:\r\n' +
    'while True:\r\n' +
        'result = infile.read(32)\r\n' +
        'len = sys.stdout.write(result)\r\n' +
        'if len == 0:\r\n' +
            'break\r\n\r\n\r\n\r\n';

/* Function to show messages to the user */
function showMessage(status, message) {
    /* Check for a valid status name */
    if (['error', 'info'].includes(status)) {
        document.getElementById(status).innerHTML = message;
    }
}

/* Function to make delay for given duration in milliseconds */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/*
 * serial port object info:
 * comName, manufacturer, serialNumber, pnpId, locationId, vendorId, productId
 */
/* Scan an show all discovered serial ports */
var serialPorts = [];
function showSerialPorts() {
    SerialPort.list((err, ports) => {
        /* When there was an error listing serial ports */
        if (err) {
            return showMessage('error', err.message);
        /* When no serial ports where discovered */
        } else if (ports.length === 0) {
            return showMessage('message', 'No ports discovered');
        }

        /* Get the serial port select element object */
        var select = document.getElementById('serialPortSelector');

        /* Populate all found serial ports */
        ports.forEach(function(port) {
            /* When given port name is not yet included */
            if (!serialPorts.includes(port.comName)) {
                var opt = port.comName;
                var el = document.createElement('option');
                el.textContent = opt;
                el.value = opt;
                select.appendChild(el);
                /* Add to the serialPorts list */
                serialPorts.push(port.comName);
            }
        });
    })
}

/* Click listener for the add wifi button */
document.getElementById('addWifiButton').addEventListener('click', async function() {
    /* Get the selected serialport name */
    var serilPortOption = document.getElementById('serialPortSelector');
    var serialPortName = serilPortOption.options[serilPortOption.selectedIndex].value;

    /* Extract the user inserted ssid and password */
    var ssid = document.getElementById('ssid').value;
    var password = document.getElementById('password').value;

    /* Open the selected serialport */
    var serial = new SerialPort(serialPortName, { baudRate: 115200 });

    /* To capture the received config file string */
    var configFileString = '';

    /* Receive serialport data */
    serial.on('data', async function(data) {
        var dataString = data.toString('ascii');
        showMessage('info', 'data: ' + dataString);
        /* If the JSON data starts or started */
        if (dataString.startsWith('{') || configFileString.length > 0) {
            /* Concatenate to the configFileString */
            configFileString += dataString;
            /* When the JSON data contains } and >, the whole JSON has been received */
            if (dataString.includes('}')) {
                /* Stop receiving serial data events */
                serial.pause();
                /* Concatenate to the configFileString, remove everything after the last } */
                var temp = configFileString.substring(0, configFileString.indexOf('>'));
                /* parse JSON, update WiFis and stingify */
                var configFileJson = JSON.parse(temp);
                configFileJson['wifis'][ssid] = password;
                var configToFile = JSON.stringify(configFileJson);

                /* Open file for writing */
                serial.write(new Buffer('f = open(\'config.json\', \'w\')\r\n'));
                /* Write the modified config back into the file on the ESP32 */
                for (i = 0; i < configToFile.length; i += 32) {
                    var slice = configToFile.slice(i, i + 32);
                    var temp = util.format('f.write(\'%s\')\r\n', slice);
                    serial.write(new Buffer(temp));
                    await sleep(100);
                }
                /* Close the file on the ESP32 */
                serial.write(new Buffer('f.close()\r\n'));
                await sleep(100);
                serial.close();

                showMessage('info', 'Wifi network added successfully!');
            }
        }
    });

    /* Wait until the system has finished outputing bootup logs */
    await sleep(1000);
    /* ctrl-C twice: interrupt any running program */
    serial.write(new Buffer([0x0D, 0x03, 0x03]));
    /* Flush input */
    //serial.flush();
    // TODO: investigate raw REPL mode
    /* ctrl-A: enter raw REPL */
    //serial.write(new Buffer([0x0D, 0x01]));
    /* Send the file read command */
    serial.write(new Buffer(read_config_file_script));
});

/* Show all discovered serial ports */
showSerialPorts();
/* Update serial ports after every X second */
setInterval(function() {
    showSerialPorts();
}, 3000);
