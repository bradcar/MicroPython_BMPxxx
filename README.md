# Micropython bmp58x driver
MicroPython Driver for the Bosch BMP585, BMP581, and BMP390 pressure sensors
* Code based on
  * micropython_bmp581 Author(s): Jose D. Montoya, jposada202020
  * github:jposada202020/MicroPython_BMP581
  * Corrected error in altitude calculation
* Also based on
  * adafruit_register.i2c_struct. Author(s): Scott Shawcroft
  * adafruit_register.i2c_bits.  Author(s): Scott Shawcroft
 
## Micropython bmp58x driver
Code includes:
* All pressures use the hPA metric.
* Temperatures use Celsius.
* Code enables setting Pressure/Temperature OverSampling and IIR values.
* It also can calculate altitude based on current pressure and sea level pressure.
* On can adjusting sea level pressure setting.
  * For sea level pressure, the driver defaults to 1013.25 hpa the international accepted world-wide average hPA, but weather causes sea level presssure to vary by more than the range of 990 hPa to 1040 hPA.
  * It is best to set sea level pressure on each use to that of the nearest airport, for example: https://www.weather.gov/wrh/timeseries?site=KPDX
  * By not setting nearest local known sea level pressure,  altitude measurements may be way off. Even at 360 feet (111m) altitudes can be off by 1500 feet (500m) depending on the weather.
  
## Recommended Oversampling rates fron Bosch datasheets
The table below is Bosch's recommended oversampling pressure and temperature settings for bmp585 and bmp581. Higher sampling rates effect the refresh rate and the power consumption. Please checked the Bosch datasheets for that information https://www.bosch-sensortec.com/products/environmental-sensors/pressure-sensors/

Table 1: BMP585/BMP581 Recommendations from Bosch
| Oversampling setting | OSR Pressure | Pressure<br /> oversampling | Pressure<br /> oversampling |
| :--- | :---: | :---: | :---: |
| Lowest Power |  000     | x1     | x1     |
| |  001     | x2     | x1     |
| Standard resolution |  010     | x4     | x1     |
| |  011     | x8     | x1     |
| High resolution    |  100     | x16     | x1     |
| |  101     | x32     | x2     |
| |  110     | x64     | x4     |
| Highest resolution |  111     | x128     | x8     |

```
#Highest recommended pressure and temp for bmp581 or bmp585 sensor
bmp.pressure_oversample_rate = bmp.OSR128
bmp.temperature_oversample_rate = bmp.OSR32
```

The bmp585 and bmp581 do not have recommended IIR filters to go with the table abovel

The table below is Bosch's recommended oversampling pressure and temperature settings for bmp390. There are recommended IIR filter settings for the bmp390 in section 3.5. Filter section, page 17, in bmp390 datasheet

Table 2: BMP390 Recommendations from Bosch
| Oversampling setting | OSR Pressure | Pressure<br /> oversampling | Pressure<br /> oversampling |
| :--- | :---: | :---: | :---: |
| Ultra low power |  000     | x1     | x1     |
| Low power |  001     | x2     | x1     |
| Standard resolution |  010     | x4     | x1     |
| High resolution |  011     | x8     | x1     |
| Ultra high resolution |  100     | x16     | x2     |
| Highest resolution|  101     | x32     | x2     |

```
#Highest recommended pressure and temp for bmp390 sensor
bmp.pressure_oversample_rate = bmp.OSR32
bmp.temperature_oversample_rate = bmp.OSR2
```

bmp58x.OSR1 corresponds to x1 for all sensors, bmp58x.OSR2 corresponds to x2 for all sensors, bmp58x.OSR4 corresponds to x4 for all sensors, etc.

## Todos
* add bmp581/bmp585 next
  * Create a subclass BMP585 that inherits from BMP581.
  * Override Device-Specific Attributes or Methods: If the BMP581 differs in specific register addresses, initialization parameters, or data handling, override these in the BMP581 class.
  * ```
    class BMP585(BMP581):
    """Driver for the BMP585 Sensor connected over I2C.

    :param ~machine.I2C i2c: The I2C bus the BMP581 is connected to.
    :param int address: The I2C device address. Defaults to :const:`0x47`

    **Example Usage**

    .. code-block:: python

        from machine import Pin, I2C
        from micropython_bmp58z import bmp585

        i2c = I2C(1, sda=Pin(2), scl=Pin(3))
        bmp = bmp585.BMP585(i2c)

    """

    def __init__(self, i2c, address: int = 0x47) -> None:
        super().__init__(i2c, address)

        # Check if the device is actually a BMP585
        if self._device_id != 0x51:  
            raise RuntimeError("Failed to find the BMP585 sensor")
        
        # Initialize any BMP581-specific attributes or configurations
        # For example, register differences on constant differences

    # Override or add any BMP581-specific methods or properties as needed.
    ```
* then add the bmp390 as a sub-class, be very careful because of the many specific changes
