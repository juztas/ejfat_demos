#!/usr/bin/env python3
"""
CPU Utilization Monitor with Real-time Bar Charts
Displays per-core CPU usage using rich library
Highlights e2sar_perf process usage
"""

import time
import psutil
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from collections import defaultdict


def get_e2sar_processes():
    """Get all e2sar_perf processes with their details"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent']):
        try:
            if proc.info['name'] and 'e2sar_perf' in proc.info['name']:
                cmdline = proc.info['cmdline'] or []

                # Determine if it's receive or send
                mode = ''
                if '--receive' in cmdline or '-r' in cmdline:
                    mode = 'rcv'
                elif '--send' in cmdline or '-s' in cmdline:
                    mode = 'snd'

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


def create_hybrid_bar(total_percent, e2sar_percent, width=25):
    """Create a visual bar with e2sar_perf usage highlighted

    Args:
        total_percent: Total CPU usage on this core
        e2sar_percent: Estimated e2sar_perf CPU usage on this core
        width: Width of the bar in characters
    """
    # Calculate filled portions
    total_filled = int((total_percent / 100) * width)
    e2sar_filled = int((e2sar_percent / 100) * width)

    # Ensure e2sar doesn't exceed total
    e2sar_filled = min(e2sar_filled, total_filled)
    other_filled = total_filled - e2sar_filled
    empty = width - total_filled

    # Build the bar with e2sar in magenta, other in normal color, empty in gray
    color = get_cpu_color(total_percent)

    bar = ""
    if e2sar_filled > 0:
        bar += f"[magenta]{'█' * e2sar_filled}[/magenta]"
    if other_filled > 0:
        bar += f"[{color}]{'█' * other_filled}[/{color}]"
    if empty > 0:
        bar += f"[{color}]{'░' * empty}[/{color}]"

    return bar


def create_cpu_table(cpu_percentages, e2sar_per_core):
    """Create a table with CPU usage bars for each core

    Args:
        cpu_percentages: List of CPU usage per core
        e2sar_per_core: List of estimated e2sar_perf usage per core
    """
    table = Table(show_header=True, header_style="bold magenta", expand=True)
    table.add_column("Core", style="cyan", width=8)
    table.add_column("Usage", width=25)
    table.add_column("Percent", justify="right", width=8)

    for i, percent in enumerate(cpu_percentages):
        color = get_cpu_color(percent)
        e2sar_pct = e2sar_per_core[i] if i < len(e2sar_per_core) else 0
        bar = create_hybrid_bar(percent, e2sar_pct, width=25)

        table.add_row(
            f"Core {i}",
            bar,
            f"[{color}]{percent:.1f}%[/{color}]"
        )

    return table


def create_e2sar_process_table(e2sar_processes):
    """Create a table showing e2sar_perf processes (Option 2)"""
    if not e2sar_processes:
        return Text("No e2sar_perf processes found", style="dim")

    table = Table(show_header=True, header_style="bold cyan", expand=True)
    table.add_column("PID", style="cyan", width=8)
    table.add_column("Mode", style="yellow", width=6)
    table.add_column("CPU %", justify="right", width=10)

    # Sort by CPU usage descending
    sorted_procs = sorted(e2sar_processes, key=lambda x: x['cpu_percent'], reverse=True)

    for proc_info in sorted_procs:
        mode_display = f"[{'green' if proc_info['mode'] == 'rcv' else 'blue'}]{proc_info['mode']}[/]" if proc_info['mode'] else "[dim]-[/dim]"
        cpu_color = get_cpu_color(proc_info['cpu_percent'])

        table.add_row(
            f"{proc_info['pid']}",
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


def generate_display(cpu_percentages, e2sar_processes, e2sar_per_core):
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
        Layout(name="e2sar_procs", size=None),
        Layout(name="stats", size=8),
        Layout(name="bars")
    )

    # Header
    header_text = Text("CPU Utilization Monitor - e2sar_perf Tracking", style="bold white on blue", justify="center")
    layout["header"].update(Panel(header_text))

    # e2sar_perf processes table (Option 2)
    layout["e2sar_procs"].update(Panel(create_e2sar_process_table(e2sar_processes),
                                       title="e2sar_perf Processes", border_style="magenta"))

    # Stats
    layout["stats"].update(Panel(create_overall_stats(cpu_percentages, cpu_freq, total_e2sar_cpu),
                                  title="Overall Statistics", border_style="blue"))

    # CPU bars (Option 3 - hybrid view)
    layout["bars"].update(Panel(create_cpu_table(cpu_percentages, e2sar_per_core),
                                title="Per-Core Usage (magenta=e2sar_perf)", border_style="green"))

    return layout


def estimate_e2sar_per_core(e2sar_processes, num_cores):
    """Estimate e2sar_perf CPU usage per core

    Simple distribution: divide total e2sar CPU across all cores equally
    This is an approximation since we can't easily get exact per-core per-process data
    """
    total_e2sar_cpu = sum(p['cpu_percent'] for p in e2sar_processes)

    # Simple approach: distribute evenly
    per_core = total_e2sar_cpu / num_cores if num_cores > 0 else 0

    return [per_core] * num_cores


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
        e2sar_per_core = estimate_e2sar_per_core(e2sar_processes, num_cores)

        with Live(generate_display(cpu_percentages, e2sar_processes, e2sar_per_core),
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
                e2sar_per_core = estimate_e2sar_per_core(e2sar_processes, num_cores)

                # Update display
                live.update(generate_display(avg_cpu_percentages, e2sar_processes, e2sar_per_core))

    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]Monitor stopped.[/bold yellow]")


if __name__ == "__main__":
    main()
