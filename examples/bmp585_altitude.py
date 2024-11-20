import time
from machine import Pin, I2C
from micropython_bmpxxx import bmpxxx

i2c = I2C(id=1, scl=Pin(27), sda=Pin(26), freq=400_000)
    
bmp = bmpxxx.BMP585(i2c=i2c, address=0x47)

sea_level_pressure = bmp.sea_level_pressure
print(f"Initial sea_level_pressure = {sea_level_pressure:.2f} hPa")

# reset driver to contain the accurate sea level pressure (SLP) from my nearest airport this hour
bmp.sea_level_pressure = 1017.0
print(f"Adjusted sea level pressure = {bmp.sea_level_pressure:.2f} hPa\n")

# Alternatively set known altitude in meters and the sea level pressure will be calculated
bmp.altitude = 111.0
print(f"Altitude 111m = {bmp.altitude:.2f} meters")
print(f"Adjusted SLP based on known altitude = {bmp.sea_level_pressure:.2f} hPa\n")

print("---- loop ----")
while True:    
    # Pressure in hPA measured at sensor, temperature in Celsius
    pressure = bmp.pressure
    print(f"Sensor pressure = {pressure:.2f} hPa")
    temp = bmp.temperature
    print(f"temp = {temp:.2f} C")
  
    # Altitude in meters and in feet/inches
    meters = bmp.altitude
    print(f"Altitude = {meters:.3f} meters")
    feet = meters * 3.28084
    feet_only = int(feet)
    inches = (feet - feet_only) * 12
    print(f"Altitude = {feet_only} feet {inches:.1f} inches\n")

    time.sleep(1)

