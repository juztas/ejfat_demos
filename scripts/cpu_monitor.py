#!/usr/bin/env python3
"""
CPU Utilization Monitor with Real-time Bar Charts
Displays per-core CPU usage using rich library
"""

import time
import psutil
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text


def get_cpu_color(percentage):
    """Return color based on CPU usage percentage"""
    if percentage < 50:
        return "green"
    elif percentage < 75:
        return "yellow"
    else:
        return "red"


def create_bar(percentage, width=40):
    """Create a visual bar representation of CPU usage"""
    filled = int((percentage / 100) * width)
    empty = width - filled
    color = get_cpu_color(percentage)

    bar = f"[{color}]{'█' * filled}{'░' * empty}[/{color}]"
    return bar


def create_cpu_table(cpu_percentages):
    """Create a table with CPU usage bars for each core"""
    table = Table(show_header=True, header_style="bold magenta", expand=True)
    table.add_column("Core", style="cyan", width=8)
    table.add_column("Usage", width=50)
    table.add_column("Percent", justify="right", width=8)

    for i, percent in enumerate(cpu_percentages):
        color = get_cpu_color(percent)
        bar = create_bar(percent, width=40)

        table.add_row(
            f"Core {i}",
            bar,
            f"[{color}]{percent:.1f}%[/{color}]"
        )

    return table


def create_overall_stats(cpu_percentages, cpu_freq):
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

    if cpu_freq:
        stats.add_row("CPU Frequency:", f"{cpu_freq.current:.0f} MHz")

    return stats


def generate_display():
    """Generate the complete display layout"""
    cpu_percentages = psutil.cpu_percent(interval=0.1, percpu=True)

    try:
        cpu_freq = psutil.cpu_freq()
    except:
        cpu_freq = None

    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="stats", size=7),
        Layout(name="bars")
    )

    # Header
    header_text = Text("CPU Utilization Monitor", style="bold white on blue", justify="center")
    layout["header"].update(Panel(header_text))

    # Stats
    layout["stats"].update(Panel(create_overall_stats(cpu_percentages, cpu_freq),
                                  title="Overall Statistics", border_style="blue"))

    # CPU bars
    layout["bars"].update(Panel(create_cpu_table(cpu_percentages),
                                title="Per-Core Usage", border_style="green"))

    return layout


def main():
    """Main function to run the CPU monitor"""
    console = Console()

    try:
        console.print("\n[bold green]Starting CPU Monitor...[/bold green]")
        console.print("[dim]Press Ctrl+C to exit[/dim]\n")
        time.sleep(1)

        with Live(generate_display(), refresh_per_second=4, console=console) as live:
            while True:
                time.sleep(0.25)
                live.update(generate_display())

    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]Monitor stopped.[/bold yellow]")


if __name__ == "__main__":
    main()
