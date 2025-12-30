"""Quick test of DMS formatting"""

def format_dms(decimal_degrees, is_longitude=True):
    """Convert decimal degrees to DMS format: ±ddd mm ss.s"""
    is_negative = decimal_degrees < 0
    abs_degrees = abs(decimal_degrees)
    
    degrees = int(abs_degrees)
    minutes_decimal = (abs_degrees - degrees) * 60
    minutes = int(minutes_decimal)
    seconds = (minutes_decimal - minutes) * 60
    
    sign = '-' if is_negative else '+'
    
    # Both longitude and latitude use ss.s format (one decimal place)
    if is_longitude:
        return f'{sign}{degrees:03d} {minutes:02d} {seconds:04.1f}'
    else:
        return f'{sign}{degrees:02d} {minutes:02d} {seconds:04.1f}'


# Test cases
print("Testing DMS formatting:")
print(f"Longitude -122.5: {format_dms(-122.5, True)}")
print(f"Longitude +122.5: {format_dms(122.5, True)}")
print(f"Latitude 37.75: {format_dms(37.75, False)}")
print(f"Latitude -37.75: {format_dms(-37.75, False)}")
print(f"Latitude 0.0: {format_dms(0.0, False)}")

# Expected outputs:
# Longitude -122.5: -122 30 00.0
# Latitude 37.75: +037 45 00.0
