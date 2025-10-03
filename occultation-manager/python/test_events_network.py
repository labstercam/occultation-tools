# test_events_network.py - Test with mocked network calls

import json
from datetime import datetime, timedelta

# Mock urllib for testing
class MockResponse:
    def __init__(self, data):
        self.data = json.dumps(data).encode('utf-8')
    
    def read(self):
        return self.data

class MockUrllib:
    @staticmethod
    def urlopen(request):
        # Return sample OWC data
        sample_data = [
            {
                'Id': 12345,
                'Object': 'Test Asteroid',
                'MaxDurSec': 15.0,
                'StarName': 'HD 123456',
                'RAJ2000Hours': 15.5,
                'DEJ2000Deg': 45.2,
                'StarMag': 11.5,
                'MagDrop': 2.1,
                'Stations': [
                    {
                        'IsOwnStation': True,
                        'EventTimeUtc': (datetime.utcnow() + timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%S.000'),
                        'ErrorInTimeSec': 3.0,
                        'StationName': 'Test Station',
                        'Latitude': 40.123,
                        'Longitude': -75.456,
                        'StarAz': 180.0,
                        'StarAlt': 45.0,
                        'CombMag': 11.3
                    }
                ]
            }
        ]
        return MockResponse(sample_data)

# Replace urllib in the events module
import sys
sys.modules['urllib.request'] = MockUrllib()

# Now test with mocked network
print("Testing events module with mocked network...")

try:
    from test_events import MockConfigManager, test_owc_data_processing
    test_owc_data_processing()
    print("✓ Network mock test completed")
except Exception as e:
    print(f"❌ Network mock test failed: {e}")