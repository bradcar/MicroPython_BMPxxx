# SPDX-FileCopyrightText: Copyright (c) 2024 Bradley Robert Carlile
#
# SPDX-License-Identifier: MIT
# MIT License
# 
# Copyright (c) 2024 Bradley Robert Carlile
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE

"""
`bmp58x`
================================================================================

MicroPython Driver for the Bosch BMP585, BMP581, BMP390 pressure sensors

* Author: Brad Carlile

Based on

* micropython-bmp581/bmp581py. Author(s): Jose D. Montoya

"""

from micropython import const
from micropython_bmp58x.i2c_helpers import CBits, RegisterStruct

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/bradcar/MicroPython_BMP58x.git"


WORLD_AVERAGE_SEA_LEVEL_PRESSURE = 1013.25  # International average standard

class BMP581:
    """Driver for the BMP585 Sensor connected over I2C.

    :param ~machine.I2C i2c: The I2C bus the BMP581 is connected to.
    :param int address: The I2C device address. Default :const:`0x47`, Secondary :const:`0x46`

    :raises RuntimeError: if the sensor is not found

    **Quickstart: Importing and using the device**

    Here is an example of using the :class:`BMP581` class.
    First you will need to import the libraries to use the sensor

    .. code-block:: python

        from machine import Pin, I2C
        from micropython_bmp58x import bmp58x

    Once this is done you can define your `machine.I2C` object and define your sensor object

    .. code-block:: python

        i2c = I2C(1, sda=Pin(2), scl=Pin(3))
        bmp = bmp58x.BMP581(i2c)

    Now you have access to the attributes

    .. code-block:: python

        press = bmp.pressure
        temp = bmp.temperature

        # altitude in meters based on sea level pressure of 1013.25 hPA
        meters = bmp.altitude
        print(f"alt = {meters:.2f} meters")

        # set sea level pressure to a known sea level pressure in hPa at nearest airport
        # https://www.weather.gov/wrh/timeseries?site=KPDX
        bmp.sea_level_pressure = 1010.80
        meters = bmp.altitude
        print(f"alt = {meters:.2f} meters")

        # Highest resolution for bmp581
        bmp.pressure_oversample_rate = bmp.OSR128
        bmp.temperature_oversample_rate = bmp.OSR8
        meters = bmp.altitude

    """

    # Power Modes for BMP581
    # in the BMP390 there is only SLEEP(aka STANDBY), FORCED, NORMAL
    STANDBY = const(0x00)
    NORMAL = const(0x01)
    FORCED = const(0x02)
    NON_STOP = const(0x03)
    power_mode_values = (STANDBY, NORMAL, FORCED, NON_STOP)

    # Oversample Rate
    OSR1 = const(0x00)
    OSR2 = const(0x01)
    OSR4 = const(0x02)
    OSR8 = const(0x03)
    OSR16 = const(0x04)
    OSR32 = const(0x05)
    OSR64 = const(0x06)
    OSR128 = const(0x07)

    # oversampling rates
    pressure_oversample_rate_values = (OSR1, OSR2, OSR4, OSR8, OSR16, OSR32, OSR64, OSR128)
    temperature_oversample_rate_values = (OSR1, OSR2, OSR4, OSR8, OSR16, OSR32, OSR64, OSR128)

    # IIR Filters Coefficients
    COEF_0 = const(0x00)
    COEF_1 = const(0x01)
    COEF_3 = const(0x02)
    COEF_7 = const(0x03)
    COEF_15 = const(0x04)
    COEF_31 = const(0x05)
    COEF_63 = const(0x06)
    COEF_127 = const(0x07)
    iir_coefficient_values = (COEF_0, COEF_1, COEF_3, COEF_7, COEF_15, COEF_31, COEF_63, COEF_127)
    
    BMP581_I2C_ADDRESS_DEFAULT = 0x47
    BMP581_I2C_ADDRESS_SECONDARY = 0x46

    _REG_WHOAMI = const(0x01)
    _OSR_CONF = const(0x36)
    _ODR_CONFIG = const(0x37)

    _device_id = RegisterStruct(_REG_WHOAMI, "B")
    _power_mode = CBits(2, _ODR_CONFIG, 0)
    _temperature_oversample_rate = CBits(3, _OSR_CONF, 0)
    _pressure_oversample_rate = CBits(3, _OSR_CONF, 3)
    _output_data_rate = CBits(5, _ODR_CONFIG, 2)
    _pressure_enabled = CBits(1, _OSR_CONF, 6)

    _temperature = CBits(24, 0x1D, 0, 3)
    _pressure = CBits(24, 0x20, 0, 3)

    def __init__(self, i2c, address: int = None) -> None:
        # If no address is provided, try the default, then secondary
        if address is None:
            if self._check_address(i2c, self.BMP581_I2C_ADDRESS_DEFAULT):
                address = self.BMP581_I2C_ADDRESS_DEFAULT
            elif self._check_address(i2c, self.BMP581_I2C_ADDRESS_SECONDARY):
                address = self.BMP581_I2C_ADDRESS_SECONDARY
            else:
                raise RuntimeError("BMP581 sensor not found at known I2C address (0x47,0x46).")
        self._i2c = i2c
        self._address = address
        if self._read_device_id() != 0x50:  #check _device_id after i2c established
            raise RuntimeError("Failed to find the BMP581 sensor")
        self._power_mode = NORMAL
        self._pressure_enabled = True
        self.sea_level_pressure = WORLD_AVERAGE_SEA_LEVEL_PRESSURE
    
    def _read_device_id(self) -> int:
        return self._device_id
        
    @property
    def power_mode(self) -> str:
        """
        Sensor power_mode
        +-----------------------------+------------------+
        | Mode                        | Value            |
        +=============================+==================+
        | :py:const:`bmp581.STANDBY`  | :py:const:`0x00` |
        | :py:const:`bmp581.NORMAL`   | :py:const:`0x01` |
        | :py:const:`bmp581.FORCED`   | :py:const:`0x02` |
        | :py:const:`bmp581.NON_STOP` | :py:const:`0X03` |
        +-----------------------------+------------------+
        """
        values = ("STANDBY","NORMAL","FORCED","NON_STOP",)
        return values[self._power_mode]

    @power_mode.setter
    def power_mode(self, value: int) -> None:
        if value not in power_mode_values:
            raise ValueError("Value must be a valid power_mode setting")
        ("Value must be a valid power_mode setting: STANDBY,NORMAL,FORCED,NON_STOP")
        self._power_mode = value

    @property
    def pressure_oversample_rate(self) -> str:
        """
        Sensor pressure_oversample_rate
        Oversampling extends the measurement time per measurement by the oversampling
        factor. Higher oversampling factors offer decreased noise at the cost of
        higher power consumption.
        +---------------------------+------------------+
        | Mode                      | Value            |
        +===========================+==================+
        | :py:const:`bmp58x.OSR1`   | :py:const:`0x00` |
        | :py:const:`bmp58x.OSR2`   | :py:const:`0x01` |
        | :py:const:`bmp58x.OSR4`   | :py:const:`0x02` |
        | :py:const:`bmp58x.OSR8`   | :py:const:`0x03` |
        | :py:const:`bmp58x.OSR16`  | :py:const:`0x04` |
        | :py:const:`bmp58x.OSR32`  | :py:const:`0x05` |
        | :py:const:`bmp58x.OSR64`  | :py:const:`0x06` |
        | :py:const:`bmp58x.OSR128` | :py:const:`0x07` |
        +---------------------------+------------------+
        :return: sampling rate as string
        """
        string_name = ("OSR1", "OSR2", "OSR4", "OSR8", "OSR16", "OSR32", "OSR64", "OSR128",)
        return string_name[self._pressure_oversample_rate]

    @pressure_oversample_rate.setter
    def pressure_oversample_rate(self, value: int) -> None:
        if value not in self.pressure_oversample_rate_values:
            raise ValueError(
                "Value must be a valid pressure_oversample_rate: OSR1,OSR2,OSR4,OSR8,OSR16,OSR32,OSR64,OSR128")
        self._pressure_oversample_rate = value

    @property
    def temperature_oversample_rate(self) -> str:
        """
        Sensor temperature_oversample_rate
        +---------------------------+------------------+
        | Mode                      | Value            |
        +===========================+==================+
        | :py:const:`bmp58x.OSR1`   | :py:const:`0x00` |
        | :py:const:`bmp58x.OSR2`   | :py:const:`0x01` |
        | :py:const:`bmp58x.OSR4`   | :py:const:`0x02` |
        | :py:const:`bmp58x.OSR8`   | :py:const:`0x03` |
        | :py:const:`bmp58x.OSR16`  | :py:const:`0x04` |
        | :py:const:`bmp58x.OSR32`  | :py:const:`0x05` |
        | :py:const:`bmp58x.OSR64`  | :py:const:`0x06` |
        | :py:const:`bmp58x.OSR128` | :py:const:`0x07` |
        +---------------------------+------------------+
        :return: sampling rate as string
        """
        string_name = ("OSR1", "OSR2", "OSR4", "OSR8", "OSR16", "OSR32", "OSR64", "OSR128",)
        return string_name[self._temperature_oversample_rate]

    @temperature_oversample_rate.setter
    def temperature_oversample_rate(self, value: int) -> None:
        if value not in self.temperature_oversample_rate_values:
            raise ValueError(
                "Value must be a valid temperature_oversample_rate: OSR1,OSR2,OSR4,OSR8,OSR16,OSR32,OSR64,OSR128")
        self._temperature_oversample_rate = value
        
    @property
    def temperature(self) -> float:
        """
        The temperature sensor in Celsius
        :return: Temperature in Celsius
        """
        raw_temp = self._temperature
        return self._twos_comp(raw_temp, 24) / 2.0**16

    @property
    def pressure(self) -> float:
        """
        The sensor pressure in hPa
        :return: Pressure in hPa
        """
        raw_pressure = self._pressure
        return self._twos_comp(raw_pressure, 24) / 2.0**6 / 100.0

    @property
    def altitude(self) -> float:
        """
        Using the sensor's measured pressure and the pressure at sea level (e.g., 1013.25 hPa),
        the altitude in meters is calculated with the international barometric formula
        """
        altitude = 44330.0 * (
                1.0 - ((self.pressure / self.sea_level_pressure) ** (1.0 / 5.255))
        )
        return round(altitude, 1)

    @altitude.setter
    def altitude(self, value: float) -> None:
        self.sea_level_pressure = self.pressure / (1.0 - value / 44330.0) ** 5.255

    @property
    def sea_level_pressure(self) -> float:
        """
        Returns the current sea-level pressure set for the sensor in hPa.
        :return: Sea-level pressure in hPa
        """
        return self._sea_level_pressure

    @sea_level_pressure.setter
    def sea_level_pressure(self, value: float) -> None:
        self._sea_level_pressure = value

    @staticmethod
    def _twos_comp(val: int, bits: int) -> int:
        if val & (1 << (bits - 1)) != 0:
            return val - (1 << bits)
        return val

    @property
    def iir_coefficient(self) -> str:
        """
        Sensor iir_coefficient
        +----------------------------+------------------+
        | Mode                       | Value            |
        +============================+==================+
        | :py:const:`bmp58x.COEF_0`  | :py:const:`0x00` |
        | :py:const:`bmp58x.COEF_1`  | :py:const:`0x01` |
        | :py:const:`bmp58x.COEF_3`  | :py:const:`0x02` |
        | :py:const:`bmp58x.COEF_7`  | :py:const:`0x03` |
        | :py:const:`bmp58x.COEF_15` | :py:const:`0x04` |
        | :py:const:`bmp58x.COEF_31` | :py:const:`0x05` |
        | :py:const:`bmp58x.COEF_63` | :py:const:`0x06` |
        | :py:const:`bmp58x.COEF_127`| :py:const:`0x07` |
        +----------------------------+------------------+
        :return: coefficients as string
        """
        string_name = ("COEF_0", "COEF_1", "COEF_3", "COEF_7", "COEF_15", "COEF_31", "COEF_63", "COEF_127",)
        return string_name[self._iir_coefficient]

    @iir_coefficient.setter
    def iir_coefficient(self, value: int) -> None:
        if value not in iir_coefficient_values:
            raise ValueError(
                "Value must be a valid iir_coefficients: COEF_0,COEF_1,COEF_3,COEF_7,COEF_15,COEF_31,COEF_63,COEF_127")
        self._iir_coefficient = value

    @property
    def output_data_rate(self) -> int:
        """
        Sensor output_data_rate. for a complete list of values please see the datasheet
        """
        return self._output_data_rate

    @output_data_rate.setter
    def output_data_rate(self, value: int) -> None:
        if value not in range(0, 32, 1):
            raise ValueError("Value must be a valid output_data_rate setting: 0 to 32")
        self._output_data_rate = value


class BMP585(BMP581):
    """Driver for the BMP585 Sensor connected over I2C.

    :param ~machine.I2C i2c: The I2C bus the BMP585 is connected to.
    :param int address: The I2C device address. Defaults to :const:`0x47`

    :raises RuntimeError: if the sensor is not found

    **Quickstart: Importing and using the device**

    Here is an example of using the :class:`BMP585` class.
    First you will need to import the libraries to use the sensor

    .. code-block:: python

        from machine import Pin, I2C
        from micropython_bmp58x import bmp58x

    Once this is done you can define your `machine.I2C` object and define your sensor object

    .. code-block:: python

        i2c = I2C(1, sda=Pin(2), scl=Pin(3))
        bmp = bmp58x.BMP585(i2c)

    Now you have access to the attributes

    .. code-block:: python

        press = bmp.pressure
        temp = bmp.temperature

        # altitude in meters based on sea level pressure of 1013.25 hPA
        meters = bmp.altitude
        print(f"alt = {meters:.2f} meters")

        # set sea level pressure to a known sea level pressure in hPa at nearest airport
        # https://www.weather.gov/wrh/timeseries?site=KPDX
        bmp.sea_level_pressure = 1010.80
        meters = bmp.altitude
        print(f"alt = {meters:.2f} meters")

        # Highest resolution for bmp585
        bmp.pressure_oversample_rate = bmp.OSR128
        bmp.temperature_oversample_rate = bmp.OSR8
        meters = bmp.altitude
    """
    
    BMP585_I2C_ADDRESS_DEFAULT = 0x47
    BMP585_I2C_ADDRESS_SECONDARY = 0x46

    def __init__(self, i2c, address: int = None) -> None:
        # If no address is provided, try the default, then secondary
        if address is None:
            if self._check_address(i2c, self.BMP585_I2C_ADDRESS_DEFAULT):
                address = self.BMP585_I2C_ADDRESS_DEFAULT
            elif self._check_address(i2c, self.BMP585_I2C_ADDRESS_SECONDARY):
                address = self.BMP585_I2C_ADDRESS_SECONDARY
            else:
                raise RuntimeError("BMP585 sensor not found at known I2C address (0x47,0x46).")
        print("*** BMP585 driver untested ***")
        
        self._i2c = i2c
        self._address = address
        if self._read_device_id() != 0x51:  # check _device_id after i2c established
            raise RuntimeError("Failed to find the BMP585 sensor")
        self._power_mode = NORMAL
        self._pressure_enabled = True
        self.sea_level_pressure = WORLD_AVERAGE_SEA_LEVEL_PRESSURE
        print("*** BMP585 driver untested ***")

    def _read_device_id(self) -> int:
        return self._device_id


class BMP390(BMP581):
    """Driver for the BMP390 Sensor connected over I2C.

    :param ~machine.I2C i2c: The I2C bus the BMP390 is connected to.
    :param int address: The I2C device address. Defaults to :const:`0x7F`

    :raises RuntimeError: if the sensor is not found

    **Quickstart: Importing and using the device**

    Here is an example of using the :class:`BMP390` class.
    First you will need to import the libraries to use the sensor

    .. code-block:: python

        from machine import Pin, I2C
        from micropython_bmp58x import bmp58x

    Once this is done you can define your `machine.I2C` object and define your sensor object

    .. code-block:: python

        i2c = I2C(1, sda=Pin(2), scl=Pin(3))
        bmp = bmp58x.BMP390(i2c)

    Now you have access to the attributes

    .. code-block:: python

        press = bmp.pressure
        temp = bmp.temperature

        # altitude in meters based on sea level pressure of 1013.25 hPA
        meters = bmp.altitude
        print(f"alt = {meters:.2f} meters")

        # set sea level pressure to a known sea level pressure in hPa at nearest airport
        # https://www.weather.gov/wrh/timeseries?site=KPDX
        bmp.sea_level_pressure = 1010.80
        meters = bmp.altitude
        print(f"alt = {meters:.2f} meters")

        # Highest resolution for bmp390
        bmp.pressure_oversample_rate = bmp.OSR32
        bmp.temperature_oversample_rate = bmp.OSR2
        bmp.iir_coefficient = bmp.COEF_3
        meters = bmp.altitude

    """
    # Power Modes for BMP390
    power_mode_values = (STANDBY, FORCED, NORMAL)

    # oversampling rates
    pressure_oversample_rate_values = (OSR1, OSR2, OSR4, OSR8, OSR16, OSR32)
    temperature_oversample_rate_values = (OSR1, OSR2, OSR4, OSR8, OSR16, OSR32)
    
    BMP585_I2C_ADDRESS_DEFAULT = 0x7f
    BMP585_I2C_ADDRESS_SECONDARY = 0x7e

    ###  BMP390 Constants - notice very different than bmp581
    _REG_WHOAMI_BMP390 = const(0x00)
    _CONFIG_BMP390 = const(0x1f)
    _ODR_CONFIG_BMP390 = const(0x1d)
    _OSR_CONF_BMP390 = const(0x1c)
    _PWR_CTRL_BMP390 = const(0x1b)
    _TEMP_DATA_BMP390 = const(0x07)
    _PRESS_DATA_BMP390 = const(0x04)

    _device_id = RegisterStruct(_REG_WHOAMI_BMP390, "B")

    _power_mode = CBits(2, _PWR_CTRL_BMP390, 4)
    _temperature_oversample_rate = CBits(3, _OSR_CONF_BMP390, 3)
    _pressure_oversample_rate = CBits(3, _OSR_CONF_BMP390, 0)
    _iir_coefficient = CBits(3, _CONFIG_BMP390, 1)
    _output_data_rate = CBits(5, _ODR_CONFIG_BMP390, 0)
    _pressure_enabled = CBits(1, _PWR_CTRL_BMP390, 0)

    _temperature = CBits(24, _TEMP_DATA_BMP390, 0, 3)
    _pressure = CBits(24, _PRESS_DATA_BMP390, 0, 3)

    _par_t1_msb = CBits(8, 0x32, 0)  # Most significant byte of par_t1
    _par_t1_lsb = CBits(8, 0x31, 0)  # Least significant byte of par_t1
    _par_t2_msb = CBits(8, 0x34, 0)  # Most significant byte of par_t2
    _par_t2_lsb = CBits(8, 0x33, 0)  # Least significant byte of par_t2
    _par_t3 = CBits(8, 0x35, 0)  # Only byte for par_t3

    _par_p1_msb = CBits(8, 0x37, 0)  # Most significant byte of par_p1
    _par_p1_lsb = CBits(8, 0x36, 0)  # Least significant byte of par_p1
    _par_p2_msb = CBits(8, 0x39, 0)  # Most significant byte of par_p2
    _par_p2_lsb = CBits(8, 0x38, 0)  # Least significant byte of par_p2
    _par_p3 = CBits(8, 0x3A, 0)  # Only byte for par_p3
    _par_p4 = CBits(8, 0x3B, 0)  # Only byte for par_p4
    _par_p5_msb = CBits(8, 0x3D, 0)  # Most significant byte of par_p5
    _par_p5_lsb = CBits(8, 0x3C, 0)  # Least significant byte of par_p5
    _par_p6_msb = CBits(8, 0x3F, 0)  # Most significant byte of par_p6
    _par_p6_lsb = CBits(8, 0x3E, 0)  # Least significant byte of par_p6
    _par_p7 = CBits(8, 0x40, 0)  # Only byte for par_p7
    _par_p8 = CBits(8, 0x41, 0)  # Only byte for par_p8
    _par_p9_msb = CBits(8, 0x43, 0)  # Most significant byte of par_p9
    _par_p9_lsb = CBits(8, 0x42, 0)  # Least significant byte of par_p9
    _par_p10 = CBits(8, 0x44, 0)  # Only byte for par_p10
    _par_p11 = CBits(8, 0x45, 0)  # Only byte for par_p11

    def __init__(self, i2c, address: int = None) -> None:
        # If no address is provided, try the default, then secondary
        if address is None:
            if self._check_address(i2c, self.BMP390_I2C_ADDRESS_DEFAULT):
                address = self.BMP581_I2C_ADDRESS_DEFAULT
            elif self._check_address(i2c, self.BMP390_I2C_ADDRESS_SECONDARY):
                address = self.BMP581_I2C_ADDRESS_SECONDARY
            else:
                raise RuntimeError("BMP390 sensor not found at known I2C address (0x7f,0x7e).")
        self._i2c = i2c
        self._address = address
        if self._read_device_id() != 0x60:  # check _device_id after i2c established
            raise RuntimeError("Failed to find the BMP390 sensor")
        self._power_mode = NORMAL
        self._pressure_enabled = True
        self.sea_level_pressure = WORLD_AVERAGE_SEA_LEVEL_PRESSURE
    
    def _check_address(self, i2c, address: int) -> bool:
        """Helper function to check if a device responds at the given I2C address."""
        try:
            i2c.writeto(address, b"")  # Attempt a write operation
            return True
        except OSError:
            return False

    def _read_device_id(self) -> int:
        return self._device_id
        
    @property
    def par_t1(self) -> int:
        """Combine _par_t1_msb and _par_t1_lsb into a unsigned 16-bit integer."""
        msb_value = self._par_t1_msb  # Reads CBits value
        lsb_value = self._par_t1_lsb  # Reads CBits value
        return ((msb_value << 8) | lsb_value) & 0xFFFF

    @property
    def par_t2(self) -> int:
        """Combine _par_t2_msb and _par_t2_lsb into a unsigned 16-bit integer."""
        msb_value = self._par_t2_msb  # Reads CBits value
        lsb_value = self._par_t2_lsb  # Reads CBits value
        return ((msb_value << 8) | lsb_value) & 0xFFFF

    @property
    def par_t3(self) -> int:
        """Read the single-byte _par_t3 signed 8-bit value."""
        return self._par_t3 if self._par_t3 <= 127 else self._par_t3 - 256

    @property
    def par_p1(self) -> int:
        """Combine _par_p1_msb and _par_p1_lsb into a signed 16-bit integer."""
        msb_value = self._par_p1_msb  # Reads CBits value
        lsb_value = self._par_p1_lsb  # Reads CBits value
        combined_value = (msb_value << 8) | lsb_value

        # Convert to signed 16-bit value (two's complement)
        if combined_value >= 0x8000:  # If the value is greater than or equal to 32768
            return combined_value - 0x10000  # Convert to signed by subtracting 65536
        return combined_value

    @property
    def par_p2(self) -> int:
        """Combine _par_p2_msb and _p_par_tp_lsb into a signed 16-bit integer."""
        msb_value = self._par_p2_msb  # Reads CBits value
        lsb_value = self._par_p2_lsb  # Reads CBits value
        combined_value = (msb_value << 8) | lsb_value
        # Convert to signed 16-bit value (two's complement)
        if combined_value >= 0x8000:  # If the value is greater than or equal to 32768
            return combined_value - 0x10000  # Convert to signed by subtracting 65536
        return combined_value

    @property
    def par_p3(self) -> int:
        """Read the single-byte _par_p3 signed 8-bit value."""
        return self._par_p3 if self._par_p3 <= 127 else self._par_p3 - 256

    @property
    def par_p4(self) -> int:
        """Read the single-byte _par_p4 signed 8-bit value."""
        return self._par_p4 if self._par_p4 <= 127 else self._par_p4 - 256

    @property
    def par_p5(self) -> int:
        """Combine _par_p5_msb and _par_p5_lsb into a unsigned 16-bit integer."""
        msb_value = self._par_p5_msb  # Reads CBits value
        lsb_value = self._par_p5_lsb  # Reads CBits value
        return (msb_value << 8) | lsb_value

    @property
    def par_p6(self) -> int:
        """Combine _par_p6_msb and _par_p6_lsb into a unsigned 16-bit integer."""
        msb_value = self._par_p6_msb  # Reads CBits value
        lsb_value = self._par_p6_lsb  # Reads CBits value
        return (msb_value << 8) | lsb_value

    @property
    def par_p7(self) -> int:
        """Read the single-byte _par_p7 signed 8-bit value."""
        return self._par_p7 if self._par_p7 <= 127 else self._par_p7 - 256

    @property
    def par_p8(self) -> int:
        """Read the single-byte _par_p8 signed 8-bit value."""
        return self._par_p8 if self._par_p8 <= 127 else self._par_p8 - 256

    @property
    def par_p9(self) -> int:
        """Combine _par_p9_msb and _par_p9_lsb into a signed 16-bit integer."""
        msb_value = self._par_p9_msb  # Reads CBits value
        lsb_value = self._par_p9_lsb  # Reads CBits value
        combined_value = (msb_value << 8) | lsb_value
        # Convert to signed 16-bit value (two's complement)
        if combined_value >= 0x8000:  # If the value is greater than or equal to 32768
            return combined_value - 0x10000  # Convert to signed by subtracting 65536
        return combined_value

    @property
    def par_p10(self) -> int:
        """Read the single-byte _par_p10 signed 8-bit value."""
        return self._par_p10 if self._par_p10 <= 127 else self._par_p10 - 256

    @property
    def par_p11(self) -> int:
        """Read the single-byte _par_p11 signed 8-bit value."""
        return self._par_p11 if self._par_p11 <= 127 else self._par_p11 - 256

    @property
    def power_mode(self) -> str:
        """
        Sensor power_mode
        +-----------------------------+------------------+
        | Mode                        | Value            |
        +=============================+==================+
        | :py:const:`bmp58x.STANDBY`  | :py:const:`0x00` |
        | :py:const:`bmp58x.FORCED`   | :py:const:`0x01` |
        | :py:const:`bmp58x.FORCED`   | :py:const:`0x02` |
        | :py:const:`bmp58x.NORMAL`   | :py:const:`0X03` |
        +-----------------------------+------------------+
        :return: sampling rate as string
        """
        string_name = ("STANDBY", "FORCED", "NORMAL",)
        return string_name[self._power_mode]

    @power_mode.setter
    def power_mode(self, value: int) -> None:
        if value not in power_mode_values:
            raise ValueError("Value must be a valid power_mode setting: STANDBY,FORCED,NORMAL")
        self._power_mode = value

    @property
    def pressure_oversample_rate(self) -> str:
        """
        Sensor pressure_oversample_rate
        Oversampling extends the measurement time per measurement by the oversampling
        factor. Higher oversampling factors offer decreased noise at the cost of
        higher power consumption.
        +---------------------------+------------------+
        | Mode                      | Value            |
        +===========================+==================+
        | :py:const:`bmp58x.OSR1`   | :py:const:`0x00` |
        | :py:const:`bmp58x.OSR2`   | :py:const:`0x01` |
        | :py:const:`bmp58x.OSR4`   | :py:const:`0x02` |
        | :py:const:`bmp58x.OSR8`   | :py:const:`0x03` |
        | :py:const:`bmp58x.OSR16`  | :py:const:`0x04` |
        | :py:const:`bmp58x.OSR32`  | :py:const:`0x05` |
        +---------------------------+------------------+
        :return: sampling rate as string
        """
        string_name = ("OSR1", "OSR2", "OSR4", "OSR8", "OSR16", "OSR32",)
        return string_name[self._pressure_oversample_rate]

    @pressure_oversample_rate.setter
    def pressure_oversample_rate(self, value: int) -> None:
        if value not in self.pressure_oversample_rate_values:
            raise ValueError("Value must be a valid pressure_oversample_rate: OSR1,OSR2,OSR4,OSR8,OSR16,OSR32")
        self._pressure_oversample_rate = value

    @property
    def temperature_oversample_rate(self) -> str:
        """
        Sensor temperature_oversample_rate
        +---------------------------+------------------+
        | Mode                      | Value            |
        +===========================+==================+
        | :py:const:`bmp58x.OSR1`   | :py:const:`0x00` |
        | :py:const:`bmp58x.OSR2`   | :py:const:`0x01` |
        | :py:const:`bmp58x.OSR4`   | :py:const:`0x02` |
        | :py:const:`bmp58x.OSR8`   | :py:const:`0x03` |
        | :py:const:`bmp58x.OSR16`  | :py:const:`0x04` |
        | :py:const:`bmp58x.OSR32`  | :py:const:`0x05` |
        +---------------------------+------------------+
        :return: sampling rate as string
        """
        string_name = ("OSR1", "OSR2", "OSR4", "OSR8", "OSR16", "OSR32",)
        return string_name[self._temperature_oversample_rate]

    @temperature_oversample_rate.setter
    def temperature_oversample_rate(self, value: int) -> None:
        if value not in self.temperature_oversample_rate_values:
            raise ValueError(
                "Value must be a valid temperature_oversample_rate: OSR1,OSR2,OSR4,OSR8,OSR16,OSR32")
        self._temperature_oversample_rate = value

    # Helper method for temperature compensation
    def _calculate_temperature_compensation(self, raw_temp: float) -> float:
        partial_data1 = float(raw_temp - (self.par_t1 / 2.0 ** -8))
        partial_data2 = partial_data1 * (self.par_t2 / 2.0 ** 30)
        tempc = partial_data2 + (partial_data1 ** 2) * (self.par_t3 / 2.0 ** 48)
        return tempc

    # Helper method for pressure compensation
    def _calculate_pressure_compensation(self, raw_pressure: float, tempc: float) -> float:
        # First part
        partial_data1 = (self.par_p6 / 2.0 ** 6) * tempc
        partial_data2 = (self.par_p7 / 2.0 ** 8) * (tempc ** 2)
        partial_data3 = (self.par_p8 / 2.0 ** 15) * (tempc ** 3)
        partial_out1 = (self.par_p5 / 2.0 ** -3) + partial_data1 + partial_data2 + partial_data3

        # Second part
        partial_data1 = ((self.par_p2 - 2.0 ** 14) / 2.0 ** 29) * tempc
        partial_data2 = (self.par_p3 / 2.0 ** 32) * (tempc ** 2)
        partial_data3 = (self.par_p4 / 2.0 ** 37) * (tempc ** 3)
        partial_out2 = raw_pressure * (
                ((self.par_p1 - 2.0 ** 14) / 2.0 ** 20) + partial_data1 + partial_data2 + partial_data3)

        # Third part
        partial_data1 = raw_pressure ** 2
        partial_data2 = (self.par_p9 / 2.0 ** 48) + (self.par_p10 / 2.0 ** 48) * tempc
        partial_data3 = partial_data1 * partial_data2
        partial_data4 = partial_data3 + (raw_pressure ** 3) * (self.par_p11 / 2.0 ** 65)

        # Final compensated pressure
        return partial_out1 + partial_out2 + partial_data4

    @property
    def temperature(self) -> float:
        """
        The temperature sensor in Celsius
        :return: Temperature in Celsius
        """
        raw_temp = self._temperature
        return self._calculate_temperature_compensation(raw_temp)

    @property
    def pressure(self) -> float:
        """
        The sensor pressure in hPa
        :return: Pressure in hPa
        """
        raw_pressure = float(self._pressure)
        raw_temp = float(self._temperature)

        tempc = self._calculate_temperature_compensation(raw_temp)
        comp_press = self._calculate_pressure_compensation(raw_pressure, tempc)
        return comp_press / 100.0  # Convert to hPa
