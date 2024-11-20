import time
from machine import Pin, I2C
from micropython_bmpxxx import bmpxxx

i2c = I2C(id=1, scl=Pin(27), sda=Pin(26), freq=400_000)
    
bmp = bmpxxx.BMP585(i2c=i2c, address=0x47)

while True:
    # temperature in Celsius
    temp = bmp.temperature
    print(f"temp = {temp:.2f} C")
    
    # Pressure in hPA
    pressure = bmp.pressure
    print(f"Sensor pressure = {pressure:.2f} hPa \n")
    
    time.sleep(1)

