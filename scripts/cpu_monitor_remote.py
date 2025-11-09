#!/usr/bin/env python3
"""
Remote CPU Monitor - SSH tunnel version
Runs data collection remotely, displays locally
"""

import time
import sys
import json
import socket
import psutil
import subprocess
import argparse

# Import rich only when needed (not in remote collector mode)
# This allows remote collector to run without rich module
Console = None
Live = None
Text = None
Table = None
Panel = None
Layout = None

def import_rich():
    """Import rich modules when needed for display"""
    global Console, Live, Text, Table, Panel, Layout
    from rich.console import Console
    from rich.live import Live
    from rich.text import Text
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout


# Color palette for e2sar_perf processes
PROCESS_COLORS = [
    "bright_magenta",
    "bright_cyan",
    "bright_yellow",
    "bright_green",
    "bright_blue",
    "bright_red",
]


def get_cpu_color(percentage):
    """Return color based on CPU usage percentage"""
    if percentage < 50:
        return "green"
    elif percentage < 75:
        return "yellow"
    else:
        return "red"


# ============================================================================
# REMOTE MODE: Data Collection (outputs JSON)
# ============================================================================

def get_network_rates():
    """Get network rates using sar -n DEV"""
    rates = {}
    try:
        # Run sar for 1 second, 1 sample
        result = subprocess.run(
            ['sar', '-n', 'DEV', '1', '1'],
            capture_output=True,
            text=True,
            timeout=3
        )

        if result.returncode == 0:
            # Parse sar output
            # Look for Average: lines which have the format:
            # Average:  IFACE  rxpck/s txpck/s rxkB/s txkB/s ...
            for line in result.stdout.split('\n'):
                if line.startswith('Average:') and 'IFACE' not in line:
                    parts = line.split()
                    if len(parts) >= 6:
                        iface = parts[1]

                        # Skip loopback
                        if iface == 'lo':
                            continue
                        # Skip VLAN interfaces to avoid double-counting
                        if '.' in iface:
                            continue
                        # Skip docker and virtual interfaces
                        if iface.startswith('docker') or iface.startswith('veth'):
                            continue

                        # Extract rxkB/s (index 4) and txkB/s (index 5)
                        try:
                            rx_kbps = float(parts[4])
                            tx_kbps = float(parts[5])

                            # Convert kB/s to Gbps (kB/s * 8 / 1e6)
                            rx_gbps = rx_kbps * 8 / 1e6
                            tx_gbps = tx_kbps * 8 / 1e6

                            rates[iface] = {'rx_gbps': rx_gbps, 'tx_gbps': tx_gbps}
                        except (ValueError, IndexError):
                            continue
    except Exception:
        pass

    return rates

def collect_cpu_data():
    """Collect CPU and e2sar process data, return as dict"""
    # Collect 8 samples over 2 seconds
    samples = []
    for _ in range(8):
        sample = psutil.cpu_percent(interval=0.25, percpu=True)
        samples.append(sample)

    # Average samples
    avg_cpu_percentages = []
    for core_idx in range(len(samples[0])):
        core_avg = sum(s[core_idx] for s in samples) / len(samples)
        avg_cpu_percentages.append(core_avg)

    # Get e2sar processes
    e2sar_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent']):
        try:
            if proc.info['name'] and 'e2sar_perf' in proc.info['name']:
                cmdline = proc.info['cmdline'] or []

                mode = ''
                if '--recv' in cmdline or '--receive' in cmdline or '-r' in cmdline:
                    mode = 'rx'
                elif '--send' in cmdline or '-s' in cmdline:
                    mode = 'tx'

                cpu_pct = proc.cpu_percent(interval=0.1)

                e2sar_processes.append({
                    'pid': proc.info['pid'],
                    'mode': mode,
                    'cpu_percent': cpu_pct,
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    # Get network rates (sar does 1-second sample internally)
    net_rates = get_network_rates()

    return {
        'hostname': socket.gethostname(),
        'cpu_percentages': avg_cpu_percentages,
        'e2sar_processes': e2sar_processes,
        'net_rates': net_rates,
        'timestamp': time.time()
    }


def run_remote_collector():
    """Run in remote mode - continuously output JSON data with heartbeat monitoring"""
    import select

    last_heartbeat = time.time()
    heartbeat_timeout = 10  # Exit if no heartbeat for 10 seconds

    while True:
        try:
            # Check for heartbeat on stdin (non-blocking)
            if select.select([sys.stdin], [], [], 0)[0]:
                line = sys.stdin.readline()
                if line.strip() == 'HEARTBEAT':
                    last_heartbeat = time.time()
                elif not line:  # EOF - stdin closed
                    break

            # Check if heartbeat timeout exceeded
            if time.time() - last_heartbeat > heartbeat_timeout:
                print(json.dumps({'error': 'Heartbeat timeout - exiting'}), file=sys.stderr, flush=True)
                break

            data = collect_cpu_data()
            print(json.dumps(data), flush=True)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(json.dumps({'error': str(e)}), file=sys.stderr, flush=True)


# ============================================================================
# LOCAL MODE: Visualization (reads JSON)
# ============================================================================

def assign_process_colors(e2sar_processes):
    """Assign a unique color to each e2sar_perf process"""
    color_map = {}
    for idx, proc_info in enumerate(e2sar_processes):
        pid = proc_info['pid']
        color_map[pid] = PROCESS_COLORS[idx % len(PROCESS_COLORS)]
    return color_map


def create_simple_bar(percent, width=20):
    """Create a simple CPU usage bar"""
    filled = int((percent / 100) * width)
    empty = width - filled

    color = get_cpu_color(percent)
    bar = f"[{color}]{'█' * filled}{'░' * empty}[/{color}]"

    return bar


def create_cpu_table(cpu_percentages):
    """Create a table with CPU usage bars for each core"""
    table = Table(show_header=True, header_style="bold magenta", expand=False, padding=(0, 0))
    table.add_column("Core", style="cyan", width=8)
    table.add_column("Usage", width=20, no_wrap=True)

    for i, percent in enumerate(cpu_percentages):
        bar = create_simple_bar(percent, width=20)
        table.add_row(
            f"Core {i}",
            bar
        )

    return table


def create_overall_stats(cpu_percentages, total_e2sar_cpu):
    """Create overall CPU statistics"""
    if not cpu_percentages:
        return Text("No data", style="dim")

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

    if total_e2sar_cpu > 0:
        stats.add_row("e2sar_perf Total:", f"[magenta]{total_e2sar_cpu:.1f}%[/magenta]")

    return stats


def create_e2sar_process_table(e2sar_processes, process_colors):
    """Create a table showing e2sar_perf processes"""
    if not e2sar_processes:
        return Text("No e2sar_perf processes found", style="dim")

    # Count tx and rx processes
    tx_count = sum(1 for p in e2sar_processes if p['mode'] == 'tx')
    rx_count = sum(1 for p in e2sar_processes if p['mode'] == 'rx')

    table = Table(show_header=True, header_style="bold cyan", expand=False,
                  show_edge=False, box=None, padding=(0, 1))
    table.add_column("Mode", style="yellow", width=12)
    table.add_column("CPU %", justify="right", width=6)

    sorted_procs = sorted(e2sar_processes, key=lambda x: x['cpu_percent'], reverse=True)

    # Limit to 8 processes
    for proc_info in sorted_procs[:8]:
        pid = proc_info['pid']
        color = process_colors.get(pid, "white")

        if proc_info['mode']:
            mode_display = Text(f"{proc_info['mode']}:{pid}", style=f"black on {color}")
        else:
            mode_display = Text(f"-:{pid}", style="dim")

        cpu_color = get_cpu_color(proc_info['cpu_percent'])

        table.add_row(
            mode_display,
            f"[{cpu_color}]{proc_info['cpu_percent']:.1f}%[/{cpu_color}]"
        )

    # Add summary row with counts
    table.add_row(
        Text("─" * 12, style="dim"),
        Text("─" * 6, style="dim")
    )
    table.add_row(
        f"[bold cyan]Total: {len(e2sar_processes)}[/bold cyan]",
        ""
    )
    if tx_count > 0 or rx_count > 0:
        table.add_row(
            f"[green]TX: {tx_count}  RX: {rx_count}[/green]",
            ""
        )

    return table


def generate_display(data):
    """Generate display from data dict"""
    hostname = data.get('hostname', 'unknown').split('.')[0]
    cpu_percentages = data.get('cpu_percentages', [])
    e2sar_processes = data.get('e2sar_processes', [])
    net_rates = data.get('net_rates', {})

    # Sort and assign colors for e2sar process table
    e2sar_processes = sorted(e2sar_processes, key=lambda x: x['pid'])
    process_colors = assign_process_colors(e2sar_processes)

    # Calculate total network rates across all interfaces
    total_rx_gbps = sum(r['rx_gbps'] for r in net_rates.values()) if net_rates else 0
    total_tx_gbps = sum(r['tx_gbps'] for r in net_rates.values()) if net_rates else 0

    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=4),
        Layout(name="e2sar_procs", size=11),
        Layout(name="bars")
    )

    # Header with network rates
    header_text = Text(f"CPU - {hostname}", style="bold white on blue", justify="center")

    # Network rates text
    if net_rates:
        net_text = Text(f"RX: {total_rx_gbps:.2f} Gbps  TX: {total_tx_gbps:.2f} Gbps", style="cyan", justify="center")
    else:
        net_text = Text("Network: --", style="dim", justify="center")

    # Combine header and network text
    header_content = Table.grid()
    header_content.add_row(header_text)
    header_content.add_row(net_text)

    layout["header"].update(Panel(header_content, border_style="blue"))

    # e2sar_perf processes table
    layout["e2sar_procs"].update(Panel(create_e2sar_process_table(e2sar_processes, process_colors),
                                       title="e2sar_perf Processes", border_style="magenta"))

    # CPU bars - simple utilization display
    layout["bars"].update(Panel(create_cpu_table(cpu_percentages),
                                title="Per-Core Usage", border_style="green"))

    return layout


def run_local_display_ssh(remote_host):
    """Run local display mode reading from SSH"""
    import_rich()
    console = Console(width=36)

    try:
        console.print(f"\n[green]Connecting to {remote_host}...[/green]")

        # Create ~/.cpu_monitor/ directory on remote if it doesn't exist
        mkdir_cmd = ['ssh', remote_host, 'mkdir -p ~/.cpu_monitor']
        subprocess.run(mkdir_cmd, capture_output=True)

        # Check if script exists in ~/.cpu_monitor/ on remote
        check_cmd = ['ssh', remote_host, 'test -f ~/.cpu_monitor/cpu_monitor_remote.py']
        result = subprocess.run(check_cmd, capture_output=True)

        if result.returncode != 0:
            console.print("[yellow]Uploading script to remote ~/.cpu_monitor/...[/yellow]")
            # Get the path to this script
            script_path = __file__
            # Upload to remote ~/.cpu_monitor/
            scp_cmd = ['scp', script_path, f'{remote_host}:~/.cpu_monitor/cpu_monitor_remote.py']
            upload_result = subprocess.run(scp_cmd, capture_output=True, text=True)
            if upload_result.returncode != 0:
                console.print(f"[red]Failed to upload script: {upload_result.stderr}[/red]")
                return
            console.print("[green]Script uploaded successfully[/green]")

        console.print("[dim]Press Ctrl+C to exit[/dim]\n")

        # Start SSH process running the remote script
        # Redirect stderr to /dev/null to avoid blocking on bash warnings
        ssh_process = subprocess.Popen(
            ['ssh', remote_host, 'bash', '-i', '-c',
             '"conda activate e2sar && python3 ~/.cpu_monitor/cpu_monitor_remote.py --remote 2>/dev/null"'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=1,
            universal_newlines=True
        )

        # Initial display
        initial_data = {
            'hostname': remote_host,
            'cpu_percentages': [],
            'e2sar_processes': [],
            'net_rates': {}
        }

        # Track time for heartbeat
        last_heartbeat_time = time.time()
        heartbeat_interval = 5  # Send heartbeat every 5 seconds

        with Live(generate_display(initial_data), refresh_per_second=0.5, console=console) as live:
            import select

            while True:
                # Send heartbeat if needed
                if time.time() - last_heartbeat_time > heartbeat_interval:
                    try:
                        ssh_process.stdin.write('HEARTBEAT\n')
                        ssh_process.stdin.flush()
                        last_heartbeat_time = time.time()
                    except:
                        break

                # Check if data is available to read (non-blocking with timeout)
                if select.select([ssh_process.stdout], [], [], 0.1)[0]:
                    line = ssh_process.stdout.readline()
                    if not line:
                        break

                    try:
                        data = json.loads(line.strip())
                        live.update(generate_display(data))
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        console.print(f"[red]Error: {e}[/red]")

                # Check if process has terminated
                if ssh_process.poll() is not None:
                    break

    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped.[/yellow]")
    finally:
        if 'ssh_process' in locals():
            try:
                ssh_process.stdin.close()
            except:
                pass
            ssh_process.terminate()
            ssh_process.wait(timeout=5)


def run_local_display():
    """Run local display mode (for local data)"""
    import_rich()
    console = Console(width=36)

    try:
        console.print("\n[green]Starting local monitor...[/green]")
        console.print("[dim]Press Ctrl+C to exit[/dim]\n")

        data = collect_cpu_data()

        with Live(generate_display(data), refresh_per_second=0.5, console=console) as live:
            while True:
                data = collect_cpu_data()
                live.update(generate_display(data))

    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped.[/yellow]")


# ============================================================================
# MAIN
# ============================================================================

def run_local_display_ssh_multi(remote_hosts):
    """Run local display mode for multiple hosts"""
    import_rich()
    console = Console()

    try:
        console.print(f"\n[green]Connecting to {len(remote_hosts)} hosts...[/green]")

        # Setup SSH processes for all hosts
        ssh_processes = {}
        for host in remote_hosts:
            # Create ~/.cpu_monitor/ directory on remote if it doesn't exist
            mkdir_cmd = ['ssh', host, 'mkdir -p ~/.cpu_monitor']
            subprocess.run(mkdir_cmd, capture_output=True)

            # Check if script exists
            check_cmd = ['ssh', host, 'test -f ~/.cpu_monitor/cpu_monitor_remote.py']
            result = subprocess.run(check_cmd, capture_output=True)

            if result.returncode != 0:
                console.print(f"[yellow]Uploading script to {host}...[/yellow]")
                script_path = __file__
                scp_cmd = ['scp', script_path, f'{host}:~/.cpu_monitor/cpu_monitor_remote.py']
                upload_result = subprocess.run(scp_cmd, capture_output=True, text=True)
                if upload_result.returncode != 0:
                    console.print(f"[red]Failed to upload script to {host}: {upload_result.stderr}[/red]")
                    continue

            # Start SSH process
            # Redirect stderr to /dev/null to avoid blocking on bash warnings
            ssh_process = subprocess.Popen(
                ['ssh', host, 'bash', '-i', '-c',
                 '"conda activate e2sar && python3 ~/.cpu_monitor/cpu_monitor_remote.py --remote 2>/dev/null"'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=1,
                universal_newlines=True
            )
            ssh_processes[host] = {
                'process': ssh_process,
                'last_heartbeat': time.time(),
                'data': {
                    'hostname': host,
                    'cpu_percentages': [],
                    'e2sar_processes': [],
                    'net_rates': {}
                }
            }

        console.print("[dim]Press Ctrl+C to exit[/dim]\n")

        heartbeat_interval = 5

        # Create initial layout with all hosts
        def create_multi_display():
            main_layout = Layout()

            # Create horizontal tiles
            host_layouts = []
            for host in remote_hosts:
                if host in ssh_processes:
                    host_layouts.append(Layout(generate_display(ssh_processes[host]['data'])))

            if len(host_layouts) == 1:
                main_layout = host_layouts[0]
            elif len(host_layouts) > 1:
                main_layout.split_row(*host_layouts)

            return main_layout

        with Live(create_multi_display(), refresh_per_second=0.5, console=console) as live:
            import select

            while ssh_processes:
                # Check for dead processes first
                for host, proc_data in list(ssh_processes.items()):
                    if proc_data['process'].poll() is not None:
                        ssh_processes.pop(host, None)

                if not ssh_processes:
                    break

                # Send heartbeats
                current_time = time.time()
                for host, proc_data in list(ssh_processes.items()):
                    # Skip if process is dead
                    if proc_data['process'].poll() is not None:
                        ssh_processes.pop(host, None)
                        continue

                    if current_time - proc_data['last_heartbeat'] > heartbeat_interval:
                        try:
                            if proc_data['process'].stdin and not proc_data['process'].stdin.closed:
                                proc_data['process'].stdin.write('HEARTBEAT\n')
                                proc_data['process'].stdin.flush()
                                proc_data['last_heartbeat'] = current_time
                        except (BrokenPipeError, OSError, ValueError):
                            # Process died, remove it
                            ssh_processes.pop(host, None)
                            continue
                        except Exception:
                            # Other errors, also remove
                            ssh_processes.pop(host, None)
                            continue

                # Check for data from any process
                ready_procs = []
                for host, proc_data in ssh_processes.items():
                    if select.select([proc_data['process'].stdout], [], [], 0)[0]:
                        ready_procs.append(host)

                for host in ready_procs:
                    proc_data = ssh_processes.get(host)
                    if not proc_data:
                        continue

                    line = proc_data['process'].stdout.readline()
                    if not line:
                        # Process ended
                        ssh_processes.pop(host, None)
                        continue

                    try:
                        data = json.loads(line.strip())
                        proc_data['data'] = data
                    except json.JSONDecodeError:
                        continue

                # Update display if we still have processes
                if ssh_processes:
                    live.update(create_multi_display())

                # Small sleep to prevent tight loop
                time.sleep(0.1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped.[/yellow]")
    finally:
        # Cleanup all SSH processes
        for host, proc_data in list(ssh_processes.items()):
            try:
                proc_data['process'].stdin.close()
            except (BrokenPipeError, OSError, ValueError):
                pass
            except Exception:
                pass
            try:
                proc_data['process'].terminate()
            except Exception:
                pass
            try:
                proc_data['process'].wait(timeout=2)
            except Exception:
                try:
                    proc_data['process'].kill()
                except Exception:
                    pass


def main():
    parser = argparse.ArgumentParser(description='CPU Monitor - Local or Remote')
    parser.add_argument('--remote', action='store_true',
                        help='Run in remote collector mode (outputs JSON)')
    parser.add_argument('--host', type=str, nargs='+',
                        help='Remote host(s) to monitor (SSH) - space separated')

    args = parser.parse_args()

    if args.remote:
        # Remote collector mode
        run_remote_collector()
    elif args.host:
        # Local display with remote data
        if len(args.host) == 1:
            run_local_display_ssh(args.host[0])
        else:
            run_local_display_ssh_multi(args.host)
    else:
        # Local mode
        run_local_display()


if __name__ == "__main__":
    main()
