import time
from machine import Pin, I2C
from micropython_bmpxxx import bmpxxx

i2c = I2C(id=1, scl=Pin(27), sda=Pin(26), freq=400_000)

# I had to modify my sensor to 0x76 address, if only using default address: bmpxxx.BMP280(i2c=i2c)
bmp = bmpxxx.BMP280(i2c=i2c, address=0x76)

while True:
    # temperature in Celsius
    temp = bmp.temperature
    print(f"temp = {temp:.2f} C")
    
    # Pressure in hPA
    pressure = bmp.pressure
    print(f"Sensor pressure = {pressure:.2f} hPa \n")
    
    time.sleep(1)

