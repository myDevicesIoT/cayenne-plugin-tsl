#   Copyright 2013 - 2015 Andreas Riegg - t-h-i-n-x.net
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#
#   Changelog
#
#   1.0    2013/02/28    Initial release
#   1.1    2014/04/03    Fixed issue 90, applied same update to _set_time
#                        Corrected typo channel1value to channel1_value
#                        Corrected typo channelRatio to channel_ratio
#                        Moved robustness checks to avoid division by zero
#   1.2    2015/09/09    Fixed issue with no-IR reading (channel 1 value = 0)
#                        
"""
This module provides a class for interfacing with TSL sensors.
"""
from myDevices.devices.i2c import I2C
from myDevices.utils.logger import info


class TSL_LIGHT_X(I2C):
    """Base class for interacting with TSL devices."""
    VAL_COMMAND = 0x80
    REG_CONTROL = 0x00 | VAL_COMMAND
    REG_CONFIG  = 0x01 | VAL_COMMAND

    VAL_PWON    = 0x03
    VAL_PWOFF   = 0x00
    VAL_INVALID = -1
    
    LUX_VALUE   = 0

    def __init__(self, slave, time):
        """Initializes TSL device.

        Arguments:
        slave: The slave address
        time: Integration time
        """      
        I2C.__init__(self, int(slave))
        self.wake() # devices are powered down after power reset, wake them
        self.set_time(int(time))

    def __str__(self):
        """Returns friendly name."""
        return "%s(slave=0x%02X)" % (self.__class__.__name__, self.slave)

    def wake(self):
        """Wake the device."""
        self.writeRegister(self.REG_CONTROL, self.VAL_PWON)

    def sleep(self):
        """Power down the device."""
        self.writeRegister(self.REG_CONTROL, self.VAL_PWOFF)
        
    def set_time(self, time):
        """Set the integration time."""
        self._set_time(time)

    def get_time(self):
        """Get the integration time."""
        return self._get_time()


class TSL2561X(TSL_LIGHT_X):
    """Class for interacting with a TSL2561X device."""
    VAL_TIME_402_MS   = 0x02
    VAL_TIME_101_MS   = 0x01
    VAL_TIME_14_MS    = 0x00
        
    REG_CHANNEL_0_LOW = 0x0C | TSL_LIGHT_X.VAL_COMMAND
    REG_CHANNEL_1_LOW = 0x0E | TSL_LIGHT_X.VAL_COMMAND
    
    MASK_GAIN         = 0x10
    MASK_TIME         = 0x03
  
    def __init__(self, slave, time, gain):
        """Initializes TSL2561X device.

        Arguments:
        slave: The slave address
        time: Integration time
        gain: Sensor gain
        """      
        TSL_LIGHT_X.__init__(self, slave, time)             
        self.set_gain(int(gain))

    def get_lux(self):
        """Gets the luminosity as a tuple with type and unit."""
        ch0_bytes = self.readRegisters(self.REG_CHANNEL_0_LOW, 2)
        ch1_bytes = self.readRegisters(self.REG_CHANNEL_1_LOW, 2)
        ch0_word = ch0_bytes[1] << 8 | ch0_bytes[0]
        ch1_word = ch1_bytes[1] << 8 | ch1_bytes[0]
        scaling = self.time_multiplier * self.gain_multiplier
        value = self._calculate_lux(scaling * ch0_word, scaling * ch1_word)
        if value != self.VAL_INVALID:
            self.LUX_VALUE = value
        return (float('{0:.1f}'.format(self.LUX_VALUE)), 'lum', 'lux')

    def set_gain(self, gain):
        """Set the sensor gain."""
        if gain == 1:
            bit_gain = 0
            self.gain_multiplier = 16
        elif gain == 16:
            bit_gain = 1
            self.gain_multiplier = 1
        else:
            raise ValueError("Gain %d out of range [%d,%d]" % (gain, 1, 16))
        new_byte_gain = (bit_gain << 4) & self.MASK_GAIN       
        current_byte_config = self.readRegister(self.REG_CONFIG)
        new_byte_config = (current_byte_config & ~self.MASK_GAIN) | new_byte_gain
        self.writeRegister(self.REG_CONFIG, new_byte_config)
    
    def get_gain(self):
        """Get the sensor gain."""
        current_byte_config = self.readRegister(self.REG_CONFIG)
        if (current_byte_config & self.MASK_GAIN):
            return 16
        else:
            return 1

    def _set_time(self, time):
        """Set the integration time."""
        if not time in [14, 101, 402]:
            raise ValueError("Time %d out of range [%d,%d,%d]" % (time, 14, 101, 402))
        if time == 402:
            bits_time = self.VAL_TIME_402_MS
            self.time_multiplier = 1
        elif time == 101:
            bits_time = self.VAL_TIME_101_MS
            self.time_multiplier = 322 / 81.0
        elif time == 14:
            bits_time = self.VAL_TIME_14_MS
            self.time_multiplier = 322 / 11.0
        new_byte_time = bits_time & self.MASK_TIME
        current_byte_config = self.readRegister(self.REG_CONFIG)
        new_byte_config = (current_byte_config & ~self.MASK_TIME) | new_byte_time
        self.writeRegister(self.REG_CONFIG, new_byte_config)
        
    def _get_time(self):
        """Get the integration time."""
        current_byte_config = self.readRegister(self.REG_CONFIG)
        bits_time = (current_byte_config & self.MASK_TIME)
        if bits_time == self.VAL_TIME_402_MS:
            t = 402
        elif bits_time == self.VAL_TIME_101_MS:
            t = 101
        elif bits_time == self.VAL_TIME_14_MS:
            t =  14
        else:
            t = TSL_LIGHT_X.VAL_INVALID # indicates undefined
        return t


class TSL2561CS(TSL2561X):
    """Class for interacting with a TSL2561CS device."""
    # Package CS (Chipscale) chip version

    def __init__(self, slave=0x39, time=402,  gain=1):
        """Initializes TSL2561CS device.

        Arguments:
        slave: The slave address
        time: Integration time
        gain: Sensor gain
        """  
        TSL2561X.__init__(self, slave, time, gain)

    def _calculate_lux(self, channel0_value, channel1_value):
        """Calculate the luminosity in lux."""
        if float(channel0_value) == 0.0:      # driver robustness, avoid division by zero
            return self.VAL_INVALID

        channel_ratio = channel1_value / float(channel0_value)
        if 0 <= channel_ratio <= 0.52:
            lux = 0.0315 * channel0_value - 0.0593 * channel0_value *(channel_ratio**1.4)
        elif 0.52 < channel_ratio <= 0.65:
            lux = 0.0229 * channel0_value - 0.0291 * channel1_value
        elif 0.65 < channel_ratio <= 0.80:
            lux = 0.0157 * channel0_value - 0.0180 * channel1_value
        elif 0.80 < channel_ratio <= 1.30:
            lux = 0.00338 * channel0_value - 0.00260 * channel1_value
        else: # if channel_ratio > 1.30
            lux = 0
        return lux


class TSL2561T(TSL2561X):
    """Class for interacting with a TSL2561T device."""
    # Package T (TMB-6)  chip version

    def __init__(self, slave=0x39, time=402, gain=1):
        """Initializes TSL2561T device.

        Arguments:
        slave: The slave address
        time: Integration time
        gain: Sensor gain
        """      
        TSL2561X.__init__(self, slave, time, gain)
        
    def _calculate_lux(self, channel0_value, channel1_value):
        """Calculate the luminosity in lux."""
        if float(channel0_value) == 0.0:      # driver robustness, avoid division by zero
            return self.VAL_INVALID

        channel_ratio = channel1_value / float(channel0_value)
        if 0 <= channel_ratio <= 0.50:
            lux = 0.0304 * channel0_value - 0.062 * channel0_value * (channel_ratio**1.4)
        elif 0.50 < channel_ratio <= 0.61:
            lux = 0.0224 * channel0_value - 0.031 * channel1_value
        elif 0.61 < channel_ratio <= 0.80:
            lux = 0.0128 * channel0_value - 0.0153 * channel1_value
        elif 0.80 < channel_ratio <= 1.30:
            lux = 0.00146 * channel0_value - 0.00112 * channel1_value
        else: # if channel_ratio > 1.30
            lux = 0
        return lux


class TSL2561(TSL2561T):
    """Class for interacting with a TSL2561 device."""
    # Default version for unknown packages, uses T Package class lux calculation

    def __init__(self, slave=0x39, time=402, gain=1):
        """Initializes TSL2561 device.

        Arguments:
        slave: The slave address
        time: Integration time
        gain: Sensor gain
        """      
        TSL2561X.__init__(self, slave, time, gain)
        
        
class TSL4531(TSL_LIGHT_X):
    """Class for interacting with a TSL4531 device."""
    # Default version for unknown subtypes, uses 0x29 as slave address
    VAL_TIME_400_MS = 0x00
    VAL_TIME_200_MS = 0x01
    VAL_TIME_100_MS = 0x02

    REG_DATA_LOW    = 0x04 | TSL_LIGHT_X.VAL_COMMAND
    
    MASK_TCNTRL     = 0x03

    def __init__(self, slave=0x29, time=400):
        """Initializes TSL4531 device.

        Arguments:
        slave: The slave address
        time: Integration time
        """      
        TSL_LIGHT_X.__init__(self, slave, time)
        
    def _set_time(self, time):
        """Set the integration time."""
        if not time in [100, 200, 400]:
            raise ValueError("Time %d out of range [%d,%d,%d]" % (time, 100, 200, 400))
        if time == 400:
            bits_time = self.VAL_TIME_400_MS
            self.time_multiplier = 1
        elif time == 200:
            bits_time = self.VAL_TIME_200_MS
            self.time_multiplier = 2
        elif time == 100:
            bits_time = self.VAL_TIME_100_MS
            self.time_multiplier = 4            
        new_byte_time = bits_time & self.MASK_TCNTRL

        current_byte_config = self.readRegister(self.REG_CONFIG)
        new_byte_config = (current_byte_config & ~self.MASK_TCNTRL) | new_byte_time
        self.writeRegister(self.REG_CONFIG, new_byte_config)

    def _get_time(self):
        """Get the integration time."""
        current_byte_config =  self.readRegister(self.REG_CONFIG)
        bits_time = (current_byte_config & self.MASK_TCNTRL)
        if bits_time == self.VAL_TIME_400_MS:
            t = 400
        elif bits_time == self.VAL_TIME_200_MS:
            t = 200
        elif bits_time == self.VAL_TIME_100_MS:
            t = 100
        else:
            t = TSL_LIGHT_X.VAL_INVALID # indicates undefined
        return t

    def get_lux(self):
        data_bytes = self.readRegisters(self.REG_DATA_LOW, 2)
        return (self.time_multiplier * (data_bytes[1] << 8 | data_bytes[0]), 'lum', 'lux')


class TSL45311(TSL4531):
    """Class for interacting with a TSL45311 device."""

    def __init__(self, slave=0x39, time=400):
        """Initializes TSL45311 device.

        Arguments:
        slave: The slave address
        time: Integration time
        """      
        TSL4531.__init__(self, slave, time)


class TSL45313(TSL4531):
    """Class for interacting with a TSL45313 device."""

    def __init__(self, slave=0x39, time=400):
        """Initializes TSL45313 device.

        Arguments:
        slave: The slave address
        time: Integration time
        """      
        TSL4531.__init__(self, slave, time)


class TSL45315(TSL4531):
    """Class for interacting with a TSL45315 device."""

    def __init__(self, slave=0x29, time=400):
        """Initializes TSL45315 device.

        Arguments:
        slave: The slave address
        time: Integration time
        """      
        TSL4531.__init__(self, slave, time)


class TSL45317(TSL4531):
    """Class for interacting with a TSL45317 device."""
    
    def __init__(self, slave=0x29, time=400):
        """Initializes HYTXXX device.

        Arguments:
        slave: The slave address
        time: Integration time
        """        
        TSL4531.__init__(self, slave, time)


class TSL2561Test(TSL2561):
    """Class for simulating a TSL2561 device."""

    def __init__(self):
        """Initializes the test class."""
        self.registers = {self.REG_CHANNEL_0_LOW: bytes([0x5C, 0x0B]), self.REG_CHANNEL_1_LOW: bytes([0xD7, 0x02]),}
        TSL2561.__init__(self)

    def readRegister(self, addr):
        """Read value from a register."""
        if addr not in self.registers:
            self.registers[addr] = 0
        return self.registers[addr]

    def readRegisters(self, addr, size):
        """Read value from a register."""
        if addr not in self.registers:
            self.registers[addr] = bytes(size)
        return self.registers[addr]

    def writeRegister(self, addr, value):
        """Write value to a register."""
        self.registers[addr] = value

    def writeRegisters(self, addr, value):
        """Write value to a register."""
        self.registers[addr] = value        