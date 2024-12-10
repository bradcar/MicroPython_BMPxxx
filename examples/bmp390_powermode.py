import time
from machine import Pin, I2C
from micropython_bmpxxx import bmpxxx

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

# set known altitude in meters and the sea level pressure will be calculated
bmp.altitude = 111.0
print(f"Adjusted SLP using {bmp.altitude:.2f} meter altitude = {bmp.sea_level_pressure:.2f} hPa\n")

print ("Testing 5 iterations in each mode")
print("\n" + "-" * 41)
print("in NORMAL mode, readings will change")
bmp.power_mode = bmp.NORMAL
for _ in range(5):
    temp = bmp.temperature
    meters = bmp.altitude
    print(f"temp = {temp:.2f} C,  Altitude = {meters:.2f} meters")
    time.sleep(1)

print("\n" + "-" * 41)
print("in STANDBY mode, readings will NOT change")
bmp.power_mode = bmp.STANDBY
for _ in range(5):
    temp = bmp.temperature
    meters = bmp.altitude
    print(f"temp = {temp:.2f} C,  Altitude = {meters:.2f} meters")
    time.sleep(1)

print("\n" + "-" * 41)
print("in FORCED mode get one new reading")
print("sensor then goes into STANDBY")
print("but mode still shows FORCED")
print("must set FORCED mode for new reading")
bmp.power_mode = bmp.FORCED
for _ in range(5):
    temp = bmp.temperature
    meters = bmp.altitude
    print(f"temp = {temp:.2f} C,  Altitude = {meters:.2f} meters")
    time.sleep(1)

print("\n" + "-" * 41)
print("in NORMAL mode, readings will change")
bmp.power_mode = bmp.NORMAL
for _ in range(5):
    temp = bmp.temperature
    meters = bmp.altitude
    print(f"temp = {temp:.2f} C,  Altitude = {meters:.2f} meters")
    time.sleep(1)
    