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

# I had to modify my sensor to 0x76 address, if only using default address: bmpxxx.BMP280(i2c=i2c)
bmp = bmpxxx.BMP280(i2c=i2c, address=0x76)

# print major driver parameters
bmp.config

# altitude in meters based on sea level pressure stored in driver
sea_level_pressure = bmp.sea_level_pressure
print(f"Sea level pressure = {sea_level_pressure:.2f} hPa")

# set known altitude in meters and the sea level pressure will be calculated
bmp.altitude = 111.0
print(f"Adjusted SLP using {bmp.altitude:.2f} meter altitude = {bmp.sea_level_pressure:.2f} hPa\n")

print("---- loop ----")

while True: 
    # Pressure in hPA measured at sensor, temperature in Celsius
    pressure = bmp.pressure
    print(f"Sensor pressure = {pressure:.2f} hPa")
    temp = bmp.temperature
    print(f"temp = {temp:.2f} C")
  
    # Pressure in hPA measured at sensor
    meters = bmp.altitude
    print(f"Altitude = {meters:.3f} meters\n")

    time.sleep(2.5)

