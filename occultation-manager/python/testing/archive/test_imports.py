# Test imports to find any syntax/import errors
import sys
import os

print("Testing imports...")

try:
    import config
    print("✓ config imported")
except Exception as e:
    print(f"✗ config failed: {e}")

try:
    import theme
    print("✓ theme imported")
except Exception as e:
    print(f"✗ theme failed: {e}")

try:
    import events
    print("✓ events imported")
except Exception as e:
    print(f"✗ events failed: {e}")

try:
    import templates
    print("✓ templates imported")
except Exception as e:
    print(f"✗ templates failed: {e}")

try:
    import utils
    print("✓ utils imported")
except Exception as e:
    print(f"✗ utils failed: {e}")

try:
    import gui_components
    print("✓ gui_components imported")
except Exception as e:
    print(f"✗ gui_components failed: {e}")

try:
    import gui_dialogs
    print("✓ gui_dialogs imported")
except Exception as e:
    print(f"✗ gui_dialogs failed: {e}")

try:
    import sequence_runner
    print("✓ sequence_runner imported")
except Exception as e:
    print(f"✗ sequence_runner failed: {e}")

try:
    import main_gui
    print("✓ main_gui imported")
except Exception as e:
    print(f"✗ main_gui failed: {e}")

print("\nAll import tests completed!")
