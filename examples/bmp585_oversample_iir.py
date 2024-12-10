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
    
bmp = bmpxxx.BMP585(i2c=i2c, address=0x47)

hpa_sensor = bmp.pressure
sea_level_pressure = bmp.sea_level_pressure
print(f"Pressure at sensor = {hpa_sensor:.4f} hPa")
print(f"Initial sea_level_pressure = {sea_level_pressure:.2f} hPa")

# Alternatively set known altitude in meters and the sea level pressure will be calculated
bmp.altitude = 111.0
print(f"Adjusted SLP using {bmp.altitude:.2f} meter altitude = {bmp.sea_level_pressure:.2f} hPa\n")

print ("Testing 5 iterations with Default sampling rate")
print(f"{bmp.pressure_oversample_rate=}")
print(f"{bmp.temperature_oversample_rate=}")
print("-" * 41)
for _ in range(5):
    temp = bmp.temperature
    meters = bmp.altitude
    print(f"temp = {temp:.2f} C,  Altitude = {meters:.2f} meters")
    time.sleep(1)
    
# Set for highest resolution for bmp585
bmp.pressure_oversample_rate = bmp.OSR128
bmp.temperature_oversample_rate = bmp.OSR8
bmp.iir_coefficient = bmp.COEF_3
print("\nTesting 5 iterations with highest resolution for bmp585")
print(f"{bmp.pressure_oversample_rate=}")
print(f"{bmp.temperature_oversample_rate=}")
print(f"{bmp.iir_coefficient=}")
print("-" * 41)
for _ in range(5):
    temp = bmp.temperature
    meters = bmp.altitude
    print(f"temp = {temp:.2f} C,  Altitude = {meters:.2f} meters")
    time.sleep(1)
    
# Set for high resolution for bmp585
bmp.pressure_oversample_rate = bmp.OSR32
bmp.temperature_oversample_rate = bmp.OSR2
bmp.iir_coefficient = bmp.COEF_3
print("\nTesting 5 iterations with high resolution for bmp585")
print(f"{bmp.pressure_oversample_rate=}")
print(f"{bmp.temperature_oversample_rate=}")
print(f"{bmp.iir_coefficient=}")
print("-" * 41)
for _ in range(5):
    temp = bmp.temperature
    meters = bmp.altitude
    print(f"temp = {temp:.2f} C,  Altitude = {meters:.2f} meters")
    time.sleep(1)

# Set for standard resolution for bmp585
bmp.pressure_oversample_rate = bmp.OSR4
bmp.temperature_oversample_rate = bmp.OSR1
bmp.iir_coefficient = bmp.COEF_3
print("\nTesting 5 iterations with standard resolution for bmp585")
print(f"{bmp.pressure_oversample_rate=}")
print(f"{bmp.temperature_oversample_rate=}")
print(f"{bmp.iir_coefficient=}")
print("-" * 41)
for _ in range(5):
    temp = bmp.temperature
    meters = bmp.altitude
    print(f"temp = {temp:.2f} C,  Altitude = {meters:.2f} meters")
    time.sleep(1)
    
# Set for lowest power for bmp585
bmp.pressure_oversample_rate = bmp.OSR1
bmp.temperature_oversample_rate = bmp.OSR1
bmp.iir_coefficient = bmp.COEF_0
print("\nTesting 5 iterations with lowest resolution")
print(f"{bmp.pressure_oversample_rate=}")
print(f"{bmp.temperature_oversample_rate=}\n")
print(f"{bmp.iir_coefficient=}")
print("-" * 41)
for _ in range(5):
    temp = bmp.temperature
    meters = bmp.altitude
    print(f"temp = {temp:.2f} C,  Altitude = {meters:.2f} meters")
    time.sleep(1)

# Set for highest resolution for bmp585
bmp.pressure_oversample_rate = bmp.OSR128
bmp.temperature_oversample_rate = bmp.OSR8
bmp.iir_coefficient = bmp.COEF_7
print("\nLoop forever with highest resolution for bmp585")
print(f"{bmp.pressure_oversample_rate=}")
print(f"{bmp.temperature_oversample_rate=}")
print(f"{bmp.iir_coefficient=}")
print("-" * 41)
while True:
    meters = bmp.altitude
    print(f"Altitude = {meters:.3f} meters")
    time.sleep(1)
