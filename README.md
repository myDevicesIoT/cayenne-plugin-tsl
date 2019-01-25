# Cayenne TSL Plugin
A plugin allowing the [Cayenne Pi Agent](https://github.com/myDevicesIoT/Cayenne-Agent) to read data from TSL light sensors (TSL2561, TSL2561T, TSL2561CS, TSL4531, TSL45311, TSL45313, TSL45317) and display it in the [Cayenne Dashboard](https://cayenne.mydevices.com).

## Requirements
### Hardware
* [Rasberry Pi](https://www.raspberrypi.org).
* An TSL light sensor, e.g. [TSL2561](https://www.adafruit.com/product/439)

### Software
* [Cayenne Pi Agent](https://github.com/myDevicesIoT/Cayenne-Agent). This can be installed from the [Cayenne Dashboard](https://cayenne.mydevices.com).
* [Git](https://git-scm.com/).

## Getting Started

### 1. Installation

   From the command line run the following commands to install this plugin.
   ```
   cd /etc/myDevices/plugins
   sudo git clone https://github.com/myDevicesIoT/cayenne-plugin-tsl.git
   ```

### 2. Setting the device class

   Specify the device you are using by setting the `class` value under the `TSL Luminosity` section in the `cayenne-tsl.plugin` file.
   By default this is set to `TSL2561` but it can be set to use any of the classes in the `cayenne_tsl` module.

### 3. Restarting the agent

   Restart the agent so it can load the plugin.
   ```
   sudo service myDevices restart
   ```
   Temporary widgets for the plugin should now show up in the [Cayenne Dashboard](https://cayenne.mydevices.com). You can make them permanent by clicking the plus sign.

   NOTE: If the temporary widgets do not show up try refreshing the [Cayenne Dashboard](https://cayenne.mydevices.com) or restarting the agent again using `sudo service myDevices restart`.