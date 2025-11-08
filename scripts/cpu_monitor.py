#!/usr/bin/env python3
"""
CPU Utilization Monitor with Real-time Bar Charts
Displays per-core CPU usage using rich library
Highlights e2sar_perf process usage with unique colors per process
"""

import time
import socket
import psutil
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from collections import defaultdict


# Color palette for e2sar_perf processes (light, distinct colors)
PROCESS_COLORS = [
    "bright_magenta",
    "bright_cyan",
    "bright_yellow",
    "bright_green",
    "bright_blue",
    "bright_red",
    "bright_white",
    "yellow"
]


def assign_process_colors(e2sar_processes):
    """Assign a unique color to each e2sar_perf process"""
    color_map = {}
    for idx, proc_info in enumerate(e2sar_processes):
        pid = proc_info['pid']
        # Cycle through colors if we have more than 8 processes
        color_map[pid] = PROCESS_COLORS[idx % len(PROCESS_COLORS)]
    return color_map


def get_e2sar_processes():
    """Get all e2sar_perf processes with their details"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent']):
        try:
            if proc.info['name'] and 'e2sar_perf' in proc.info['name']:
                cmdline = proc.info['cmdline'] or []

                # DEBUG: Print cmdline to help diagnose mode detection
                print(f"DEBUG: PID {proc.info['pid']} cmdline: {cmdline}")

                # Determine if it's receive or send
                mode = ''
                if '--receive' in cmdline or '-r' in cmdline:
                    mode = 'rx'
                elif '--send' in cmdline or '-s' in cmdline:
                    mode = 'tx'

                # DEBUG: Print detected mode
                print(f"DEBUG: PID {proc.info['pid']} detected mode: '{mode}'")

                # Get CPU percent (may need to call cpu_percent() to get non-zero value)
                cpu_pct = proc.cpu_percent(interval=0.1)

                processes.append({
                    'pid': proc.info['pid'],
                    'mode': mode,
                    'cpu_percent': cpu_pct,
                    'proc': proc
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    return processes


def get_cpu_color(percentage):
    """Return color based on CPU usage percentage"""
    if percentage < 50:
        return "green"
    elif percentage < 75:
        return "yellow"
    else:
        return "red"


def create_stacked_bar(total_percent, e2sar_processes, process_colors, per_core_dist, width=25):
    """Create a visual bar with stacked segments for each e2sar_perf process

    Args:
        total_percent: Total CPU usage on this core
        e2sar_processes: List of e2sar_perf process info
        process_colors: Dict mapping PID to color
        per_core_dist: List of (pid, percent) tuples for this core
        width: Width of the bar in characters
    """
    total_filled = int((total_percent / 100) * width)

    # Build segments for each process
    segments = []
    filled_so_far = 0

    for pid, proc_percent in per_core_dist:
        proc_filled = int((proc_percent / 100) * width)
        proc_filled = min(proc_filled, total_filled - filled_so_far)
        if proc_filled > 0:
            color = process_colors.get(pid, "magenta")
            segments.append((color, proc_filled))
            filled_so_far += proc_filled

    # Other processes (non-e2sar)
    other_filled = total_filled - filled_so_far
    empty = width - total_filled

    # Build the bar
    color = get_cpu_color(total_percent)
    bar = ""

    # Add e2sar process segments
    for seg_color, seg_size in segments:
        bar += f"[{seg_color}]{'█' * seg_size}[/{seg_color}]"

    # Add other processes
    if other_filled > 0:
        bar += f"[{color}]{'█' * other_filled}[/{color}]"

    # Add empty space
    if empty > 0:
        bar += f"[{color}]{'░' * empty}[/{color}]"

    return bar


def create_cpu_table(cpu_percentages, e2sar_processes, process_colors, e2sar_per_core_dist):
    """Create a table with CPU usage bars for each core

    Args:
        cpu_percentages: List of CPU usage per core
        e2sar_processes: List of e2sar_perf process info
        process_colors: Dict mapping PID to color
        e2sar_per_core_dist: List of per-core process distributions
    """
    table = Table(show_header=True, header_style="bold magenta", expand=True)
    table.add_column("Core", style="cyan", width=8)
    table.add_column("Usage", width=25)
    table.add_column("Percent", justify="right", width=8)

    for i, percent in enumerate(cpu_percentages):
        color = get_cpu_color(percent)
        per_core_dist = e2sar_per_core_dist[i] if i < len(e2sar_per_core_dist) else []
        bar = create_stacked_bar(percent, e2sar_processes, process_colors, per_core_dist, width=25)

        table.add_row(
            f"Core {i}",
            bar,
            f"[{color}]{percent:.1f}%[/{color}]"
        )

    return table


def create_e2sar_process_table(e2sar_processes, process_colors):
    """Create a table showing e2sar_perf processes without borders"""
    if not e2sar_processes:
        return Text("No e2sar_perf processes found", style="dim")

    # Table without borders
    table = Table(show_header=True, header_style="bold cyan", expand=True,
                  show_edge=False, box=None, padding=(0, 1))
    table.add_column("Mode", style="yellow", width=12)
    table.add_column("CPU %", justify="right", width=10)

    # Sort by CPU usage descending
    sorted_procs = sorted(e2sar_processes, key=lambda x: x['cpu_percent'], reverse=True)

    for proc_info in sorted_procs:
        pid = proc_info['pid']
        color = process_colors.get(pid, "white")

        # Mode with PID and background color matching bar
        if proc_info['mode']:
            mode_display = Text(f"{proc_info['mode']}:{pid}", style=f"black on {color}")
        else:
            mode_display = Text(f"-:{pid}", style="dim")

        cpu_color = get_cpu_color(proc_info['cpu_percent'])

        table.add_row(
            mode_display,
            f"[{cpu_color}]{proc_info['cpu_percent']:.1f}%[/{cpu_color}]"
        )

    return table


def create_overall_stats(cpu_percentages, cpu_freq, total_e2sar_cpu):
    """Create overall CPU statistics"""
    avg_usage = sum(cpu_percentages) / len(cpu_percentages)
    max_usage = max(cpu_percentages)
    min_usage = min(cpu_percentages)

    stats = Table.grid(padding=(0, 2))
    stats.add_column(style="bold cyan")
    stats.add_column(style="white")

    stats.add_row("CPU Cores:", f"{len(cpu_percentages)}")
    stats.add_row("Average Usage:", f"[{get_cpu_color(avg_usage)}]{avg_usage:.1f}%[/{get_cpu_color(avg_usage)}]")
    stats.add_row("Max Usage:", f"[{get_cpu_color(max_usage)}]{max_usage:.1f}%[/{get_cpu_color(max_usage)}]")
    stats.add_row("Min Usage:", f"[{get_cpu_color(min_usage)}]{min_usage:.1f}%[/{get_cpu_color(min_usage)}]")

    # Add e2sar_perf total CPU usage
    if total_e2sar_cpu > 0:
        stats.add_row("e2sar_perf Total:", f"[magenta]{total_e2sar_cpu:.1f}%[/magenta]")

    if cpu_freq:
        stats.add_row("CPU Frequency:", f"{cpu_freq.current:.0f} MHz")

    return stats


def generate_display(cpu_percentages, e2sar_processes, process_colors, e2sar_per_core_dist):
    """Generate the complete display layout"""
    try:
        cpu_freq = psutil.cpu_freq()
    except:
        cpu_freq = None

    # Calculate total e2sar CPU usage
    total_e2sar_cpu = sum(p['cpu_percent'] for p in e2sar_processes)

    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="stats_row", size=12),
        Layout(name="bars")
    )

    # Split stats row into two columns
    layout["stats_row"].split_row(
        Layout(name="stats"),
        Layout(name="e2sar_procs")
    )

    # Header
    hostname = socket.gethostname()
    header_text = Text(f"CPU Utilization - {hostname}", style="bold white on blue", justify="center")
    layout["header"].update(Panel(header_text))

    # Stats (left side)
    layout["stats"].update(Panel(create_overall_stats(cpu_percentages, cpu_freq, total_e2sar_cpu),
                                  title="Overall Statistics", border_style="blue"))

    # e2sar_perf processes table (right side)
    layout["e2sar_procs"].update(Panel(create_e2sar_process_table(e2sar_processes, process_colors),
                                       title="e2sar_perf Processes", border_style="magenta"))

    # CPU bars with stacked process colors
    layout["bars"].update(Panel(create_cpu_table(cpu_percentages, e2sar_processes, process_colors, e2sar_per_core_dist),
                                title="Per-Core Usage (colored by process)", border_style="green"))

    return layout


def estimate_e2sar_per_core_distribution(e2sar_processes, num_cores):
    """Estimate per-core CPU distribution for each e2sar_perf process

    Returns a list where each element is a list of (pid, percent) tuples for that core
    This is an approximation - we distribute each process's CPU evenly across cores
    """
    per_core_dist = [[] for _ in range(num_cores)]

    for proc_info in e2sar_processes:
        pid = proc_info['pid']
        total_cpu = proc_info['cpu_percent']

        # Distribute this process's CPU evenly across all cores
        per_core = total_cpu / num_cores if num_cores > 0 else 0

        for core_idx in range(num_cores):
            if per_core > 0:
                per_core_dist[core_idx].append((pid, per_core))

    return per_core_dist


def main():
    """Main function to run the CPU monitor"""
    console = Console()

    try:
        console.print("\n[bold green]Starting e2sar_perf CPU Monitor...[/bold green]")
        console.print("[dim]Press Ctrl+C to exit[/dim]\n")
        time.sleep(1)

        # Get initial values
        num_cores = psutil.cpu_count()
        cpu_percentages = psutil.cpu_percent(interval=0.1, percpu=True)
        e2sar_processes = get_e2sar_processes()

        # Sort processes by PID to maintain consistent color assignment
        e2sar_processes = sorted(e2sar_processes, key=lambda x: x['pid'])
        process_colors = assign_process_colors(e2sar_processes)
        e2sar_per_core_dist = estimate_e2sar_per_core_distribution(e2sar_processes, num_cores)

        with Live(generate_display(cpu_percentages, e2sar_processes, process_colors, e2sar_per_core_dist),
                  refresh_per_second=0.5, console=console) as live:
            while True:
                # Collect CPU samples over time
                samples = []
                for _ in range(8):
                    sample = psutil.cpu_percent(interval=0.25, percpu=True)
                    samples.append(sample)

                # Calculate average across all samples for each core
                avg_cpu_percentages = []
                for core_idx in range(len(samples[0])):
                    core_avg = sum(sample[core_idx] for sample in samples) / len(samples)
                    avg_cpu_percentages.append(core_avg)

                # Get e2sar_perf processes
                e2sar_processes = get_e2sar_processes()

                # Sort by PID to maintain consistent colors
                e2sar_processes = sorted(e2sar_processes, key=lambda x: x['pid'])
                process_colors = assign_process_colors(e2sar_processes)
                e2sar_per_core_dist = estimate_e2sar_per_core_distribution(e2sar_processes, num_cores)

                # Update display
                live.update(generate_display(avg_cpu_percentages, e2sar_processes, process_colors, e2sar_per_core_dist))

    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]Monitor stopped.[/bold yellow]")


if __name__ == "__main__":
    main()
