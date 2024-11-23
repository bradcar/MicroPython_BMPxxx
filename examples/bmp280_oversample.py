import time
from machine import Pin, I2C
from micropython_bmpxxx import bmpxxx

i2c = I2C(id=1, scl=Pin(27), sda=Pin(26), freq=400_000)

# I had to modify my sensor to 0x76 address, if only using default address: bmpxxx.BMP280(i2c=i2c)
bmp = bmpxxx.BMP280(i2c=i2c, address=0x76)

print(f"{bmp.pressure_oversample_rate_values=}")

# Set for the Highest suggested resolution for bmp280
bmp.pressure_oversample_rate = bmp.OSR16
bmp.temperature_oversample_rate = bmp.OSR2
print(f"{bmp.pressure_oversample_rate=}")
print(f"{bmp.temperature_oversample_rate=}\n")

print(f"{bmp.pressure_oversample_rate_values=}")

# Then overwrite as we cycle through each oversample rate

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

