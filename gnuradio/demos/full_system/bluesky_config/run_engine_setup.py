"""
RunEngine setup utilities for headless/GUI-free operation.

This module provides utilities for setting up Bluesky RunEngine with
callbacks that work properly in headless environments (no GUI).
"""

import matplotlib
# Set non-interactive backend BEFORE any other matplotlib imports
matplotlib.use('Agg')

from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback


def create_headless_run_engine():
    """
    Create a RunEngine configured for headless operation.

    This sets up matplotlib to not require a display and configures
    BestEffortCallback to not create interactive plots.

    Returns
    -------
    RE : RunEngine
        Configured RunEngine instance
    bec : BestEffortCallback
        BestEffortCallback configured for non-interactive use
    """
    # Create RunEngine
    RE = RunEngine({})

    # Create BestEffortCallback without plotting
    bec = BestEffortCallback()

    # Disable live plotting to avoid GUI window creation
    bec.disable_plots()

    return RE, bec


def create_standard_run_engine():
    """
    Create a standard RunEngine with full BestEffortCallback.

    Note: This may fail on macOS when run from non-main threads
    due to matplotlib GUI requirements.

    Returns
    -------
    RE : RunEngine
        Configured RunEngine instance
    bec : BestEffortCallback
        BestEffortCallback with live plotting enabled
    """
    # Create RunEngine
    RE = RunEngine({})

    # Create BestEffortCallback with default settings
    bec = BestEffortCallback()

    return RE, bec
