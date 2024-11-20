import time
from machine import Pin, I2C
from micropython_bmpxxx import bmpxxx

i2c = I2C(id=1, scl=Pin(27), sda=Pin(26), freq=400_000)
    
bmp = bmpxxx.BMP585(i2c=i2c, address=0x47)

# Set for the Highest resolution for bmp585 & bmp581
bmp.pressure_oversample_rate = bmp.OSR128
bmp.temperature_oversample_rate = bmp.OSR8
print(f"{bmp.pressure_oversample_rate=}")
print(f"{bmp.temperature_oversample_rate=}\n")

# Then overwrite and go throug each oversample rate

print(f"{bmp.pressure_oversample_rate=}")

print("---- loop ----")
while True:
    for pressure_oversample_rate in bmp.pressure_oversample_rate_values:
        bmp.pressure_oversample_rate = pressure_oversample_rate
        print(f"Pressure Oversampling setting: {bmp.pressure_oversample_rate}")
        
        for _ in range(5):
            # Pressure in hPA measured at sensor, temperature in Celsius
            pressure = bmp.pressure
            print(f"Sensor pressure = {pressure:.2f} hPa")
            time.sleep(0.5)
        print()

    time.sleep(2.5)

