"""
Data visualization utilities for Bluesky experiments.

This module provides functions to plot and visualize data from
completed experiment runs.
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def plot_run(run, x_key, y_key, title=None, save_path=None):
    """
    Plot data from a single run.

    Parameters
    ----------
    run : BlueskyRun
        Run object from databroker
    x_key : str
        Key for x-axis data
    y_key : str
        Key for y-axis data
    title : str, optional
        Plot title (auto-generated from metadata if None)
    save_path : str or Path, optional
        Path to save figure (shows interactive plot if None)

    Returns
    -------
    fig, ax
        Matplotlib figure and axes objects
    """
    table = run.table()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(table[x_key], table[y_key], 'o-', linewidth=2, markersize=6)

    ax.set_xlabel(x_key, fontsize=12)
    ax.set_ylabel(y_key, fontsize=12)

    if title is None:
        start = run.metadata['start']
        title = f"{start['plan_name']} - {start.get('purpose', 'No description')}"
        title += f"\nRun {start['scan_id']} - UID: {start['uid'][:8]}"

    ax.set_title(title, fontsize=14)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to: {save_path}")

    return fig, ax


def plot_multiple_runs(runs, x_key, y_key, title=None, save_path=None):
    """
    Compare multiple runs on the same plot.

    Parameters
    ----------
    runs : list of BlueskyRun
        List of run objects from databroker
    x_key : str
        Key for x-axis data
    y_key : str
        Key for y-axis data
    title : str, optional
        Plot title
    save_path : str or Path, optional
        Path to save figure

    Returns
    -------
    fig, ax
        Matplotlib figure and axes objects
    """
    fig, ax = plt.subplots(figsize=(12, 7))

    for i, run in enumerate(runs):
        table = run.table()
        start = run.metadata['start']
        label = f"Run {start['scan_id']} - {start.get('sample', 'unknown')}"

        ax.plot(table[x_key], table[y_key], 'o-', label=label, alpha=0.7,
                linewidth=2, markersize=5)

    ax.set_xlabel(x_key, fontsize=12)
    ax.set_ylabel(y_key, fontsize=12)

    if title:
        ax.set_title(title, fontsize=14)
    else:
        ax.set_title("Comparison of Multiple Runs", fontsize=14)

    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to: {save_path}")

    return fig, ax


def plot_heatmap(run, x_key, y_key, z_key, title=None, save_path=None):
    """
    Create 2D heatmap from grid scan data.

    Parameters
    ----------
    run : BlueskyRun
        Run object from databroker
    x_key : str
        Key for x-axis (first motor)
    y_key : str
        Key for y-axis (second motor)
    z_key : str
        Key for color values (detector)
    title : str, optional
        Plot title
    save_path : str or Path, optional
        Path to save figure

    Returns
    -------
    fig, ax
        Matplotlib figure and axes objects
    """
    table = run.table()

    # Reshape data into 2D grid
    x_unique = sorted(table[x_key].unique())
    y_unique = sorted(table[y_key].unique())

    X, Y = np.meshgrid(x_unique, y_unique)
    Z = np.zeros_like(X)

    for i, y_val in enumerate(y_unique):
        for j, x_val in enumerate(x_unique):
            mask = (table[x_key] == x_val) & (table[y_key] == y_val)
            if mask.any():
                Z[i, j] = table[z_key][mask].iloc[0]

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.pcolormesh(X, Y, Z, shading='auto', cmap='viridis')

    ax.set_xlabel(x_key, fontsize=12)
    ax.set_ylabel(y_key, fontsize=12)

    if title is None:
        start = run.metadata['start']
        title = f"{start['plan_name']} - {z_key}"

    ax.set_title(title, fontsize=14)

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label(z_key, fontsize=12)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Heatmap saved to: {save_path}")

    return fig, ax


def plot_time_series(run, y_keys, title=None, save_path=None):
    """
    Plot time series data with multiple signals.

    Parameters
    ----------
    run : BlueskyRun
        Run object from databroker
    y_keys : list of str
        Keys for signals to plot
    title : str, optional
        Plot title
    save_path : str or Path, optional
        Path to save figure

    Returns
    -------
    fig, axes
        Matplotlib figure and axes objects
    """
    table = run.table()

    # Use time as x-axis if available, otherwise use sequence number
    if 'time' in table.columns:
        x_data = table['time'] - table['time'].iloc[0]  # Relative time
        x_label = 'Time (s)'
    else:
        x_data = table.index
        x_label = 'Sequence Number'

    num_plots = len(y_keys)
    fig, axes = plt.subplots(num_plots, 1, figsize=(12, 4*num_plots),
                             sharex=True)

    if num_plots == 1:
        axes = [axes]

    for ax, y_key in zip(axes, y_keys):
        ax.plot(x_data, table[y_key], '-', linewidth=1)
        ax.set_ylabel(y_key, fontsize=11)
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel(x_label, fontsize=12)

    if title is None:
        start = run.metadata['start']
        title = f"Time Series - {start['plan_name']}"

    fig.suptitle(title, fontsize=14)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Time series plot saved to: {save_path}")

    return fig, axes


def plot_scatter(run, x_key, y_key, color_key=None, title=None, save_path=None):
    """
    Create scatter plot with optional color mapping.

    Parameters
    ----------
    run : BlueskyRun
        Run object from databroker
    x_key : str
        Key for x-axis data
    y_key : str
        Key for y-axis data
    color_key : str, optional
        Key for color values
    title : str, optional
        Plot title
    save_path : str or Path, optional
        Path to save figure

    Returns
    -------
    fig, ax
        Matplotlib figure and axes objects
    """
    table = run.table()

    fig, ax = plt.subplots(figsize=(10, 7))

    if color_key:
        scatter = ax.scatter(table[x_key], table[y_key],
                           c=table[color_key], cmap='viridis',
                           s=50, alpha=0.7)
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label(color_key, fontsize=12)
    else:
        ax.scatter(table[x_key], table[y_key], s=50, alpha=0.7)

    ax.set_xlabel(x_key, fontsize=12)
    ax.set_ylabel(y_key, fontsize=12)

    if title is None:
        start = run.metadata['start']
        title = f"Scatter Plot - {start['plan_name']}"

    ax.set_title(title, fontsize=14)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Scatter plot saved to: {save_path}")

    return fig, ax


def create_summary_figure(run, save_path=None):
    """
    Create comprehensive summary figure with multiple subplots.

    Automatically detects data structure and creates appropriate plots.

    Parameters
    ----------
    run : BlueskyRun
        Run object from databroker
    save_path : str or Path, optional
        Path to save figure

    Returns
    -------
    fig
        Matplotlib figure object
    """
    table = run.table()
    start = run.metadata['start']

    # Determine number and type of plots needed
    numeric_columns = table.select_dtypes(include=[np.number]).columns.tolist()

    fig = plt.figure(figsize=(15, 10))
    fig.suptitle(f"{start['plan_name']} - Run {start['scan_id']}\n"
                f"UID: {start['uid'][:8]}", fontsize=16)

    # Main data plot
    ax1 = plt.subplot(2, 2, 1)
    if len(numeric_columns) >= 2:
        ax1.plot(table[numeric_columns[0]], table[numeric_columns[1]], 'o-')
        ax1.set_xlabel(numeric_columns[0])
        ax1.set_ylabel(numeric_columns[1])
        ax1.set_title("Main Data")
        ax1.grid(True, alpha=0.3)

    # Histogram
    ax2 = plt.subplot(2, 2, 2)
    if len(numeric_columns) >= 2:
        ax2.hist(table[numeric_columns[1]], bins=20, alpha=0.7, edgecolor='black')
        ax2.set_xlabel(numeric_columns[1])
        ax2.set_ylabel('Frequency')
        ax2.set_title("Distribution")
        ax2.grid(True, alpha=0.3)

    # Time series (if time available)
    ax3 = plt.subplot(2, 2, 3)
    if 'time' in table.columns and len(numeric_columns) >= 2:
        t = table['time'] - table['time'].iloc[0]
        ax3.plot(t, table[numeric_columns[1]], '-')
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel(numeric_columns[1])
        ax3.set_title("Time Series")
        ax3.grid(True, alpha=0.3)

    # Metadata text
    ax4 = plt.subplot(2, 2, 4)
    ax4.axis('off')
    metadata_text = f"Operator: {start.get('operator', 'N/A')}\n"
    metadata_text += f"Purpose: {start.get('purpose', 'N/A')}\n"
    metadata_text += f"Start time: {start.get('time', 'N/A')}\n"
    metadata_text += f"Plan args: {start.get('plan_args', {})}\n"
    ax4.text(0.1, 0.5, metadata_text, fontsize=11, family='monospace',
             verticalalignment='center')
    ax4.set_title("Metadata")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Summary figure saved to: {save_path}")

    return fig
