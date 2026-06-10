import platform
import os

print("--- OS Information ---")
print(f"OS Name: {platform.system()}")
print(f"OS Version: {platform.version()}")
print(f"OS Platform: {platform.platform()}")
print(f"Architecture: {platform.machine()}")

print("\n--- CPU Information ---")
print(f"Processor: {platform.processor()}")
