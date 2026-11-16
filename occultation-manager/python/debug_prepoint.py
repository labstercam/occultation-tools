#!/usr/bin/env python
"""
Debug script to test prepoint calculations
"""

import math
from datetime import datetime, timedelta

# Simplified version of the buggy altaz_to_radec method
def buggy_altaz_to_radec(alt_deg, az_deg, lat_deg, lon_deg, utc_time):
    """Buggy version from prepoint_manager.py"""
    # Convert to radians
    alt_rad = math.radians(alt_deg)
    az_rad = math.radians(az_deg)
    lat_rad = math.radians(lat_deg)
    
    # Calculate Declination
    sin_dec = math.sin(alt_rad) * math.sin(lat_rad) + math.cos(alt_rad) * math.cos(lat_rad) * math.cos(az_rad)
    sin_dec = max(-1.0, min(1.0, sin_dec))
    dec_rad = math.asin(sin_dec)
    dec_degrees = math.degrees(dec_rad)
    
    # Calculate Hour Angle (BUGGY!)
    cos_ha = (math.sin(alt_rad) - math.sin(dec_rad) * math.sin(lat_rad)) / (math.cos(dec_rad) * math.cos(lat_rad))
    cos_ha = max(-1.0, min(1.0, cos_ha))
    ha_rad = math.acos(cos_ha)  # This always returns positive [0, π]
    ha_hours = math.degrees(ha_rad) / 15.0
    
    # Determine HA sign based on azimuth (WRONG!)
    # Azimuth: 0° = North, 90° = East, 180° = South, 270° = West
    if az_deg > 180:  # West side (azimuth > 180°)
        ha_hours = -ha_hours
    
    # For testing, just return the hour angle
    return ha_hours, dec_degrees

def fixed_altaz_to_radec(alt_deg, az_deg, lat_deg, lon_deg, utc_time):
    """Fixed version with correct hour angle sign calculation"""
    # Convert to radians
    alt_rad = math.radians(alt_deg)
    az_rad = math.radians(az_deg)
    lat_rad = math.radians(lat_deg)
    
    # Calculate Declination
    sin_dec = math.sin(alt_rad) * math.sin(lat_rad) + math.cos(alt_rad) * math.cos(lat_rad) * math.cos(az_rad)
    sin_dec = max(-1.0, min(1.0, sin_dec))
    dec_rad = math.asin(sin_dec)
    dec_degrees = math.degrees(dec_rad)
    
    # Calculate Hour Angle CORRECTLY using atan2
    sin_ha = -math.sin(az_rad) * math.cos(alt_rad) / math.cos(dec_rad)
    cos_ha = (math.sin(alt_rad) - math.sin(dec_rad) * math.sin(lat_rad)) / (math.cos(dec_rad) * math.cos(lat_rad))
    
    ha_rad = math.atan2(sin_ha, cos_ha)
    ha_hours = math.degrees(ha_rad) / 15.0
    
    return ha_hours, dec_degrees

def test_conversion():
    """Test the conversion with sample values"""
    print("Testing Alt/Az to RA/Dec conversion bug...")
    print("=" * 60)
    
    # Sample values (Wellington, NZ)
    lat = -41.2865  # Wellington latitude
    lon = 174.7762  # Wellington longitude
    
    # Test case 1: Object at meridian (azimuth = 180° or 0°)
    print("\nTest 1: Object at meridian (azimuth = 180°)")
    alt = 45.0
    az = 180.0
    
    ha_buggy, dec_buggy = buggy_altaz_to_radec(alt, az, lat, lon, datetime.utcnow())
    ha_fixed, dec_fixed = fixed_altaz_to_radec(alt, az, lat, lon, datetime.utcnow())
    
    print(f"  Buggy: HA = {ha_buggy:.4f}h, Dec = {dec_buggy:.4f}°")
    print(f"  Fixed: HA = {ha_fixed:.4f}h, Dec = {dec_fixed:.4f}°")
    
    # Test case 2: Object in east (azimuth = 90°)
    print("\nTest 2: Object in east (azimuth = 90°)")
    alt = 45.0
    az = 90.0
    
    ha_buggy, dec_buggy = buggy_altaz_to_radec(alt, az, lat, lon, datetime.utcnow())
    ha_fixed, dec_fixed = fixed_altaz_to_radec(alt, az, lat, lon, datetime.utcnow())
    
    print(f"  Buggy: HA = {ha_buggy:.4f}h, Dec = {dec_buggy:.4f}°")
    print(f"  Fixed: HA = {ha_fixed:.4f}h, Dec = {dec_fixed:.4f}°")
    
    # Test case 3: Object in west (azimuth = 270°)
    print("\nTest 3: Object in west (azimuth = 270°)")
    alt = 45.0
    az = 270.0
    
    ha_buggy, dec_buggy = buggy_altaz_to_radec(alt, az, lat, lon, datetime.utcnow())
    ha_fixed, dec_fixed = fixed_altaz_to_radec(alt, az, lat, lon, datetime.utcnow())
    
    print(f"  Buggy: HA = {ha_buggy:.4f}h, Dec = {dec_buggy:.4f}°")
    print(f"  Fixed: HA = {ha_fixed:.4f}h, Dec = {dec_fixed:.4f}°")
    
    # Test case 4: User's scenario (approximate)
    print("\nTest 4: Simulating user's error scenario")
    # For an object at RA 6.9h, Dec -10.4°, at some time/location
    # Let's test with arbitrary Alt/Az that might produce wrong sign
    alt = 30.0
    az = 120.0  # Southeast
    
    ha_buggy, dec_buggy = buggy_altaz_to_radec(alt, az, lat, lon, datetime.utcnow())
    ha_fixed, dec_fixed = fixed_altaz_to_radec(alt, az, lat, lon, datetime.utcnow())
    
    print(f"  Buggy: HA = {ha_buggy:.4f}h, Dec = {dec_buggy:.4f}°")
    print(f"  Fixed: HA = {ha_fixed:.4f}h, Dec = {dec_fixed:.4f}°")
    print(f"  Difference in HA: {abs(ha_fixed - ha_buggy):.4f}h = {abs(ha_fixed - ha_buggy)*15:.2f}°")
    
    print("\n" + "=" * 60)
    print("Analysis:")
    print("The buggy code uses math.acos() which always returns positive HA.")
    print("Then it tries to assign sign based on azimuth > 180°, which is wrong.")
    print("The correct approach uses math.atan2(sin_ha, cos_ha) to get signed HA.")
    print("This bug would cause RA errors of up to 12 hours (180°).")

if __name__ == "__main__":
    test_conversion()