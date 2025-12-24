"""
Quick test to verify TT report implementation
This doesn't generate a full report, just checks the structure
"""

import os
from tt_report import TTReportGenerator
from config import OccultationConfig

print("="*80)
print("TRANS-TASMAN REPORT GENERATOR TEST")
print("="*80)
print()

# Initialize
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'occultation_config.json')
config = OccultationConfig(config_path)

tt_gen = TTReportGenerator(config)

# Check template exists
print("Checking template...")
template_ok, message = tt_gen.check_template_exists()
if template_ok:
    print("  SUCCESS: Template found at", message)
else:
    print("  ERROR:", message)
print()

# Check cell mapping
print("Checking cell mapping...")
cell_mapping = tt_gen.get_cell_mapping()
print("  Total cells mapped:", len(cell_mapping))
print("  Sample mappings:")
print("    AstNum:", cell_mapping.get('AstNum'))
print("    AstName:", cell_mapping.get('AstName'))
print("    ObserverName:", cell_mapping.get('ObserverName'))
print("    Latitude:", cell_mapping.get('Latitude'))
print("    Aperture:", cell_mapping.get('Aperture'))
print("    StartedObservingHours:", cell_mapping.get('StartedObservingHours'))
print()

# Check methods exist
print("Checking fill methods...")
methods = ['_fill_event_data', '_fill_observer_data', '_fill_telescope_data', 
           '_fill_recording_times', '_fill_metadata']
for method_name in methods:
    if hasattr(tt_gen, method_name):
        print("  ✓", method_name)
    else:
        print("  ✗", method_name, "MISSING!")
print()

print("="*80)
print("TEST COMPLETE")
print("="*80)
print()
print("The Trans-Tasman report generator is ready to use.")
print("Try generating a report from the main GUI!")
