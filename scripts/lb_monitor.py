#!/usr/bin/env python3
"""
lb_monitor.py - Monitor EJFAT Load Balancer Overview

Runs 'make overview' every second and displays statistics.
Tracks state transitions and alerts when senders complete.

Usage:
  cd ESnetDTN/runs/test2
  python3 ~/ejfat_demos/scripts/lb_monitor.py
"""

import subprocess
import time
import re
import sys
import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich import box

class LBMonitor:
    def __init__(self):
        self.console = Console()
        self.receivers_seen = False
        self.senders_seen = False
        self.last_sender_count = 0
        self.start_time = None
        self.iteration = 0

    def run_make_overview(self):
        """Run 'make overview' command locally (non-interactive)"""
        try:
            # We need to run the lbadm command directly since make overview uses watch
            # First, get EJFAT_URI_BETA from environment or INSTANCE_URI file
            ejfat_uri = os.environ.get('EJFAT_URI_BETA')

            if not ejfat_uri and os.path.exists('INSTANCE_URI'):
                with open('INSTANCE_URI', 'r') as f:
                    for line in f:
                        if 'EJFAT_URI' in line:
                            match = re.search(r'export EJFAT_URI="?([^"\s]+)"?', line)
                            if match:
                                ejfat_uri = match.group(1)
                                break

            if not ejfat_uri:
                return None, "EJFAT_URI not found. Set EJFAT_URI_BETA or ensure INSTANCE_URI exists."

            # Run lbadm --overview directly
            result = subprocess.run(
                ['lbadm', '-u', ejfat_uri, '-6', '--overview'],
                capture_output=True,
                text=True,
                timeout=3
            )

            if result.returncode != 0:
                return None, f"lbadm error: {result.stderr.strip()}"

            return result.stdout, None

        except FileNotFoundError as e:
            return None, f"Command not found: {e.filename}. Ensure lbadm is in PATH."
        except subprocess.TimeoutExpired:
            return None, "Command timeout"
        except Exception as e:
            return None, f"Error: {str(e)}"

    def parse_overview(self, output):
        """Parse lbadm --overview output"""
        if not output:
            return None

        data = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'session_id': '',
            'name': '',
            'status': '',
            'duration': '',
            'worker_count': 0,
            'sender_count': 0,
            'workers': [],
            'senders': [],
            'sync_count': 0,
            'state_epoch': 0,
            'send_state_epoch': 0,
        }

        lines = output.split('\n')
        in_workers_section = False
        in_senders_section = False

        for line in lines:
            stripped = line.strip()

            # Parse session info
            if 'session' in line.lower() and ':' in line:
                match = re.search(r':\s*(\S+)', line)
                if match:
                    data['session_id'] = match.group(1)

            elif re.search(r'\bname\b.*:', line, re.IGNORECASE):
                match = re.search(r':\s*(.+)', line)
                if match:
                    data['name'] = match.group(1).strip()

            elif re.search(r'\bstatus\b.*:', line, re.IGNORECASE):
                match = re.search(r':\s*(\w+)', line)
                if match:
                    data['status'] = match.group(1)

            elif re.search(r'\bduration\b.*:', line, re.IGNORECASE):
                match = re.search(r':\s*(.+)', line)
                if match:
                    data['duration'] = match.group(1).strip()

            elif re.search(r'\b(workers|receivers)\b.*:', line, re.IGNORECASE):
                match = re.search(r':\s*(\d+)', line)
                if match:
                    data['worker_count'] = int(match.group(1))
                in_workers_section = True
                in_senders_section = False

            elif re.search(r'\bsenders\b.*:', line, re.IGNORECASE):
                match = re.search(r':\s*(\d+)', line)
                if match:
                    data['sender_count'] = int(match.group(1))
                in_workers_section = False
                in_senders_section = True

            elif 'syncCount' in line or 'sync_count' in line.lower():
                match = re.search(r':\s*(\d+)', line)
                if match:
                    data['sync_count'] = int(match.group(1))

            elif 'stateEpoch' in line or 'state_epoch' in line.lower():
                match = re.search(r':\s*(\d+)', line)
                if match:
                    data['state_epoch'] = int(match.group(1))

            elif 'sendStateEpoch' in line or 'send_state_epoch' in line.lower():
                match = re.search(r':\s*(\d+)', line)
                if match:
                    data['send_state_epoch'] = int(match.group(1))

            # Parse IP addresses
            elif re.search(r'^\s*\d+\.\d+\.\d+\.\d+', stripped) or \
                 re.search(r'^\s*[0-9a-f:]+:[0-9a-f:]+', stripped, re.IGNORECASE):
                ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+|[0-9a-f:]+:[0-9a-f:]+)', stripped, re.IGNORECASE)
                if ip_match:
                    ip = ip_match.group(1)
                    if in_workers_section:
                        data['workers'].append(ip)
                    elif in_senders_section:
                        data['senders'].append(ip)

        return data

    def check_state_transitions(self, data):
        """Check for state transitions and return alert message"""
        if not data:
            return None

        worker_count = data.get('worker_count', 0)
        sender_count = data.get('sender_count', 0)

        alert = None

        # Check if receivers appeared
        if not self.receivers_seen and worker_count > 0:
            self.receivers_seen = True
            alert = f"🔵 RECEIVERS ACTIVE: {worker_count} receiver(s) registered"

        # Check if senders appeared (after receivers)
        if self.receivers_seen and not self.senders_seen and sender_count > 0:
            self.senders_seen = True
            self.start_time = datetime.now()
            alert = f"🟢 SENDERS ACTIVE: {sender_count} sender(s) started"

        # Check if receivers dropped to zero while senders still active
        if self.senders_seen and sender_count > 0 and worker_count == 0:
            alert = f"💀 OH OH.. BAD NEWS BEARS - Receivers dropped to 0 while {sender_count} sender(s) still active!"

        # Check if senders dropped to zero (after being active)
        if self.senders_seen and self.last_sender_count > 0 and sender_count == 0:
            elapsed = ""
            if self.start_time:
                duration = datetime.now() - self.start_time
                hours = int(duration.total_seconds() // 3600)
                minutes = int((duration.total_seconds() % 3600) // 60)
                seconds = int(duration.total_seconds() % 60)
                if hours > 0:
                    elapsed = f" (Duration: {hours}h {minutes}m {seconds}s)"
                elif minutes > 0:
                    elapsed = f" (Duration: {minutes}m {seconds}s)"
                else:
                    elapsed = f" (Duration: {seconds}s)"
            alert = f"🔴 TIME TO KILL{elapsed}"

        self.last_sender_count = sender_count

        return alert

    def create_display(self, data, error=None, alert=None):
        """Create rich display"""

        # Main stats table
        table = Table(title="EJFAT Load Balancer Overview", box=box.ROUNDED, show_header=True)
        table.add_column("Metric", style="cyan", no_wrap=True, width=20)
        table.add_column("Value", style="yellow")

        if error:
            table.add_row("Status", f"[red]{error}[/red]")
        elif data:
            table.add_row("Timestamp", data['timestamp'])
            table.add_row("Iteration", str(self.iteration))
            if data.get('session_id'):
                table.add_row("Session ID", data['session_id'])
            if data.get('name'):
                table.add_row("Name", data['name'])
            if data.get('status'):
                table.add_row("Status", data['status'])
            if data.get('duration'):
                table.add_row("Duration", data['duration'])
            table.add_row("", "")

            # Color code the counts based on state
            worker_style = "green" if data['worker_count'] > 0 else "dim"
            sender_style = "green" if data['sender_count'] > 0 else "dim"

            table.add_row("Workers/Receivers", f"[{worker_style}]{data['worker_count']}[/{worker_style}]")
            table.add_row("Senders", f"[{sender_style}]{data['sender_count']}[/{sender_style}]")

            if data.get('sync_count') or data.get('state_epoch') or data.get('send_state_epoch'):
                table.add_row("", "")
                if data.get('sync_count'):
                    table.add_row("Sync Count", str(data['sync_count']))
                if data.get('state_epoch'):
                    table.add_row("State Epoch", str(data['state_epoch']))
                if data.get('send_state_epoch'):
                    table.add_row("SendState Epoch", str(data['send_state_epoch']))
        else:
            table.add_row("Status", "[yellow]Waiting for data...[/yellow]")

        # IP address tables
        ip_tables = Table.grid(padding=(0, 2))

        # Receivers table
        receivers_table = Table(title="Receivers", box=box.ROUNDED, show_header=True, width=40)
        receivers_table.add_column("#", style="dim", width=3)
        receivers_table.add_column("IP Address", style="green")

        if data and data.get('workers'):
            for i, ip in enumerate(data['workers'], 1):
                receivers_table.add_row(str(i), ip)
        elif data and data['worker_count'] == 0:
            receivers_table.add_row("", "[dim]No receivers[/dim]")
        else:
            receivers_table.add_row("", "[dim]Waiting...[/dim]")

        # Senders table
        senders_table = Table(title="Senders", box=box.ROUNDED, show_header=True, width=40)
        senders_table.add_column("#", style="dim", width=3)
        senders_table.add_column("IP Address", style="yellow")

        if data and data.get('senders'):
            for i, ip in enumerate(data['senders'], 1):
                senders_table.add_row(str(i), ip)
        elif data and data['sender_count'] == 0:
            senders_table.add_row("", "[dim]No senders[/dim]")
        else:
            senders_table.add_row("", "[dim]Waiting...[/dim]")

        ip_tables.add_row(receivers_table, senders_table)

        # State indicators
        state_text = Text()
        if self.receivers_seen:
            state_text.append("✓ Receivers Seen  ", style="green")
        else:
            state_text.append("⏳ Waiting for Receivers  ", style="yellow")

        if self.senders_seen:
            state_text.append("✓ Senders Seen", style="green")
        else:
            state_text.append("⏳ Waiting for Senders", style="yellow")

        # Combine everything
        display = Table.grid()
        display.add_row(table)
        display.add_row("")
        display.add_row(ip_tables)
        display.add_row("")
        display.add_row(Panel(state_text, title="State Tracking", border_style="blue"))

        if alert:
            display.add_row("")
            if "BAD NEWS BEARS" in alert:
                display.add_row(Panel(
                    Text(alert, style="bold white on red", justify="center"),
                    border_style="red",
                    box=box.DOUBLE,
                    title="[bold red]💀  ERROR  💀[/bold red]"
                ))
            elif "TIME TO KILL" in alert:
                display.add_row(Panel(
                    Text(alert, style="bold white on red", justify="center"),
                    border_style="red",
                    box=box.DOUBLE,
                    title="[bold red]⚠️  ALERT  ⚠️[/bold red]"
                ))
            else:
                display.add_row(Panel(
                    Text(alert, justify="center"),
                    border_style="green"
                ))

        return display

    def run(self):
        """Main monitoring loop"""
        self.console.print("[bold cyan]EJFAT Load Balancer Monitor[/bold cyan]")
        self.console.print("Monitoring load balancer state every second...")
        self.console.print("Press Ctrl-C to stop\n")

        try:
            with Live(self.create_display(None), refresh_per_second=2, console=self.console) as live:
                while True:
                    self.iteration += 1

                    # Get overview data
                    output, error = self.run_make_overview()

                    if error:
                        data = None
                    else:
                        data = self.parse_overview(output)

                    # Check for state transitions
                    alert = self.check_state_transitions(data)

                    # Update display
                    live.update(self.create_display(data, error, alert))

                    # If TIME TO KILL, beep
                    if alert and "TIME TO KILL" in alert:
                        self.console.bell()

                    # Wait before next update
                    time.sleep(1)

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Monitoring stopped[/yellow]")
        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/red]")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    monitor = LBMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
