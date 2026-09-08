#!/usr/bin/env python3
"""
bmp585_altitude_pi_zero.py

Simple BMP585 Barometer for Pi Zero.

Feature:
    * lib.pi_zero_i2c_bridge_utils - must be in /lib folder
    * the scan_i2c_bus function is included in this test code for Pi Zero

Use nearest airport for sea level pressure
    Ex: Portland updated hourly (7 min before the hour)
        https://www.weather.gov/wrh/timeseries?site=KPDX
"""

import time

from lib.micropython_bmpxxx import bmpxxx
from lib.pi_zero_i2c_bridge_utils import PiZeroI2CBridge


def scan_i2c_bus(i2c_primary):
    print("I2C device Scan...")

    try:
        devices1 = i2c_primary.scan()
        if not devices1:
            print("No I2C1 devices detected (primary). Check your wiring.")
            return None

        print(f"Found {len(devices1)} I2C1 {'device' if len(devices1) == 1 else 'devices'}:")
        for address in devices1:
            addr_hex = hex(address)

            if address in (0x47, 0x46):
                identity = "likely BMP585/581 pressure Sensor"
                bmp_detected = True
            else:
                identity = "unknown device signature"

            print(f"  Device: Hex: {addr_hex} ({address}) -> {identity}")
        print("I2C1 scanning complete\n")

    except RuntimeError as e:
        print(f"I2C Hardware Error during scan: {e}")


# -------------------------------------------------------------------------
def main():
    # Initialize the driver using Pi Zero hardware bridge compatibility layer
    i2c1 = PiZeroI2CBridge("/dev/i2c-1")
    scan_i2c_bus(i2c1)

    try:
        bmp = bmpxxx.BMP585(i2c=i2c1, address=0x47)

        # Configure OverSampling and IIR filter settings
        bmp.pressure_oversample_rate = bmp.OSR4
        bmp.temperature_oversample_rate = bmp.OSR4
        bmp.iir_coefficient = bmp.COEF_1

        sea_level_pressure = bmp.sea_level_pressure
        print(f"Initial sea_level_pressure = {sea_level_pressure:.2f} hPa")

        # Set known reference altitude, example author's home office
        home_office_alt_meters = 110.03  # ~361 feet elevation in meters
        bmp.altitude = home_office_alt_meters
        print(f"Altitude set to = {bmp.altitude:.2f} meters")
        print(f"Adjusted SLP based on known altitude = {bmp.sea_level_pressure:.2f} hPa\n")

        print("\nStart test Loop")

        # State tracking variables
        last_ts_ns = time.perf_counter_ns()
        last_pressure = bmp.pressure

        while True:
            pressure = bmp.pressure
            now_ns = time.perf_counter_ns()

            if pressure != last_pressure:
                elapsed_ms = (now_ns - last_ts_ns) / 1_000_000.0
                print(f"Sensor pressure = {pressure:.4f} hPa last={last_pressure:.4f}, {elapsed_ms:.1f} ms")

                # Update tracking states
                last_ts_ns = now_ns
                last_pressure = pressure

                meters = bmp.altitude
                print(f"Altitude = {meters:.3f} meters")

                temp = bmp.temperature
                print(f"temp = {temp:.2f} C\n")

            # small sleep
            time.sleep(0.005)

    except KeyboardInterrupt:
        print("\nExit on User Interrupt...")
    finally:
        # close bridge interface
        i2c1.close()


if __name__ == "__main__":
    main()
