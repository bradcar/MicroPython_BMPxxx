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
* All pressures use the hPA metric
* Temperatures use Celsius
* Code enables setting OverSampling, IIR values, and sea level pressure
  * For sea level pressure, the driver defaults to 1013.25 hpa the international accepted world-wide average hPA, but weather causes sea level presssure to vary by more than the range of 990 hPa to 1040 hPA.
  * It is best to set sea level pressure on each use to that of the nearest airport, for example: https://www.weather.gov/wrh/timeseries?site=KPDX
  * Not setting nearest sea level pressure will cause any altitude reading to be way off.
  
## Recommended Oversampling rates fron Bosch datasheets
The table below is Bosch's recommended oversampling pressure and temperature settings for bmp585 and bmp581. Higher sampling rates effect the refresh rate and the power consumption. Please checked the Bosch datasheets for that information https://www.bosch-sensortec.com/products/environmental-sensors/pressure-sensors/

| Oversampling setting | OSR Pressure | Pressure oversampling | Pressure oversampling |
|------------------|------------------|------------------|------------------|
| Lowest Power |  000     | x1     | x1     |
| |  001     | x2     | x1     |
| Standard resolution |  010     | x4     | x1     |
| |  011     | x8     | x1     |
| High resolution    |  100     | x16     | x1     |
| |  101     | x32     | x2     |
| |  110     | x64     | x4     |
| Highest resolution |  111     | x128     | x8     |

The bmp585 and bmp581 do not have recommended IIR filters to go with the table abovel

The table below is Bosch's recommended oversampling pressure and temperature settings for bmp390. There are recommended IIR filter settings for the bmp390 in section 3.5. Filter section, page 17, in bmp390 datasheet

| Oversampling setting | OSR Pressure | Pressure oversampling | Pressure oversampling |
|------------------|------------------|------------------|------------------|
| Ultra low power |  000     | x1     | x1     |
| Low power |  001     | x2     | x1     |
| Standard resolution |  010     | x4     | x1     |
| High resolution |  011     | x8     | x1     |
| Ultra high resolution |  100     | x16     | x2     |
| Highest resolution|  101     | x32     | x2     |

bmp58x.OSR1 corresponds to x1 for all sensors, bmp58x.OSR2 corresponds to x2 for all sensors, bmp58x.OSR4 corresponds to x4 for all sensors, etc.
