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
`bmpxxx`
================================================================================

MicroPython Driver for the Bosch BMP585, BMP581, BMP390, BMP280 pressure sensors

* Author: Brad Carlile

Based on

* micropython-bmp581/bmp581py. Author(s): Jose D. Montoya

"""
import time

from micropython import const
from micropython_bmpxxx.i2c_helpers import CBits, RegisterStruct

try:
    import struct
except ImportError:
    import ustruct as struct

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
        from micropython_bmpxxx import bmpxxx

    Once this is done you can define your `machine.I2C` object and define your sensor object

    .. code-block:: python

        i2c = I2C(1, sda=Pin(2), scl=Pin(3))
        bmp = bmpxxx.BMP581(i2c)

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

        # Highest recommended resolution bmp581
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

    # bmp581 Address & Settings
    _REG_WHOAMI = const(0x01)
    _INT_STATUS = const(0x27)
    _DSP_CONFIG = const(0x30)
    _DSP_IIR = const(0x31)
    _OSR_CONF = const(0x36)
    _ODR_CONFIG = const(0x37)
    _CMD_BMP581 = const(0x7e)

    _device_id = RegisterStruct(_REG_WHOAMI, "B")
    _SOFTRESET = const(0xB6)  # same value for 585,581,390,280

    _cmd_register_BMP581 = CBits(8, _CMD_BMP581, 0)
    _drdy_status = CBits(1, _INT_STATUS, 0)
    _power_mode = CBits(2, _ODR_CONFIG, 0)
    _temperature_oversample_rate = CBits(3, _OSR_CONF, 0)
    _pressure_oversample_rate = CBits(3, _OSR_CONF, 3)
    _output_data_rate = CBits(5, _ODR_CONFIG, 2)
    _pressure_enabled = CBits(1, _OSR_CONF, 6)
    _iir_coefficient = CBits(3, _DSP_IIR, 3)  # Pressure IIR coefficient
    _iir_temp_coefficient = CBits(3, _DSP_IIR, 0)  # Temp IIR coefficient
    _iir_control = CBits(8, _DSP_CONFIG, 0)
    _temperature = CBits(24, 0x1D, 0, 3)
    _pressure = CBits(24, 0x20, 0, 3)

    def __init__(self, i2c, address: int = None) -> None:
        time.sleep_ms(3)  # t_powup done in 2ms

        # If no address is provided, try the default, then secondary
        if address is None:
            if self._check_address(i2c, self.BMP581_I2C_ADDRESS_DEFAULT):
                address = self.BMP581_I2C_ADDRESS_DEFAULT
            elif self._check_address(i2c, self.BMP581_I2C_ADDRESS_SECONDARY):
                address = self.BMP581_I2C_ADDRESS_SECONDARY
            else:
                raise RuntimeError("BMP581 sensor not found at I2C expected address (0x47,0x46).")
        else:
            # Check if the specified address is valid
            if not self._check_address(i2c, address):
                raise RuntimeError(f"BMP581 sensor not found at specified I2C address ({hex(address)}).")

        self._i2c = i2c
        self._address = address
        if self._read_device_id() != 0x50:  # check _device_id after i2c established
            raise RuntimeError("Failed to find the BMP581 sensor")

        self._cmd_register_BMP581 = _SOFTRESET
        time.sleep_ms(5)  # soft reset finishes in 2ms

        # Must be in STANDBY to initialize _iir_coefficient    
        self._power_mode = STANDBY
        time.sleep_ms(5)  # mode change takes 4ms
        self._pressure_enabled = True
        self._output_data_rate = 0  # Default rate
        self._temperature_oversample_rate = self.OSR1  # Default oversampling
        self._pressure_oversample_rate = self.OSR1  # Default oversampling
        self._iir_coefficient = COEF_0
        self._iir_temp_coefficient = COEF_0
        self._power_mode = NORMAL
        time.sleep_ms(5)  # mode change takes 4ms

#         self._drdy_status = 0  # Default data-ready status
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
    def config(self):
        print(f"{hex(self._address)=}")
        print(f"{hex(self._device_id)=}")
        print(f"{self.power_mode=}")
        print(f"{self.pressure_oversample_rate=}")
        print(f"{self.temperature_oversample_rate=}")
        print(f"{self.iir_coefficient=}")
        print(f"{self.sea_level_pressure=}")
        print(f"{self.pressure=} hPa")
        print(f"{self.temperature=} C")
        print(f"{self.altitude=} m\n")

    @property
    def power_mode(self) -> str:
        """
        Sensor power_mode
        +-----------------------------+------------------+
        | Mode                        | Value            |
        +=============================+==================+
        | :py:const:`bmp58x.STANDBY`  | :py:const:`0x00` |
        | :py:const:`bmp58x.NORMAL`   | :py:const:`0x01` |
        | :py:const:`bmp58x.FORCED`   | :py:const:`0x02` |
        | :py:const:`bmp58x.NON_STOP` | :py:const:`0X03` |
        +-----------------------------+------------------+
        """
        values = ("STANDBY", "NORMAL", "FORCED", "NON_STOP",)
        return values[self._power_mode]

    @power_mode.setter
    def power_mode(self, value: int) -> None:
        if value not in self.power_mode_values:
            raise ValueError("Value must be a valid power_mode setting: STANDBY,NORMAL,FORCED,NON_STOP")
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
        | :py:const:`bmpxxx.OSR1`   | :py:const:`0x00` |
        | :py:const:`bmpxxx.OSR2`   | :py:const:`0x01` |
        | :py:const:`bmpxxx.OSR4`   | :py:const:`0x02` |
        | :py:const:`bmpxxx.OSR8`   | :py:const:`0x03` |
        | :py:const:`bmpxxx.OSR16`  | :py:const:`0x04` |
        | :py:const:`bmpxxx.OSR32`  | :py:const:`0x05` |
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
        | :py:const:`bmpxxx.OSR1`   | :py:const:`0x00` |
        | :py:const:`bmpxxx.OSR2`   | :py:const:`0x01` |
        | :py:const:`bmpxxx.OSR4`   | :py:const:`0x02` |
        | :py:const:`bmpxxx.OSR8`   | :py:const:`0x03` |
        | :py:const:`bmpxxx.OSR16`  | :py:const:`0x04` |
        | :py:const:`bmpxxx.OSR32`  | :py:const:`0x05` |
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
        :return: Temperature in Celsius
        """
        raw_temp = self._temperature
        return self._twos_comp(raw_temp, 24) / 65536.0

    @property
    def pressure(self) -> float:
        """
        :return: Pressure in hPa
        """
        raw_pressure = self._pressure
        return self._twos_comp(raw_pressure, 24) / 64.0 / 100.0

    @property
    def altitude(self) -> float:
        """
        Using the sensor's measured pressure and the pressure at sea level (e.g., 1013.25 hPa),
        the altitude in meters is calculated with the international barometric formula
        https://ncar.github.io/aircraft_ProcessingAlgorithms/www/PressureAltitude.pdf
        """
        altitude = 44330.77 * (
                1.0 - ((self.pressure / self.sea_level_pressure) ** 0.1902632)
        )
        return altitude

    @altitude.setter
    def altitude(self, value: float) -> None:
        self.sea_level_pressure = self.pressure / (1.0 - value / 44330.77) ** (1 / 0.1902632)

    @property
    def sea_level_pressure(self) -> float:
        """
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
        | :py:const:`bmpxxx.COEF_0`  | :py:const:`0x00` |
        | :py:const:`bmpxxx.COEF_1`  | :py:const:`0x01` |
        | :py:const:`bmpxxx.COEF_3`  | :py:const:`0x02` |
        | :py:const:`bmpxxx.COEF_7`  | :py:const:`0x03` |
        | :py:const:`bmpxxx.COEF_15` | :py:const:`0x04` |
        | :py:const:`bmpxxx.COEF_31` | :py:const:`0x05` |
        | :py:const:`bmpxxx.COEF_63` | :py:const:`0x06` |
        | :py:const:`bmpxxx.COEF_127`| :py:const:`0x07` |
        +----------------------------+------------------+
        :return: coefficients as string
        """
        values = ("COEF_0", "COEF_1", "COEF_3", "COEF_7", "COEF_15", "COEF_31", "COEF_63", "COEF_127",)
        return values[self._iir_coefficient]

    @iir_coefficient.setter
    def iir_coefficient(self, value: int) -> None:
        if value not in self.iir_coefficient_values:
            raise ValueError(
                "Value must be a valid iir_coefficients: COEF_0,COEF_1,COEF_3,COEF_7,COEF_15,COEF_31,COEF_63,COEF_127")

        # Ensure the sensor is in STANDBY mode before updating
        original_mode = self._power_mode  # Save the current mode
        if original_mode != STANDBY:
            self.power_mode = STANDBY  # Set to STANDBY if not already
        self._iir_coefficient = value
        self._iir_temp_coefficient = value

        # Restore the original power mode
        self.power_mode = original_mode

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

    .. code-block:: python

        from machine import Pin, I2C
        from micropython_bmpxxx import bmpxxx

    Once this is done you can define your `machine.I2C` object and define your sensor object

    .. code-block:: python

        i2c = I2C(1, sda=Pin(2), scl=Pin(3))
        bmp = bmpxxx.BMP585(i2c)

    Now you have access to the attributes

    .. code-block:: python

        press = bmp.pressure
        temp = bmp.temperature

        # Highest recommended resolution for bmp585
        bmp.pressure_oversample_rate = bmp.OSR128
        bmp.temperature_oversample_rate = bmp.OSR8
        meters = bmp.altitude

    """
    BMP585_I2C_ADDRESS_DEFAULT = 0x47
    BMP585_I2C_ADDRESS_SECONDARY = 0x46

    _CMD_BMP585 = const(0x7e)
    _cmd_register_BMP585 = CBits(8, _CMD_BMP585, 0)

    def __init__(self, i2c, address: int = None) -> None:
        time.sleep_ms(3)  # t_powup done in 2ms

        # If no address is provided, try the default, then secondary
        if address is None:
            if self._check_address(i2c, self.BMP585_I2C_ADDRESS_DEFAULT):
                address = self.BMP585_I2C_ADDRESS_DEFAULT
            elif self._check_address(i2c, self.BMP585_I2C_ADDRESS_SECONDARY):
                address = self.BMP585_I2C_ADDRESS_SECONDARY
            else:
                raise RuntimeError("BMP585 sensor not found at I2C expected address (0x47,0x46).")
        else:
            # Check if the specified address is valid
            if not self._check_address(i2c, address):
                raise RuntimeError(f"BMP585 sensor not found at specified I2C address ({hex(address)}).")

        self._i2c = i2c
        self._address = address
        if self._read_device_id() != 0x51:  # check _device_id after i2c established
            raise RuntimeError("Failed to find the BMP585 sensor")

        self._cmd_register_BMP585 = _SOFTRESET
        time.sleep_ms(5)  # soft reset finishes in 2ms

        # Must be in STANDBY to initialize _iir_coefficient    
        self._power_mode = STANDBY
        time.sleep_ms(5)  # mode change takes 4ms
        self._pressure_enabled = True
        self._temperature_oversample_rate = self.OSR1  # Default oversampling
        self._pressure_oversample_rate = self.OSR1  # Default oversampling
        self._iir_coefficient = COEF_0
        self._iir_temp_coefficient = COEF_0
        self._power_mode = NORMAL
        time.sleep_ms(5)  # mode change takes 4ms
        #         self._write_reg(0x18, 0x01)  # Enable data ready interrupts
        #         val = self._read_reg(0x27, 1)[0]  # Read Interrupt Status Register
        #         drdy_data_reg = (val & 0x01) != 0  # Check Data Ready bit
        # 
        #         print(f"{drdy_data_reg=}")
        self.sea_level_pressure = WORLD_AVERAGE_SEA_LEVEL_PRESSURE


class BMP390(BMP581):
    """Driver for the BMP390 Sensor connected over I2C.

    :param ~machine.I2C i2c: The I2C bus the BMP390 is connected to.
    :param int address: The I2C device address. Defaults to :const:`0x7F`

    :raises RuntimeError: if the sensor is not found

    **Quickstart: Importing and using the device**

    .. code-block:: python

        from machine import Pin, I2C
        from micropython_bmpxxx import bmpxxx

    Once this is done you can define your `machine.I2C` object and define your sensor object

    .. code-block:: python

        i2c = I2C(1, sda=Pin(2), scl=Pin(3))
        bmp = bmpxxx.BMP390(i2c)

    Now you have access to the attributes

    .. code-block:: python

        press = bmp.pressure
        temp = bmp.temperature

        # Highest recommended resolution for bmp390
        bmp.pressure_oversample_rate = bmp.OSR32
        bmp.temperature_oversample_rate = bmp.OSR2
        meters = bmp.altitude

    """
    # Power Modes for BMP390
    BMP390_SLEEP_POWER = const(0x00)  # aka  STANDBY for bmp585/bmp581
    BMP390_FORCED_ALT_POWER = const(0x01)
    BMP390_FORCED_POWER = const(0x02)
    BMP390_NORMAL_POWER = const(0x03)
    power_mode_values = (BMP390_SLEEP_POWER, BMP390_FORCED_ALT_POWER, BMP390_FORCED_POWER, BMP390_NORMAL_POWER)

    # oversampling rates
    pressure_oversample_rate_values = (OSR1, OSR2, OSR4, OSR8, OSR16, OSR32)
    temperature_oversample_rate_values = (OSR1, OSR2, OSR4, OSR8, OSR16, OSR32)

    # ODR_SEL page 38 Bosch Data sheet
    BMP390_ODR_25 = const(0x03)  # ODR_25 Hz = 40ms

    BMP390_I2C_ADDRESS_DEFAULT = 0x7f
    BMP390_I2C_ADDRESS_SECONDARY = 0x7e

    ###  BMP390 Constants - notice very different than bmp581
    _REG_WHOAMI_BMP390 = const(0x00)
    _CMD_BMP390 = const(0x7e)
    _CONFIG_BMP390 = const(0x1f)
    _ODR_CONFIG_BMP390 = const(0x1d)
    _OSR_CONF_BMP390 = const(0x1c)
    _PWR_CTRL_BMP390 = const(0x1b)
    _TEMP_DATA_BMP390 = const(0x07)
    _PRESS_DATA_BMP390 = const(0x04)
    _TRIM_COEFF_BMP390 = const(0x31)

    _device_id = RegisterStruct(_REG_WHOAMI_BMP390, "B")

    _mode = CBits(2, _PWR_CTRL_BMP390, 4)
    _temperature_enabled = CBits(1, _PWR_CTRL_BMP390, 1)
    _pressure_enabled = CBits(1, _PWR_CTRL_BMP390, 0)
    _control_register_BMP390 = CBits(8, _PWR_CTRL_BMP390, 0)
    _cmd_register_BMP390 = CBits(8, _CMD_BMP390, 0)

    _temperature_oversample_rate = CBits(3, _OSR_CONF_BMP390, 3)
    _pressure_oversample_rate = CBits(3, _OSR_CONF_BMP390, 0)
    _iir_coefficient = CBits(3, _CONFIG_BMP390, 1)
    _output_data_rate = CBits(5, _ODR_CONFIG_BMP390, 0)
    _temperature = CBits(24, _TEMP_DATA_BMP390, 0, 3)
    _pressure = CBits(24, _PRESS_DATA_BMP390, 0, 3)

    def __init__(self, i2c, address: int = None) -> None:
        time.sleep_ms(3)  # t_powup done in 2ms
        # If no address is provided, try the default, then secondary
        if address is None:
            if self._check_address(i2c, self.BMP390_I2C_ADDRESS_DEFAULT):
                address = self.BMP390_I2C_ADDRESS_DEFAULT
            elif self._check_address(i2c, self.BMP390_I2C_ADDRESS_SECONDARY):
                address = self.BMP390_I2C_ADDRESS_SECONDARY
            else:
                raise RuntimeError("BMP390 sensor not found at I2C expected address (0x7f,0x7e).")
        else:
            # Check if the specified address is valid
            if not self._check_address(i2c, address):
                raise RuntimeError(f"BMP390 sensor not found at specified I2C address ({hex(address)}).")


        self._i2c = i2c
        self._address = address
        if self._read_device_id() != 0x60:  # check _device_id after i2c established
            raise RuntimeError("Failed to find the BMP390 sensor with id=0x60")

        self._cmd_register_BMP390 = _SOFTRESET
        time.sleep_ms(5)  # soft reset finishes in ?ms

        self._pressure_enabled = True
        self._temperature_enabled = True
        self._output_data_rate = BMP390_ODR_25
        self._mode = BMP390_NORMAL_POWER
        time.sleep_ms(4)  # mode change takes 3ms

        self.sea_level_pressure = WORLD_AVERAGE_SEA_LEVEL_PRESSURE
        self._read_calibration_bmp390()

    def _read_calibration_bmp390(self):
        """
        Read & save the calibration coefficients
        Unpack data specified in string: "<HHbhhbbHHbbhbb"
            Little-endian (<), 16-bit unsigned (H), 16-bit unsigned (H), 8-bit signed (b), 16-bit signed (h)
        """
        coeff = self._i2c.readfrom_mem(self._address, _TRIM_COEFF_BMP390, 21)
        values = struct.unpack("<HHbhhbbHHbbhbb", coeff)
        self.t1, self.t2, self.t3, self.p1, self.p2, self.p3, self.p4, self.p5, self.p6, self.p7, self.p8, self.p9, self.p10, self.p11 = values

        #         #values for one of sensors in comments, each sensor different
        #         print(f"t1 (16-bit unsigned, H): {self.t1}")    # 27778
        #         print(f"t2 (16-bit unsigned, H): {self.t2}")    # 19674
        #         print(f"t3 (8-bit signed, b): {self.t3}")       # -7
        #         print(f"p1 (16-bit signed, h): {self.p1}")      # 7174
        #         print(f"p2 (16-bit signed, h): {self.p2}")      # 5507
        #         print(f"p3 (8-bit signed, b): {self.p3}")       # 6
        #         print(f"p4 (8-bit signed, b): {self.p4}")       # 1
        #         print(f"p5 (16-bit unsigned, H): {self.p5}")    # 19311
        #         print(f"p6 (16-bit unsigned, H): {self.p6}")    # 24165
        #         print(f"p7 (8-bit signed, b): {self.p7}")       # 3
        #         print(f"p8 (8-bit signed, b): {self.p8}")       # -6
        #         print(f"p9 (16-bit signed, h): {self.p9}")      # 4017
        #         print(f"p10 (8-bit signed, b): {self.p10}")     # 7 
        #         print(f"p11 (8-bit signed, b): {self.p11}")     # -11
        return

    @property
    def power_mode(self) -> str:
        """
        Sensor power_mode
        notice: Bosch BMP280/BMP390 and BMP581/BMP585 have different power mode  numbers
        +-----------------------------+------------------+------------------------------+------------------+
        | Mode   rest of classes      | Value            | BMP390/BMP280 Mode           | Value            |
        +=============================+==================+==============================+==================+
        | :py:const:`bmp58x.STANDBY`  | :py:const:`0x00` | :py:const:`bmp390.SLEEP`     | :py:const:`0x00` |
        | :py:const:`bmp581.NORMAL`   | :py:const:`0x01` | :py:const:`bmp390.FORCED_ALT`| :py:const:`0x01` |
        | :py:const:`bmp58x.FORCED`   | :py:const:`0x02` | :py:const:`bmp390.FORCED`    | :py:const:`0x02` |
        | :py:const:`bmp58x.NON_STOP` | :py:const:`0X03` | :py:const:`bmp390.NORMAL`    | :py:const:`0X03` |
        +-----------------------------+------------------+------------------------------+------------------+
        :return: power_mode as string
        """
        # Notice ordering is different only for BMP390 & BMP280
        string_name = ("STANDBY", "FORCED", "FORCED", "NORMAL",)
        return string_name[self._mode]

    @power_mode.setter
    def power_mode(self, value: int) -> None:
        if value not in self.power_mode_values:
            raise ValueError("Value must be a valid power_mode setting: STANDBY,FORCED,NORMAL")
        if value == 0x01:  # NORMAL mode requested, change value to 0x03 for bmp390
            value = BMP390_NORMAL_POWER
        # if value == 0x02:  FORCED mode requested, no need to remap value
        self._mode = value

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
        | :py:const:`bmp390.OSR1`   | :py:const:`0x00` |
        | :py:const:`bmp390.OSR2`   | :py:const:`0x01` |
        | :py:const:`bmp390.OSR4`   | :py:const:`0x02` |
        | :py:const:`bmp390.OSR8`   | :py:const:`0x03` |
        | :py:const:`bmp390.OSR16`  | :py:const:`0x04` |
        | :py:const:`bmp390.OSR32`  | :py:const:`0x05` |
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
        debug? if set OSR32, my temp/pressure do not change, so debug or only use OSR16
        I've seen this in other drivers
        +---------------------------+------------------+
        | Mode                      | Value            |
        +===========================+==================+
        | :py:const:`bmp390.OSR1`   | :py:const:`0x00` |
        | :py:const:`bmp390.OSR2`   | :py:const:`0x01` |
        | :py:const:`bmp390.OSR4`   | :py:const:`0x02` |
        | :py:const:`bmp390.OSR8`   | :py:const:`0x03` |
        | :py:const:`bmp390.OSR16`  | :py:const:`0x04` |
        | :py:const:`bmp390.OSR32`  | :py:const:`0x05` | * debug: sensor may not update?
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

    @property
    def iir_coefficient(self) -> str:
        """
        Sensor iir_coefficient

        Bosch datasheet bmp390 4.3.21 Register 0x1F "CONFIG" uses thse names
        Datasheet in 3.4.4, refers to the IIR filter coefficients using coefficient+1
        IIR filter coefficient 4 is "COEF_3",  IIR filter coefficient 8 is"COEF_7"
        +----------------------------+------------------+------------------+
        | Mode                       | Value 4.3.21     | Value  3.4.4     |
        +============================+==================+==================+
        | :py:const:`bmpxxx.COEF_0`  | :py:const:`0x00` |        0         |
        | :py:const:`bmpxxx.COEF_1`  | :py:const:`0x01` |        2         |
        | :py:const:`bmpxxx.COEF_3`  | :py:const:`0x02` |        4         |
        | :py:const:`bmpxxx.COEF_7`  | :py:const:`0x03` |        8         |
        | :py:const:`bmpxxx.COEF_15` | :py:const:`0x04` |       16         |
        | :py:const:`bmpxxx.COEF_31` | :py:const:`0x05` |       32         |
        | :py:const:`bmpxxx.COEF_63` | :py:const:`0x06` |       64         |
        | :py:const:`bmpxxx.COEF_127`| :py:const:`0x07` |      128         |
        +----------------------------+------------------+------------------+
        :return: coefficients as string
        """
        values = ("COEF_0", "COEF_1", "COEF_3", "COEF_7", "COEF_15", "COEF_31", "COEF_63", "COEF_127",)
        return values[self._iir_coefficient]

    @iir_coefficient.setter
    def iir_coefficient(self, value: int) -> None:
        if value not in self.iir_coefficient_values:
            raise ValueError(
                "Value must be a valid iir_coefficients: COEF_0,COEF_1,COEF_3,COEF_7,COEF_15,COEF_31,COEF_63,COEF_127")
        self._iir_coefficient = value

    # Helper method for temperature compensation
    def _calculate_temperature_compensation(self, raw_temp: float) -> float:
        partial_data1 = float(raw_temp - (self.t1 * 2 ** 8))
        partial_data2 = partial_data1 * (self.t2 / 2 ** 30)
        tempc = partial_data2 + (partial_data1 * partial_data1) * (self.t3 / 2 ** 48)
        return tempc

    # Helper method for pressure compensation
    def _calculate_pressure_compensation(self, raw_pressure: float, tempc: float) -> float:
        # First part
        partial_data1 = (self.p6 / 2 ** 6) * tempc
        partial_data2 = (self.p7 / 2 ** 8) * (tempc * tempc)
        partial_data3 = (self.p8 / 2 ** 15) * (tempc * tempc * tempc)
        partial_out1 = (self.p5 * 2 ** 3) + partial_data1 + partial_data2 + partial_data3

        # Second part
        partial_data1 = ((self.p2 - 2 ** 14) / 2 ** 29) * tempc
        partial_data2 = (self.p3 / 2 ** 32) * (tempc * tempc)
        partial_data3 = (self.p4 / 2 ** 37) * (tempc * tempc * tempc)
        partial_out2 = raw_pressure * (
                ((self.p1 - 2 ** 14) / 2 ** 20) + partial_data1 + partial_data2 + partial_data3)

        # Third part
        partial_data1 = raw_pressure * raw_pressure
        partial_data2 = (self.p9 / 2 ** 48) + (self.p10 / 2 ** 48) * tempc
        partial_data3 = partial_data1 * partial_data2
        partial_data4 = partial_data3 + (raw_pressure * raw_pressure * raw_pressure) * (self.p11 / 2 ** 65)

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


class BMP280(BMP581):
    """Driver for the BMP280 Sensor connected over I2C.

    :param ~machine.I2C i2c: The I2C bus the BMP280 is connected to.
    :param int address: The I2C device address. Defaults to :const:`0x7F`

    :raises RuntimeError: if the sensor is not found

     **Quickstart: Importing and using the device**

    .. code-block:: python

        from machine import Pin, I2C
        from micropython_bmpxxx import bmpxxx

    Once this is done you can define your `machine.I2C` object and define your sensor object

    .. code-block:: python

        i2c = I2C(1, sda=Pin(2), scl=Pin(3))
        bmp = bmpxxx.BMP280(i2c)

    Now you have access to the attributes

    .. code-block:: python

        press = bmp.pressure
        temp = bmp.temperature

        # Highest recommended resolution for bmp280
        bmp.pressure_oversample_rate = bmp.OSR16
        bmp.temperature_oversample_rate = bmp.OSR2
        meters = bmp.altitude
    """
    # Power Modes for BMP280
    power_mode_values = (STANDBY, FORCED, NORMAL)
    BMP280_NORMAL_POWER = const(0x03)
    BMP280_FORCED_POWER = const(0x01)

    # oversampling rates
    # Below we give OSR_SKIP a unique value 0x05, but will remap it to bmp280 values
    # When we get       OSR1=0, OSR2=1, OSR4=2, OSR8=3, OSR16=4, OSR_SKIP=5
    # input to BMP280,  OSR1=1, OSR2=2, OSR4=3, OSR8=4, OSR16=5, OSR_SKIP=0
    # this will be translated in _translate_osr_bmp280
    OSR_SKIP = const(0x05)

    # OSR_SKIP turns off sampling and we do not present it as setable from outside the driver
    pressure_oversample_rate_values = (OSR1, OSR2, OSR4, OSR8, OSR16)
    temperature_oversample_rate_values = (OSR1, OSR2, OSR4, OSR8, OSR16)

    BMP280_I2C_ADDRESS_DEFAULT = 0x77
    BMP280_I2C_ADDRESS_SECONDARY = 0x76

    ###  BMP390 Constants - notice very different than bmp581
    _REG_WHOAMI_BMP280 = const(0xd0)
    _PWR_CTRL_BMP280 = const(0x1b)
    _CONTROL_REGISTER_BMP280 = const(0xF4)
    _CONFIG_BMP280 = const(0xf5)
    _RESET_BMP280 = const(0xe0)
    _TRIM_COEFF_BMP280 = const(0x88)

    _device_id = RegisterStruct(_REG_WHOAMI_BMP280, "B")

    _mode = CBits(2, _CONTROL_REGISTER_BMP280, 0)
    _pressure_oversample_rate = CBits(3, _CONTROL_REGISTER_BMP280, 2)
    _temperature_oversample_rate = CBits(3, _CONTROL_REGISTER_BMP280, 5)
    _control_register = CBits(8, _CONTROL_REGISTER_BMP280, 0)
    _config_register = CBits(8, _CONFIG_BMP280, 0)
    _reset_register = CBits(8, _RESET_BMP280, 0)
    _iir_coefficient = CBits(3, _CONFIG_BMP280, 2)

    # read pressure 0xf7 and temp 0xfa
    _d = CBits(48, 0xf7, 0, 6)

    def __init__(self, i2c, address: int = None) -> None:
        time.sleep_ms(3)  # t_powup done in 2ms

        # If no address is provided, try the default, then secondary
        if address is None:
            if self._check_address(i2c, self.BMP280_I2C_ADDRESS_DEFAULT):
                address = self.BMP280_I2C_ADDRESS_DEFAULT
            elif self._check_address(i2c, self.BMP280_I2C_ADDRESS_SECONDARY):
                address = self.BMP280_I2C_ADDRESS_SECONDARY
            else:
                raise RuntimeError("BMP280 sensor not found at I2C expected address (0x77,0x76).")
        else:
            # Check if the specified address is valid
            if not self._check_address(i2c, address):
                raise RuntimeError(f"BMP280 sensor not found at specified I2C address ({hex(address)}).")

        self._i2c = i2c
        self._address = address
        if self._read_device_id() != 0x58:  # check _device_id after i2c established
            raise RuntimeError("Failed to find the BMP280 sensor with id 0x58")

        self._reset_register_BMP280 = _SOFTRESET
        time.sleep_ms(5)  # soft reset finishes in ?ms

        self._read_calibration_bmp280()

        # To start measurements: temp OSR1, pressure OSR1 must be init with Normal power mode
        # set all values at onc
        self._config_register = 0x00
        self._control_register = (self._translate_osr_bmp280(OSR1) << 5) + (
                self._translate_osr_bmp280(OSR1) << 2) + BMP280_NORMAL_POWER
        _ = self.pressure

        time.sleep_ms(4)  # mode change takes 3ms
        time.sleep_ms(63)  # OSR can be take up to 62.5ms standby

        self.t_fine = 0
        self.sea_level_pressure = WORLD_AVERAGE_SEA_LEVEL_PRESSURE

    def _read_calibration_bmp280(self):
        """
        Read & save the calibration coefficients
        Unpack data specified in string: "<<HhhHhhhhhhhh"
            Little-endian (<), 16-bit unsigned (H), 16-bit unsigned (H), 8-bit signed (b), 16-bit signed (h)
        """
        coeff = self._i2c.readfrom_mem(self._address, _TRIM_COEFF_BMP280, 24)
        values = struct.unpack("<HhhHhhhhhhhh", coeff)
        self.t1, self.t2, self.t3, self.p1, self.p2, self.p3, self.p4, self.p5, self.p6, self.p7, self.p8, self.p9 = values

        # values for one of sensors in comments, each sensor different
        #         print(f"t1 (16-bit unsigned, H): {self.t1}")    # 27753
        #         print(f"t2 (16-bit signed, h): {self.t2}")      # 26492
        #         print(f"t3 (16-bit signed, h): {self.t3}")      # -1000
        #         print(f"p1 (16-bit unsigned, H): {self.p1}")    # 37585
        #         print(f"p2 (16-bit signed, h): {self.p2}")      # -10627
        #         print(f"p3 (16-bit signed, h): {self.p3}")      # 3024
        #         print(f"p4 (16-bit signed, h): {self.p4}")      # 9631
        #         print(f"p5 (16-bit signed, h): {self.p5}")      # 119
        #         print(f"p6 (16-bit signed, h): {self.p6}")      # -7
        #         print(f"p7 (16-bit signed, h): {self.p7}")      # 15500
        #         print(f"p8 (16-bit signed, h): {self.p8}")      # -14600
        #         print(f"p9 (16-bit signed, h): {self.p9}")      # 6000
        return

    def _translate_osr_bmp280(self, osr_value):
        """ Map the constants to their corresponding values """
        osr_map = {
            OSR1: 1,    # OSR1=0 for other sensors, but 1 for bmp280
            OSR2: 2,     # OSR2=1 for other sensors, but 2 for bmp280
            OSR4: 3,     # OSR4=2 for other sensors, but 3 for bmp280
            OSR8: 4,     # OSR8=3 for other sensors, but 4 for bmp280
            OSR16: 5,    # OSR16=4 for other sensors, but 5 for bmp280
            OSR_SKIP: 0  # OSR_SKIP=0 for bmp280, no other sensor has OSR_SKIP, we assigned it to 0x05
        }
        return osr_map.get(osr_value, 0)

    @property
    def power_mode(self) -> str:
        """
        Sensor power_mode
        notice: Bosch BMP280/BMP390 and BMP581/BMP585 have different power mode  numbers
        +-----------------------------+------------------+------------------------------+------------------+
        | Mode   rest of classes      | Value            | BMP390/BMP280 Mode           | Value            |
        +=============================+==================+==============================+==================+
        | :py:const:`bmp58x.STANDBY`  | :py:const:`0x00` | :py:const:`bmp280.SLEEP`     | :py:const:`0x00` |
        | :py:const:`bmp58x.NORMAL`   | :py:const:`0x01` | :py:const:`bmp280.FORCED_ALT`| :py:const:`0x01` |
        | :py:const:`bmp58x.FORCED`   | :py:const:`0x02` | :py:const:`bmp280.FORCED`    | :py:const:`0x02` |
        | :py:const:`bmp58x.NON_STOP` | :py:const:`0X03` | :py:const:`bmp280.NORMAL`    | :py:const:`0X03` |
        +-----------------------------+------------------+------------------------------+------------------+
        :return: power_mode as string
        """
        # Notice ordering is different only for BMP390 & BMP280
        string_name = ("STANDBY", "FORCED", "FORCED", "NORMAL",)
        return string_name[self._mode]

    @power_mode.setter
    def power_mode(self, value: int) -> None:
        if value not in self.power_mode_values:
            raise ValueError("Value must be a valid power_mode setting: STANDBY,FORCED,NORMAL")
        if value == 0x01:  # NORMAL mode requested, change value to 0x03 for bmp390
            value = BMP390_NORMAL_POWER
        # if value == 0x02:  FORCED mode requested, no need to remap value
        self._mode = value

    @property
    def pressure_oversample_rate(self) -> str:
        """
        Sensor pressure_oversample_rate
        Oversampling extends the measurement time per measurement by the oversampling
        factor. Higher oversampling factors offer decreased noise at the cost of
        higher power consumption.
        +---------------------------+------------------+---------------------------+------------------+
        | Mode-for all other classes| Value            | BMP280 Mode                | Value            |
        +===========================+==================+===========================+==================+
        | :py:const:`bmp58x.OSR1`   | :py:const:`0x00` | :py:const:`OSR_SKIP'      | :py:const:`0x00` |
        | :py:const:`bmp58x.OSR2`   | :py:const:`0x01` | :py:const:`bmp280.OSR1`   | :py:const:`0x01` |
        | :py:const:`bmp58x.OSR4`   | :py:const:`0x02` | :py:const:`bmp280.OSR2`   | :py:const:`0x02` |
        | :py:const:`bmp58x.OSR8`   | :py:const:`0x03` | :py:const:`bmp280.OSR4`   | :py:const:`0x03` |
        | :py:const:`bmp58x.OSR16`  | :py:const:`0x04` | :py:const:`bmp280.OSR8``  | :py:const:`0x04` |
        |                           |                  | :py:const:`bmp280.OSR16`  | :py:const:`0x05` |
        +---------------------------+------------------+---------------------------+------------------+
        :return: sampling rate as string
        """
        # Notice these are in the order and numbering that is appropriate for bmp280, which is different
        # than the other sensors
        string_name = ("OSR_SKIP", "OSR1", "OSR2", "OSR4", "OSR8", "OSR16",)
        return string_name[self._pressure_oversample_rate]

    @pressure_oversample_rate.setter
    def pressure_oversample_rate(self, value: int) -> None:
        if value not in self.pressure_oversample_rate_values:
            raise ValueError("Value must be a valid pressure_oversample_rate: OSR_SKIP,OSR1,OSR2,OSR4,OSR8,OSR16")
        # Get whole control register for temp Oversample (3-bit), pressure Oversample (3-bit), & powermode (2-bit)
        current_control_register = self._control_register
        # only update pressure oversample
        current_control_register = (current_control_register & 0xe3) + (self._translate_osr_bmp280(value) << 2)
        # Write whole control register at once
        self._config_register = 0x00
        self._control_register = current_control_register

    @property
    def temperature_oversample_rate(self) -> str:
        """
        Sensor temperature_oversample_rate
        +---------------------------+------------------+---------------------------+------------------+
        | Mode-for all other classes| Value            | BMP280 Mode                | Value            |
        +===========================+==================+===========================+==================+
        | :py:const:`bmp58x.OSR1`   | :py:const:`0x00` | :py:const:`OSR_SKIP'      | :py:const:`0x00` |
        | :py:const:`bmp58x.OSR2`   | :py:const:`0x01` | :py:const:`bmp280.OSR1`   | :py:const:`0x01` |
        | :py:const:`bmp58x.OSR4`   | :py:const:`0x02` | :py:const:`bmp280.OSR2`   | :py:const:`0x02` |
        | :py:const:`bmp58x.OSR8`   | :py:const:`0x03` | :py:const:`bmp280.OSR4`   | :py:const:`0x03` |
        | :py:const:`bmp58x.OSR16`  | :py:const:`0x04` | :py:const:`bmp280.OSR8``  | :py:const:`0x04` |
        |                           |                  | :py:const:`bmp280.OSR16`  | :py:const:`0x05` |
        +---------------------------+------------------+---------------------------+------------------+
        :return: sampling rate as string
        """
        string_name = ("OSR_SKIP", "OSR1", "OSR2", "OSR4", "OSR8", "OSR16",)
        return string_name[self._temperature_oversample_rate]

    @temperature_oversample_rate.setter
    def temperature_oversample_rate(self, value: int) -> None:
        if value not in self.temperature_oversample_rate_values:
            raise ValueError("Value must be a valid pressure_oversample_rate: OSR_SKIP,OSR1,OSR2,OSR4,OSR8,OSR16")
        # Get current control register for temp Oversample (3-bit), pressure Oversample (3-bit), powermode (8-bit)
        current_control_register = self._control_register
        # only update temperature oversample
        current_control_register = (current_control_register & 0x1f) + (self._translate_osr_bmp280(value) << 5)
        # Write whole control register at once
        self._config_register = 0x00
        self._control_register = current_control_register

    def _get_raw_temp_pressure(self):
        raw_data = self._d
        t_xlsb = (raw_data >> 40) & 0xFF
        t_lsb = (raw_data >> 32) & 0xFF
        t_msb = (raw_data >> 24) & 0xFF
        p_xlsb = (raw_data >> 16) & 0xFF
        p_lsb = (raw_data >> 8) & 0xFF
        p_msb = raw_data & 0xFF
        self._p_raw = (p_msb << 12) | (p_lsb << 4) | (p_xlsb >> 4)
        self._t_raw = (t_msb << 12) | (t_lsb << 4) | (t_xlsb >> 4)
        return self._t_raw, self._p_raw

    def _calculate_temperature_compensation_bmp280(self, raw_temp: float) -> float:
        var1 = (((raw_temp / 16384) - (self.t1 / 1024)) * self.t2)
        var2 = ((((raw_temp / 131072) - (self.t1 / 8192)) *
                 ((raw_temp / 131072) - (self.t1 / 8192))) * self.t3)
        self.t_fine = int(var1 + var2)  # Store t_fine as an instance variable
        tempc = (var1 + var2) / 5120.0
        return tempc

    def _calculate_pressure_compensation_bmp280(self, raw_pressure: float, tempc: float) -> float:
        var1 = (self.t_fine / 2.0) - 64000
        var2 = var1 * var1 * self.p6 / 32768
        var2 += var1 * self.p5 * 2.0
        var2 = (var2 / 4.0) + (self.p4 * 65536)
        var1 = ((self.p3 * var1 * var1 / 524288) + (self.p2 * var1)) / 524288
        var1 = (1.0 + var1 / 32768) * self.p1

        if var1 == 0.0:
            return 0  # Avoid division by zero

        p = 1048576.0 - raw_pressure
        p = (p - (var2 / 4096)) * 6250 / var1
        var1 = self.p9 * p * p / 2147483648
        var2 = p * self.p8 / 32768

        return p + (var1 + var2 + self.p7) / 16.0

    @property
    def temperature(self) -> float:
        """
        The temperature sensor in Celsius
        :return: Temperature in Celsius
        """
        raw_temp, raw_pressure = self._get_raw_temp_pressure()
        return self._calculate_temperature_compensation_bmp280(raw_temp)

    @property
    def pressure(self) -> float:
        """
        The sensor pressure in hPa
        :return: Pressure in hPa
        """
        raw_temp, raw_pressure = self._get_raw_temp_pressure()

        tempc = self._calculate_temperature_compensation_bmp280(raw_temp)
        comp_press = self._calculate_pressure_compensation_bmp280(raw_pressure, tempc)
        return comp_press / 100.0  # Convert to hPa

class BME280(BMP280):
    """Driver for the BME280 Sensor connected over I2C.

    :param ~machine.I2C i2c: The I2C bus the BMP280 is connected to.
    :param int address: The I2C device address. Defaults to :const:`0x7F`

    :raises RuntimeError: if the sensor is not found

     **Quickstart: Importing and using the device**

    .. code-block:: python

        from machine import Pin, I2C
        from micropython_bmpxxx import bmpxxx

    Once this is done you can define your `machine.I2C` object and define your sensor object

    .. code-block:: python

        i2c = I2C(1, sda=Pin(2), scl=Pin(3))
        bme = bmpxxx.BME280(i2c)

    Now you have access to the attributes,
    NOTE: ONLY this BME280 sensor has humidity measurements !!

    .. code-block:: python

        press = bme.pressure
        temp = bme.temperature
        humid = bme.humidity
        dew = bme.dew_point

        # Highest recommended resolution for bme280
        bmp.pressure_oversample_rate = bmp.OSR16
        bmp.temperature_oversample_rate = bmp.OSR2
        meters = bmp.altitude
    """
    # Power Modes for BME280
    power_mode_values = (STANDBY, FORCED, NORMAL)
    BME280_NORMAL_POWER = const(0x03)
    BME280_FORCED_POWER = const(0x01)

    # oversampling rates
    # Below we give OSR_SKIP a unique value 0x05, but will remap it to bmp280 values
    # When we get       OSR1=0, OSR2=1, OSR4=2, OSR8=3, OSR16=4, OSR_SKIP=5
    # input to BMP280,  OSR1=1, OSR2=2, OSR4=3, OSR8=4, OSR16=5, OSR_SKIP=0
    # this will be translated in _translate_osr_bmp280
    # OSR_SKIP = const(0x05)

    # OSR_SKIP turns off sampling and we do not present it as setable from outside the driver
    pressure_oversample_rate_values = (OSR1, OSR2, OSR4, OSR8, OSR16)
    temperature_oversample_rate_values = (OSR1, OSR2, OSR4, OSR8, OSR16)

    BMP280_I2C_ADDRESS_DEFAULT = 0x77
    BMP280_I2C_ADDRESS_SECONDARY = 0x76

    ###  BME280 Constants - notice very different than bmp581
    _REG_WHOAMI_BME280 = const(0xd0)
    _PWR_CTRL_BME280 = const(0x1b)
    _HUMID_CONTROL_REGISTER_BME280 = const(0xF2)
    _CONTROL_REGISTER_BME280 = const(0xF4)
    _CONFIG_BME280 = const(0xf5)
    _RESET_BME280 = const(0xe0)
    _TRIM_COEFF_BME280 = const(0x88)
    _TRIM_HUMDID_COEFF_BME280 = const(0xe1)
    

    _device_id = RegisterStruct(_REG_WHOAMI_BME280, "B")

    _mode = CBits(2, _CONTROL_REGISTER_BME280, 0)
    _pressure_oversample_rate = CBits(3, _CONTROL_REGISTER_BME280, 2)
    _temperature_oversample_rate = CBits(3, _CONTROL_REGISTER_BME280, 5)
    _humidity_oversample_rate = CBits(3, _HUMID_CONTROL_REGISTER_BME280, 0)
    _humid_control_register = CBits(3, _HUMID_CONTROL_REGISTER_BME280, 0)
    _control_register = CBits(8, _CONTROL_REGISTER_BME280, 0)
    _config_register = CBits(8, _CONFIG_BME280, 0)
    _reset_register = CBits(8, _RESET_BME280, 0)
    _iir_coefficient = CBits(3, _CONFIG_BME280, 2)

    # read pressure 0xf7, temp 0xfa, humidity 0xfd
    _d = CBits(64, 0xf7, 0, 8)

    def __init__(self, i2c, address: int = None) -> None:
        time.sleep_ms(3)  # t_powup done in 2ms

        # If no address is provided, try the default, then secondary
        if address is None:
            if self._check_address(i2c, self.BME280_I2C_ADDRESS_DEFAULT):
                address = self.BME280_I2C_ADDRESS_DEFAULT
            elif self._check_address(i2c, self.BME280_I2C_ADDRESS_SECONDARY):
                address = self.BME280_I2C_ADDRESS_SECONDARY
            else:
                raise RuntimeError("BME280 sensor not found at I2C expected address (0x77,0x76).")
        else:
            # Check if the specified address is valid
            if not self._check_address(i2c, address):
                raise RuntimeError(f"BME280 sensor not found at specified I2C address ({hex(address)}).")

        self._i2c = i2c
        self._address = address
        if self._read_device_id() != 0x60:  # check _device_id after i2c established
            raise RuntimeError("Failed to find the BME280 sensor with id 0x60")

        self._reset_register_BME280 = _SOFTRESET
        time.sleep_ms(5)  # soft reset finishes in ?ms

        self._read_calibration_bme280()

        # To start measurements: temp OSR1, pressure OSR1 must be init with Normal power mode
        # set all values at onc
        self._config_register = 0x00
        self._humid_control_register = self._translate_osr_bmp280(OSR1)
        self._control_register = (self._translate_osr_bmp280(OSR1) << 5) + (
                self._translate_osr_bmp280(OSR1) << 2) + BME280_NORMAL_POWER
        _ = self.pressure

        time.sleep_ms(4)  # mode change takes 3ms
        time.sleep_ms(63)  # OSR can be take up to 62.5ms standby

        self.t_fine = 0
        self.sea_level_pressure = WORLD_AVERAGE_SEA_LEVEL_PRESSURE

    def _read_calibration_bme280(self):
        """
        Read & save the calibration coefficients
        Unpack data specified in string: "<<HhhHhhhhhhhh"
            Little-endian (<), 16-bit unsigned (H), 16-bit unsigned (H), 8-bit signed (b), 16-bit signed (h)
        """
        coeff = self._i2c.readfrom_mem(self._address, _TRIM_COEFF_BME280, 26)
        values = struct.unpack("<HhhHhhhhhhhhBB", coeff)
        self.t1, self.t2, self.t3, self.p1, self.p2, self.p3, self.p4, self.p5, self.p6, self.p7, self.p8, self.p9, _, self.h1 = values

        coeff = self._i2c.readfrom_mem(self._address, _TRIM_HUMDID_COEFF_BME280, 7)
        values = struct.unpack("<hBbhb", coeff)
        self.h2, self.h3, self.h4, self.h5, self.h6 = values
        # convert h4, h5, allow for signed values
        self.h4 = (self.h4 * 16) + (self.h5 & 0xF)
        self.h5 //= 16

        # values for one of sensors in comments, each sensor different
        #         print(f"t1 (16-bit unsigned, H): {self.t1}")    # 27753
        #         print(f"t2 (16-bit signed, h): {self.t2}")      # 26492
        #         print(f"t3 (16-bit signed, h): {self.t3}")      # -1000
        #         print(f"p1 (16-bit unsigned, H): {self.p1}")    # 37585
        #         print(f"p2 (16-bit signed, h): {self.p2}")      # -10627
        #         print(f"p3 (16-bit signed, h): {self.p3}")      # 3024
        #         print(f"p4 (16-bit signed, h): {self.p4}")      # 9631
        #         print(f"p5 (16-bit signed, h): {self.p5}")      # 119
        #         print(f"p6 (16-bit signed, h): {self.p6}")      # -7
        #         print(f"p7 (16-bit signed, h): {self.p7}")      # 15500
        #         print(f"p8 (16-bit signed, h): {self.p8}")      # -14600
        #         print(f"p9 (16-bit signed, h): {self.p9}")      # 6000
        #         print(f"h1 (8-bit unsigned, B): {self.h1}")     # 75
        #         print(f"h2 (16-bit signed, h): {self.h2}")      # 370
        #         print(f"h3 (8-bit unsigned, B): {self.h3}")     # 0
        #         print(f"h4 (16-bit signed, h): {self.h4}")      # 301
        #         print(f"h5 (8-bit signed, b): {self.h5}")       # 50
        return

    def _get_raw_temp_pressure_humid(self):
        raw_data = self._d
        h_lsb = (raw_data >> 56) & 0xFF
        h_msb = (raw_data >> 48) & 0xFF
        t_xlsb = (raw_data >> 40) & 0xFF
        t_lsb = (raw_data >> 32) & 0xFF
        t_msb = (raw_data >> 24) & 0xFF
        p_xlsb = (raw_data >> 16) & 0xFF
        p_lsb = (raw_data >> 8) & 0xFF
        p_msb = raw_data & 0xFF
        self._p_raw = (p_msb << 12) | (p_lsb << 4) | (p_xlsb >> 4)
        self._t_raw = (t_msb << 12) | (t_lsb << 4) | (t_xlsb >> 4)
        self._h_raw = (h_msb << 8) | h_lsb
        return self._t_raw, self._p_raw, self._h_raw

    def _calculate_humidity_compensation_bme280(self, raw_temp: float, raw_humid: float) -> float:
        var1 = (((raw_temp / 16384) - (self.t1 / 1024)) * self.t2)
        var2 = ((((raw_temp / 131072) - (self.t1 / 8192)) *
                 ((raw_temp / 131072) - (self.t1 / 8192))) * self.t3)
        self.t_fine = int(var1 + var2)  # Store t_fine as an instance variable
        
        h = (self.t_fine - 76800.0)
        h = ((raw_humid - (self.h4 * 64.0 + self.h5 / 16384.0 * h)) *
             (self.h2 / 65536.0 * (1.0 + self.h6 / 67108864.0 * h *
                                       (1.0 + self.h3 / 67108864.0 * h))))
        humidity = h * (1.0 - self.h1 * h / 524288.0)
        if (humidity < 0):
            humidity = 0
        if (humidity > 100):
            humidity = 100.0
        return humidity

    @property
    def temperature(self) -> float:
        """
        The temperature sensor in Celsius
        :return: Temperature in Celsius
        """
        raw_temp, raw_pressure, raw_humid = self._get_raw_temp_pressure_humid()
        return self._calculate_temperature_compensation_bmp280(raw_temp)

    @property
    def pressure(self) -> float:
        """
        The sensor pressure in hPa
        :return: Pressure in hPa
        """
        raw_temp, raw_pressure, raw_humid = self._get_raw_temp_pressure_humid()
        tempc = self._calculate_temperature_compensation_bmp280(raw_temp)
        comp_press = self._calculate_pressure_compensation_bmp280(raw_pressure, tempc)
        return comp_press / 100.0  # Convert to hPa
    
    @property
    def humidity(self) -> float:
        """
        The sensor humidity in %
        :return: humidity in %
        """
        raw_temp, raw_pressure, raw_humid = self._get_raw_temp_pressure_humid()
        return self._calculate_humidity_compensation_bme280(raw_temp, raw_humid)

    def _calculate_dew_point(self, temperature, humidity, pressure) -> float:
        """
        Dew-point calculator uses the Sonntag formula (1990) for water vapor pressure
        https://www.weather.gov/media/epz/wxcalc/rhTdFromWetBulb.pdf
       
        Calculation first determines the saturation vapor pressure (es),
        the wet-bulb vapor pressure (ew), then computes the actual vapor pressure (e)
        using a correction factor involving station pressure.
        Finally, relative humidity and dew point temperature are derived using logarithmic equations.
 
        [Sonntag90] Sonntag D.: Important New Values of the Physical Constants of 1986,
        Vapour Pressure Formulations based on the IST-90 and Psychrometer Formulae;
        Z. Meteorol., 70 (5), pp. 340-344, 1990.
        
        :return: dew point in celsius
        """
        from math import exp, log  
        # Constants from the paper (Sonntag, 1990)
        a = 17.67
        b  = 243.5

        # Compute saturation vapor pressure (es first parenthetical) in hPa
        # Compute actual vapor pressure (e - 2nd parenthetical) in hPa
        # Apply pressure correction factor (3rd parenthetical)
        corrected_e = (6.112 * exp((a * temperature) / (b + temperature))) * (humidity / 100.0) * (pressure / 1013.25)

        # Compute dew point temperature (Td)
        alpha = log(corrected_e / 6.112)
        dew_point = (b * alpha) / (a - alpha)
        return dew_point

    @property
    def dew_point(self) -> float:
        """
        example:
        Sensor pressure = 1008.5769 hPa
        temp = 20.06 C
        humidity = 33.9%
        dew_point = 3.62

        :return: dew point in celsius
        """
        raw_temp, raw_pressure, raw_humid = self._get_raw_temp_pressure_humid()
        t = self._calculate_temperature_compensation_bmp280(raw_temp)
        p = (self._calculate_pressure_compensation_bmp280(raw_pressure, t))/100.0
        h = self._calculate_humidity_compensation_bme280(raw_temp, raw_humid)    
        return self._calculate_dew_point(t, h, p)
