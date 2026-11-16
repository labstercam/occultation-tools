"""
Test script to verify the prepoint calculation fix
"""
import math
from datetime import datetime, timedelta

from prepoint_manager import PrepointCalculator

# Create calculator with test coordinates (Auckland, NZ)
lat=-36.8
lon=174.7
calculator = PrepointCalculator(lat, lon, elev=0)
print(f"Created calculator with lat={calculator.lat}, lon={calculator.lon}")

# Test sidereal time calculation
test_time = datetime.utcnow()
lst = calculator.calculate_sidereal_time(test_time, calculator.lon)
print(f"Lat: {lat:.1f}\nLong: {lon:.1f}")
print(f"UTC: {test_time} hours")
print(f"Calculated Local Sidereal Time: {lst:.4f} hours")
print(f"SharpCap Sidereal Time: {SharpCap.SiderealTime:.4f} hours")

# Test Alt/Az to RA/Dec conversion
alt = 45
az = 90
print("calculator.altaz_to_radec Debug Log")
ra_back, dec_back = calculator.altaz_to_radec(alt, az, test_time)
print(f'Test Alt={alt:.2f}°, Az={az:.2f}°')
print(f"✓ Converted RA={ra_back}h, Dec={dec_back}° to Alt={alt:.2f}°, Az={az:.2f}°")

# Test conversion back to Alt/Az
print("calculator.ra_dec_to_altaz Debug Log")
alt2, az2 = calculator.ra_dec_to_altaz(ra_back, dec_back, test_time)
print(f"✓ Converted back Alt={alt:.2f}°, Az={az:.2f}°")

# Verify inverse transformation accuracy
alt_error = abs(alt - alt2)
az_error = abs(az - az2)
if alt_error < 0.01 and az_error < 0.1:  # Allow some tolerance
    print(f"✓ Inverse transformation accurate: Alt error={alt_error:.4f}°, Az error={az_error:.2f}°")
else:
    print(f"⚠ Inverse transformation has errors: Alt error={alt_error:.4f}°, Az error={az_error:.2f}°")

#if __name__ == "__main__":
    #test_hour_angle_fix()