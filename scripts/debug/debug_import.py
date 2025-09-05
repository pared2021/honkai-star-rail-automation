#!/usr/bin/env python3

try:
    import sys

    sys.path.insert(0, ".")
    print("Attempting to import test_service_integration...")
    import tests.integration.test_service_integration

    print("Import successful!")
except Exception as e:
    import traceback

    print(f"Import failed with error: {e}")
    print("Full traceback:")
    traceback.print_exc()
