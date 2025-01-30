import time
from machine import Pin, I2C
from micropython_bmpxxx import bmpxxx

i2c = I2C(id=1, scl=Pin(27), sda=Pin(26), freq=400_000)
    
bme = bmpxxx.BME280(i2c=i2c, address=0x76)
print("BME280 - pressure, temperature, and %humidity")

sea_level_pressure = bme.sea_level_pressure
print(f"Initial sea_level_pressure = {sea_level_pressure:.2f} hPa")

# reset driver to contain the accurate sea level pressure (SLP) from my nearest airport this hour
bme.sea_level_pressure = 1017.0
print(f"Adjusted sea level pressure = {bme.sea_level_pressure:.2f} hPa\n")

bme.pressure_oversample_rate = bme.OSR16
bme.temperature_oversample_rate = bme.OSR8
bme.iir_coefficient = bme.COEF_3

# Alternatively set known altitude in meters and the sea level pressure will be calculated
bme.altitude = 106.0
print(f"Altitude 106m = {bme.altitude:.2f} meters")
print(f"Adjusted SLP based on known altitude = {bme.sea_level_pressure:.2f} hPa\n")
pressure = bme.pressure
print(f"Sensor pressure = {pressure:.4f} hPa")

print("---- loop ----")
while True:    
    # Pressure in hPA measured at sensor, temperature in Celsius
    # NOTE: only the BME280 supports %humidity and dew_point functionality
    pressure = bme.pressure
    print(f"sensor pressure = {pressure:.4f} hPa")
    temp = bme.temperature
    print(f"temp = {temp:.2f} C")
    humid = bme.humidity
    print(f"humidity = {humid:.2f}%")
    dew = bme.dew_point
    print(f"dew_point temperature = {dew:.2f} C")
  
    # Altitude in meters and in feet/inches
    meters = bme.altitude
    print(f"Altitude = {meters:.2f} meters\n")
    feet = meters * 3.28084
    feet_only = int(feet)
    inches = int((feet - feet_only) * 12)
#     print(f"Altitude = {feet_only} feet {inches} inches\n")

    time.sleep(2.0)

