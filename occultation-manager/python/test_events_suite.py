# Full test suite for events.py 
python test_events.py
python test_events_config.py
python test_events_network.py

""" 
What the Tests Verify
Module Imports: All required classes import without errors
Configuration Integration: Config dependencies work correctly
Data Processing: Event data parsing and calculations
File Operations: Save/load JSON functionality
Date/Time Handling: ISO datetime parsing and local time conversion
Filtering Logic: Station filtering and event selection
Edge Cases: Error handling for invalid data
Network Mocking: OWC data processing without real API calls

==================================================
Expected output
Events Module Standalone Test
==================================================
✓ Events module imported successfully

=== Testing EventProcessor ===
✓ EventProcessor created successfully
✓ Save test: Success
✓ Load test: 1 events loaded
  - First event: Test Asteroid - Station ABC
✓ Merge test: 2 events after merge

=== Testing OccultationEvent ===
✓ OccultationEvent created successfully
  - Event name: Test Asteroid - Station ABC
  - Coordinates: 15.5000h, 45.2000°
  - Exposure: 80ms
  - Status: 1d 23h
  - Display name: Test Asteroid
  - Has custom exposure: False
  - Exposure seconds: 0.08
  - After custom exposure: 150ms, custom: True
  - Event datetime: 2024-01-15 14:30:45
  - Local times: GOTO=09:25:45, Event=09:30:45

=== Testing OccultationManager ===
✓ OccultationManager created successfully
✓ Load events test: Success
  - Loaded 2 events
✓ Station list: ['Station ABC', 'Station XYZ']
✓ Filter test: 1 events for station Station ABC
✓ Select all: 1 events selected
✓ Select none: 0 events selected

✓ All tests completed successfully!
"""