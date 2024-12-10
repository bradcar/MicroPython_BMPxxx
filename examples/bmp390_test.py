import time
from machine import Pin, I2C
from micropython_bmpxxx import bmpxxx

#i2c = I2C(1, sda=Pin(2), scl=Pin(3))  # Correct I2C pins for RP2040
i2c = I2C(id=1, scl=Pin(27), sda=Pin(26))

i2c1_devices = i2c.scan()
if i2c1_devices:
    for d in i2c1_devices: print(f"i2c1 device at address: {hex(d)}")
else:
    print("ERROR: No i2c1 devices")
print("")
    
bmp = bmpxxx.BMP390(i2c=i2c, address=0x76)

sea_level_pressure = bmp.sea_level_pressure
print(f"initial sea_level_pressure = {sea_level_pressure:.2f} hPa")

sea_level_pressure = bmp.sea_level_pressure
print(f"Initial sea_level_pressure = {sea_level_pressure:.2f} hPa")

# reset driver to contain the accurate sea level pressure (SLP) from my nearest airport this hour
bmp.sea_level_pressure = 1017.0
print(f"Adjusted sea level pressure = {bmp.sea_level_pressure:.2f} hPa")

# Alternatively set known altitude in meters and the sea level pressure will be calculated
bmp.altitude = 111.0
print(f"Adjusted SLP using {bmp.altitude:.2f} meter altitude = {bmp.sea_level_pressure:.2f} hPa\n")

while True:
    print(f"Pressure = {bmp.pressure:.2f} hPa")
    temp = bmp.temperature
    print(f"temp = {temp:.2f} C")
  
    meters = bmp.altitude
    print(f"Altitude = {meters:.2f} meters")
    feet = meters * 3.28084
    feet_only = int(feet)
    inches = (feet - feet_only) * 12
    print(f"Altitude = {feet_only} feet {inches:.1f} inches")

    time.sleep(2.5)
 