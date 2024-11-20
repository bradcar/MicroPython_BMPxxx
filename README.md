# Micropython bmp58x driver
MicroPython Driver for the Bosch ~~BMP585~~ (to test Nov 2024), BMP581, and BMP390 pressure sensors using I2C. It has the ability to adjust sea level pressure and/or the sensors altitude at a known elevation for accurate future tracking.

## Micropython bmp58x driver
Code includes:
* ~~BMP585~~ (to test Nov 18-20, 2024), BMP581, BMP390 supported
* I2C only (driver needs modifications for SDI)
  * checks i2c primary address of 0x47, and then checks secondary 0x46
* All pressures are in hPA.
* All temperatures are in Celsius.
* Code enables setting Pressure/Temperature OverSampling and IIR values.
* It also can calculate altitude based on current pressure and sea level pressure.
* One can adjusting sea level pressure setting to known local measurements.
  * For sea level pressure, the driver defaults to 1013.25 hpa which is the international accepted world-wide average hPa. However you should know that weather causes sea level presssure to typically vary from 990 hPa to 1040 hPA or more.
  * It is best to set sea level pressure on each use to that of the nearest airport, for example: https://www.weather.gov/wrh/timeseries?site=KPDX
  * altitude measurements may be way off if you do not set sea level to the nearest local known sea level pressure at the current time. Even at 360 feet (111m), altitudes can be off by 1500 feet (500m) depending on the weather.
* Various error checks.

## Sample Usage
Required Imports:
```
from machine import Pin, I2C
from micropython_bmp58x import bmp58x
```
Define your machine.I2C object in this case I2C 1 (not 0) and your sensor objects:
```
i2c = I2C(1, sda=Pin(2), scl=Pin(3))
bmp = bmp58x.BMP581(i2c)
```
Access sensor's data:
```
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
```
Increase bmp585/bmp581 sensor to highest accuracy (see below for bmp390):
```
# Highest resolution for bmp585 & bmp581
bmp.pressure_oversample_rate = bmp.OSR128
bmp.temperature_oversample_rate = bmp.OSR8
```
Other data from sensors, see data sheet for more info:
```
print("Current power mode setting: ", bmp.power_mode)
for power_mode in bmp.power_mode_values:
    bmp.power_mode = power_mode
    print(f"New Power mode setting: {bmp.power_mode}")

print(f"Current Output data rate setting: ", bmp.output_data_rate)
for output_data_rate in range(0, 32, 1):
    bmp.output_data_rate = output_data_rate
    print(f"New data rate setting: {bmp.output_data_rate}")

print("Current IIR setting: ", bmp.iir_coefficient)
for iir_coef in bmp.iir_coefficient_values:
    bmp.iir_coefficient = iir_coef
    print(f"New IRR setting: {bmp.iir_coefficient}")
```
## I2C Addresses
If you only have one sensor on the same I2C, they it will use the table below to scan the addresses. If you have multiple devices on the same I2C it is a good practice to specify the sensors address. To change the address to secondary you need to look look up the specs of your specific sensor. Often addresses can be changed with a solder blob or by connecting specific pins on the sensor to ground or vcc. This driver will scan th

Table 1: I2C Sensor Address
| Sensor | Default | Secondary | 
| :---:  | :---:| :---: |
| bmp585 | 0x47 | 0x46  | 
| bmp581 | 0x47 | 0x46  | 
| bmp390 | 0x7f | 0x7e  | 
| bmp280 | 0x77 | 0x76  | 

The following code is useful when scanning for device addresses on I2C. I always put this in my code when bringing up new sensor. Also if device not found triple-check all wiring.
```
# Notice this is using i2c1 not i2c0(typically used for REPL)
i2c = I2C(id=1, scl=Pin(27), sda=Pin(26))
i2c1_devices = i2c.scan()
if i2c1_devices:
    for d in i2c1_devices: print(f"i2c1 device at address: {hex(d)}")
else:
    print("ERROR: No i2c1 devices")
```
Example of specifying an address for a bmp581:
```
bmp = bmp58x.BMP581(i2c=i2c, address=0x47)
```
## Recommended Oversampling Rates to Improve Sensors' Accuracy
The table 2 below is Bosch's recommended oversampling pressure and temperature settings for bmp585 and bmp581. Higher sampling rates effect the refresh rate and the power consumption. Please checked the Bosch datasheets for more information https://www.bosch-sensortec.com/products/environmental-sensors/pressure-sensors/

Table 2: BMP585/BMP581 Recommendations from Bosch
| Oversampling setting | OSR Pressure | Pressure<br /> Oversampling | Temperature<br /> Oversampling |
| :--- | :---: | :---: | :---: |
| Lowest Power |  000     | x1     | x1     |
| |  001  | x2     | x1     |
| Standard resolution |  010     | x4     | x1     |
| |  011  | x8     | x1     |
| High resolution    |  100     | x16     | x1     |
| |  101  | x32     | x2     |
| |  110  | x64     | x4     |
| Highest resolution |  111     | x128     | x8     |

```
#Highest recommended for combined pressure and temperature for bmp581 or bmp585 sensor
bmp.pressure_oversample_rate = bmp.OSR128
bmp.temperature_oversample_rate = bmp.OSR8
```

The bmp585 and bmp581 do not have recommended IIR filters to go with the table above.

The table 3 below is Bosch's recommended oversampling pressure and temperature settings for bmp390. There are recommended IIR filter settings for the bmp390 in section 3.5. Filter section, page 17, in bmp390 datasheet

Table 3: BMP390 Recommendations from Bosch
| Oversampling setting | OSR Pressure | Pressure<br /> Oversampling | Temperature<br /> Oversampling | Sample Use |
| :-------------------- |:---:|:---:|:---:| :--- |
| Ultra low power       | 000 | x1  | x1  | Weather monitoring<br />lowest power, iif off|
| Low power             | 001 | x2  | x1  | Drop detecton, iir off |
| Standard resolution   | 010 | x4  | x1  | Handheld dynamic|
| High resolution       | 011 | x8  | x1  | Drone,<br />low power|
| Ultra high resolution | 100 | x16 | x2  | Indoor navigation|
| Highest resolution    | 101 | x32 | x2  | Highest, Drone accurate |

```
# Highest recommended for combined pressure and temperature for bmp390 sensor
# Indoor Navigation page 17 of bmp390 datasheet
bmp.pressure_oversample_rate = bmp.OSR32
bmp.temperature_oversample_rate = bmp.OSR2
bmp.iir_coefficient = bmp.COEF_3
```
bmp.OSR1 corresponds to x1 for all sensors, bmp.OSR2 corresponds to x2 for all sensors, bmp.OSR4 corresponds to x4 for all sensors, etc. If you go over for a particular sensor, then an error message will show possible values.

## Installing
Make sure the a directory called micropython_bmp58x is on your Raspberry Pi under the /lib directory. You will need to make sure it contains these files: __init__.py, bmp58x.py, and i2c_helpers.py.

## Example projects using this Driver
* Digital altimeter: https://github.com/bradcar/digital-altimeter-rp2

## Bosch Sensors Compared
* Bosch BMP585, MEMS-based barometric pressure sensor, perf similar to BMP581, released 2023.
  * Liquid resistant due to gel sensor
  * The BMP585 accuracy similar to Bosch’s existing BMP581.
    * Measure change in height of just a few centimeters. 
    * Relative accuracy of +/-0.06 hPa and typical absolute accuracy of +/-0.5 hPa.
* The BMP581, capacitive-based barometric pressure sensor, released 2022. 
  * The BMP581 accuracy similar to Bosch’s existing BMP585.
    * Measure change in height of just a few centimeters. 
    * Relative accuracy of +/-0.06 hPa and typical absolute accuracy of +/-0.3 hPa.
  * the BMP581 vs. BMP390: draws 85% less current, noise is 80% lower, and temperature coefficient offset is reduced by 33%.
* Bosch BMP390, previous generation, released 2021.
  * Relative accuracy of +/-0.03 hPa and typical absolute accuracy of +/-0.5 hPa.
  * Measure change in height of 0.25 meters.

## To Test in Nov 2024 with BMP585 Shuttle Board
Bosch makes the BMP585 shuttle board, but it must be wired as below to use the I2C interface with Raspberry Pi. Shuttleboard pin details: https://www.electroniclinic.com/bosch-bmp585-barometric-pressure-sensor-with-arduino/
* 1.27mm pins not breadboard friendly (boardboards use 2.54mm)
* 3.3v:
  * vdd to 3.3v (pin 1 of 7 pin connector)
  * vddio to 3.3v (pin 2 of 7 pin connector)
* gnd:
  * wire gnd to ground (pins 3 of 7 pin connector)
* CS for I2C mode:
  * wire to 3.3v (pin 1 of 9 pin connector)
* SCK/SCL: I2C SCL (pin 2 of 9 pin connector)
* SDO for I2C mode:
  * wire to 3.3v  (pin 3 of 9 pin connector)
* SDI/SDA: I2C SDA (pin 4 of 9 pin connector)

## License Information
This product is open source. Please review the LICENSE.md file for license information.
* distributed as-is; no warranty is given.
 
## Credits
Code based on great work by Jose & Scott!
* micropython_bmp581 Author(s): Jose D. Montoya, jposada202020
  * github:jposada202020/MicroPython_BMP581
  * Corrected error in altitude calculation, also removed limitation of only 0.1m accuracy.
* Also based on
  * adafruit_register.i2c_struct, adafruit_register.i2c_bits.  Author(s): Scott Shawcroft

## Todos
* test/debug bmp585 subclass after delivery of bmp585 on 19-Nov-2024.
* ~~fix IIR filters for bmp585 & bmp581 - currently tries to set IIR when running (but this is ignored), need to change code to go into STANDBY power modem and then update, then return to previous power mode.~~
* double check IIR filters to make sure limited to correct values for bmp390, note can update IIR on bmp390 on the fly.
* started to add code for bmp280 (going down sensor rabit hole...), untested awaiting sensor
* IIR code for  bmp585 & bmp581 uses the same IIR for pressure and temperature, this simplifies control and is like bmp280 & bmp390 sensors, but takes away flexibility for newer sensors.
* added bmp.config to print out all major variables & settings, open question: should this stay?
