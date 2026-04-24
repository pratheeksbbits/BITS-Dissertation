# Demonstration of error messages without emoji indicators
import sys

# Simulate error messages that would be shown to users
print("\n" + "="*60)
print("ERROR MESSAGE SAMPLES (No Emoji Indicators)")
print("="*60)

error_messages = [
    "ERROR: Invalid mode. Choose from: interactive, text, all",
    "INFO: Navigating to https://www.google.com...",
    "ERROR: Page load timeout. The website took too long to load (>30s).",
    "ERROR: Failed to navigate to https://invalid-site.xyz",
    "ERROR: Invalid CSS selector or selector not found",
    "WARNING: Failed to process element 5. Skipping...",
    "ERROR: Invalid choice. Please enter 1, 2, 3, or 4. (2 attempts remaining)",
    "ERROR: Maximum retry attempts reached. Exiting...",
    "ERROR: No elements found. Please check:",
    "SUCCESS: File saved successfully!",
    "ERROR: Operation cancelled by user.",
    "WARNING: Failed to add rankings. Continuing without rankings...",
]

for msg in error_messages:
    print(f"  {msg}")

print("\n" + "="*60)
print("All messages are now plain text without emoji indicators")
print("="*60 + "\n")
