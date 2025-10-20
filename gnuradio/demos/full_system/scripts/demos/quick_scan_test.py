#!/usr/bin/env python3
"""
Quick test: Basic frequency scan on real GNU Radio device.

This demonstrates the simplest possible scan using a real device.
"""

import sys
from pathlib import Path

# IMPORTANT: Set matplotlib backend BEFORE importing any bluesky modules
# This prevents GUI thread issues on macOS
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

# Add project root to path (2 levels up from scripts/demos/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky_config.devices import GNURadioSignalGenerator, MockDetector
from bluesky_config.plans import frequency_scan
from bluesky_config.metadata import create_experiment_metadata


def main():
    """Run a simple frequency scan."""
    print("=" * 70)
    print("Basic Frequency Scan on Real GNU Radio Device")
    print("=" * 70)

    # Setup RunEngine
    RE = RunEngine({})

    # Add best effort callback for live feedback
    bec = BestEffortCallback()
    RE.subscribe(bec)

    # Create real GNU Radio device
    print("\nConnecting to GNU Radio (localhost:8080)...")
    sig_gen = GNURadioSignalGenerator('', name='sig_gen',
                                       host='localhost', port=8080)

    # Use mock detector for now (in real setup, this would be SDR receiver)
    detector = MockDetector(name='det', noise_level=0.1)

    # Create metadata
    md = create_experiment_metadata(
        experiment_id='QUICK-SCAN-001',
        purpose='Test basic frequency scan on real GNU Radio device',
        plan_type='frequency_scan',
    )

    # Run scan
    print("\nRunning frequency scan from 1 MHz to 10 MHz (20 points)...")
    print("This will take ~20 seconds (1s settling time per point)")
    print("-" * 70)

    RE(frequency_scan(
        detectors=[detector],
        signal_gen=sig_gen,
        start=1e6,      # 1 MHz
        stop=10e6,      # 10 MHz
        num_points=20   # 20 frequency points
    ), **md)

    print("-" * 70)
    print("✓ Scan completed successfully!")
    print("\nThe scan used the 'frequency_scan' plan which:")
    print("  - Swept from 1 MHz to 10 MHz in 20 steps")
    print("  - Set frequency on GNU Radio via XML-RPC")
    print("  - Waited 1s at each frequency (prevents GNU Radio crashes)")
    print("  - Collected data from the mock detector")
    print("\nYou can view the GNU Radio GUI to see the frequency changing!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
