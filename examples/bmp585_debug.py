import time
from machine import Pin, I2C
from micropython_bmpxxx import bmpxxx

i2c = I2C(id=1, scl=Pin(27), sda=Pin(26), freq=400_000)

i2c1_devices = i2c.scan()
if i2c1_devices:
    for d in i2c1_devices: print(f"i2c1 device at address: {hex(d)}")
else:
    print("ERROR: No i2c1 devices")
print("")
    
bmp = bmpxxx.BMP585(i2c=i2c, address=0x47)

# print major driver parameters
bmp.config

bmp.altitude = 111.0
print(f"Altitude 111m = {bmp.altitude:.2f} meters")
print(f"Adjusted SLP based on known altitude = {bmp.sea_level_pressure:.2f} hPa\n")

print("---- loop ----")
while True:
    # altitude in meters based on sea level pressure stored in driver
    sea_level_pressure = bmp.sea_level_pressure
    print(f"Sea level pressure = {sea_level_pressure:.2f} hPa")
    
    # Pressure in hPA measured at sensor, temperature in Celsius
    pressure = bmp.pressure
    print(f"Sensor pressure = {pressure:.2f} hPa")
    temp = bmp.temperature
    print(f"temp = {temp:.2f} C")
  
    # Pressure in hPA measured at sensor
    meters = bmp.altitude
    print(f"Altitude = {meters:.3f} meters\n")

    time.sleep(2.5)

