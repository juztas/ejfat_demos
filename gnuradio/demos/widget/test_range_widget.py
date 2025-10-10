#!/usr/bin/env python3
"""Test to inspect RangeWidget internal structure"""

from gnuradio import qtgui
from PyQt5 import Qt, QtCore
import sys

app = Qt.QApplication(sys.argv)

# Create a Range and RangeWidget like the flowgraph does
freq_range = qtgui.Range(88e6, 108e6, 100e3, 98.5e6, 200)
freq_win = qtgui.RangeWidget(freq_range, lambda x: print(f"Callback: {x}"), "Frequency", "counter_slider", float, QtCore.Qt.Horizontal)

# Inspect the widget
print("RangeWidget attributes:")
for attr in dir(freq_win):
    if not attr.startswith('_'):
        print(f"  {attr}")

print("\nLooking for internal widget attributes:")
for attr in ['d_widget', 'd_slider', 'd_spin', 'd_counter', 'widget']:
    if hasattr(freq_win, attr):
        obj = getattr(freq_win, attr)
        print(f"  {attr}: {type(obj)}")
        if hasattr(obj, 'setValue'):
            print(f"    -> has setValue method!")
