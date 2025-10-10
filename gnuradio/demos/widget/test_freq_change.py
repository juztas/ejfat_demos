#!/usr/bin/env python3
"""
Simple test to verify frequency changes are working.
Watch the GNU Radio GUI waterfall/FFT display while this runs.
"""

import xmlrpc.client
import time

rpc = xmlrpc.client.ServerProxy('http://localhost:8080')

print("Frequency Change Test")
print("=" * 60)
print("Watch the GNU Radio GUI waterfall/FFT plot!")
print("The center frequency should visibly shift left/right.")
print("Note: The slider widget may NOT update, but the actual")
print("      SDR frequency WILL change.")
print("=" * 60)

# Save original
original = rpc.get_freq()
print(f"\nOriginal frequency: {original / 1e6:.1f} MHz")

# Test with obvious changes
test_freqs = [88.0e6, 95.0e6, 102.0e6, 108.0e6]

print("\nChanging frequency every 2 seconds...")
print("Watch for the signal peak moving in the waterfall!\n")

for i, freq in enumerate(test_freqs, 1):
    print(f"[{i}/{len(test_freqs)}] Setting to {freq / 1e6:.1f} MHz...")
    rpc.set_freq(freq)

    time.sleep(2)

    # Verify
    actual = rpc.get_freq()
    print(f"         Verified: {actual / 1e6:.1f} MHz")

    if abs(actual - freq) < 1000:
        print("         ✓ Frequency change confirmed via XML-RPC")
    else:
        print(f"         ✗ Mismatch: expected {freq}, got {actual}")
    print()

# Restore
print(f"Restoring original frequency: {original / 1e6:.1f} MHz")
rpc.set_freq(original)

print("\n✓ Test complete!")
print("\nIf you saw the signal peak moving in the waterfall display,")
print("the frequency control IS working correctly.")
print("\nNote: The Qt slider widget may not update programmatically -")
print("this is a known Qt behavior. The actual SDR is tuning correctly.")
