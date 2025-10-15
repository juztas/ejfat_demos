#!/usr/bin/env python3
"""
Load Balancer Admin Manager
Handles SSH connections and lbadm command execution for EJFAT load balancer management.
"""

import subprocess
import re
from typing import Optional, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class LBAdminManager:
    """Manages EJFAT load balancer operations via SSH and lbadm command."""
    
    def __init__(self, config: Dict):
        """
        Initialize LBAdminManager with configuration.
        
        Args:
            config: Configuration dictionary with ssh and load_balancer settings
        """
        self.config = config
        self.ssh_config = config.get('ssh', {})
        self.lb_config = config.get('load_balancer', {})
        self.enabled = self.ssh_config.get('enabled', True)
        
    def _build_ssh_command(self, remote_command: str) -> list:
        """
        Build SSH command with proper options.

        Args:
            remote_command: Command to execute on remote host

        Returns:
            List of command arguments for subprocess
        """
        hostname = self.ssh_config.get('hostname', 'wash-dtn1-mgt.es.net')
        username = self.ssh_config.get('username', '')
        key_file = self.ssh_config.get('key_file', '')
        port = self.ssh_config.get('port', 22)
        timeout = self.ssh_config.get('timeout', 10)

        # Build SSH target
        ssh_target = f"{username}@{hostname}" if username else hostname

        # Build SSH command with -t option for pseudo-terminal
        ssh_cmd = ['ssh', '-t', '-p', str(port)]

        # Add timeout using ConnectTimeout
        ssh_cmd.extend(['-o', f'ConnectTimeout={timeout}'])

        # Add strict host key checking option (accept new hosts)
        ssh_cmd.extend(['-o', 'StrictHostKeyChecking=accept-new'])

        # Add key file if specified
        if key_file:
            ssh_cmd.extend(['-i', key_file])

        # Add target and command
        ssh_cmd.append(ssh_target)
        ssh_cmd.append(remote_command)

        return ssh_cmd
    
    def _execute_ssh_command(self, remote_command: str) -> Tuple[bool, str, str]:
        """
        Execute command via SSH.
        
        Args:
            remote_command: Command to execute on remote host
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            ssh_cmd = self._build_ssh_command(remote_command)
            logger.info(f"Executing SSH command: {' '.join(ssh_cmd)}")
            
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", "SSH command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def _parse_instance_uri(self, output: str, use_export: bool = True) -> Optional[str]:
        """
        Parse instance URI from lbadm output.

        Args:
            output: Command output from lbadm
            use_export: Whether -e flag was used (export format)

        Returns:
            Instance URI string or None if not found
        """
        if use_export:
            # Parse: export EJFAT_URI=ejfat://instance_xxx@host:port/...
            # Handle both quoted and unquoted URIs
            match = re.search(r'export\s+EJFAT_URI=([^\s]+)', output)
            if match:
                uri = match.group(1)
                # Strip surrounding quotes if present
                uri = uri.strip("'\"")
                return uri
        else:
            # Parse from regular output - look for ejfat:// URI
            match = re.search(r'ejfat://instance[^\s]+', output)
            if match:
                uri = match.group(0)
                # Strip surrounding quotes if present
                uri = uri.strip("'\"")
                return uri

        return None
    
    def _wrap_with_conda(self, lbadm_command: str) -> str:
        """
        Wrap lbadm command with bash -i -c and conda activate.

        Args:
            lbadm_command: The lbadm command to wrap

        Returns:
            Command wrapped with bash and conda activation
        """
        # Escape any double quotes in the lbadm command for nested quoting
        escaped_cmd = lbadm_command.replace('"', '\\"')
        # Wrap in bash -i -c with conda activation
        return f'bash -i -c "conda activate e2sar && {escaped_cmd}"'

    def _build_ssh_command_string(self, remote_command: str) -> str:
        """
        Build SSH command as a string for display purposes.

        Args:
            remote_command: Command to execute on remote host (lbadm command)

        Returns:
            Full SSH command as string
        """
        hostname = self.ssh_config.get('hostname', 'wash-dtn1-mgt.es.net')
        username = self.ssh_config.get('username', '')
        key_file = self.ssh_config.get('key_file', '')
        port = self.ssh_config.get('port', 22)

        # Build SSH target
        ssh_target = f"{username}@{hostname}" if username else hostname

        # Wrap remote command with conda activation
        wrapped_command = self._wrap_with_conda(remote_command)

        # Build SSH command string with -t option
        ssh_parts = ['ssh', '-t']

        if port != 22:
            ssh_parts.extend(['-p', str(port)])

        if key_file:
            ssh_parts.extend(['-i', key_file])

        ssh_parts.append(ssh_target)
        ssh_parts.append(f"'{wrapped_command}'")

        return ' '.join(ssh_parts)

    def test_connection(self) -> Tuple[bool, str]:
        """
        Test SSH connection to remote host.

        Returns:
            Tuple of (success, message)
        """
        if not self.enabled:
            return True, "SSH disabled (using simulated mode)"

        success, stdout, stderr = self._execute_ssh_command("echo 'SSH connection test'")

        if success:
            return True, "SSH connection successful"
        else:
            return False, f"SSH connection failed: {stderr}"

    def get_reserve_command(self, admin_uri: str, duration: Optional[str] = None) -> str:
        """
        Get the SSH command that would be executed for reserve operation.

        Args:
            admin_uri: Admin URI for the EJFAT control plane
            duration: Duration in HH:MM:SS format (optional, uses config default if not provided)

        Returns:
            Full SSH command string
        """
        if not self.enabled:
            return "SSH disabled (simulated mode)"

        # Build lbadm command
        lbadm_path = self.ssh_config.get('lbadm_path', 'lbadm')
        lb_name = self.lb_config.get('name', 'fm_demo_lb')
        duration = duration or self.lb_config.get('duration', '02:00:00')
        worker_addr = self.lb_config.get('worker_address', '')
        use_export = self.lb_config.get('use_export_format', True)

        # Build command
        cmd_parts = [lbadm_path, '-u', f'"{admin_uri}"', '--reserve', '-l', lb_name, '-d', duration]

        if worker_addr:
            cmd_parts.extend(['-a', worker_addr])

        if use_export:
            cmd_parts.append('-e')

        remote_command = ' '.join(cmd_parts)

        return self._build_ssh_command_string(remote_command)

    def get_free_command(self, instance_uri: str) -> str:
        """
        Get the SSH command that would be executed for free operation.

        Args:
            instance_uri: Instance URI for the load balancer

        Returns:
            Full SSH command string
        """
        if not self.enabled:
            return "SSH disabled (simulated mode)"

        if not instance_uri:
            return "No instance URI available"

        # Build lbadm command with export EJFAT_URI first, then run lbadm without -u
        lbadm_path = self.ssh_config.get('lbadm_path', 'lbadm')

        # Export EJFAT_URI first, then run lbadm --free without -u option
        remote_command = f'export EJFAT_URI="{instance_uri}" && {lbadm_path} --free'

        return self._build_ssh_command_string(remote_command)

    def get_overview_command(self, admin_uri: str) -> str:
        """
        Get the SSH command that would be executed for overview operation.

        Args:
            admin_uri: Admin URI for the EJFAT control plane

        Returns:
            Full SSH command string
        """
        if not self.enabled:
            return "SSH disabled (simulated mode)"

        # Build lbadm command
        lbadm_path = self.ssh_config.get('lbadm_path', 'lbadm')

        cmd_parts = [lbadm_path, '-u', f'"{admin_uri}"', '--overview']
        remote_command = ' '.join(cmd_parts)

        return self._build_ssh_command_string(remote_command)
    
    def reserve_load_balancer(self, admin_uri: str, duration: Optional[str] = None) -> Tuple[bool, Optional[str], str]:
        """
        Reserve an EJFAT load balancer.

        Args:
            admin_uri: Admin URI for the EJFAT control plane
            duration: Duration in HH:MM:SS format (optional, uses config default if not provided)

        Returns:
            Tuple of (success, instance_uri, message)
        """
        if not self.enabled:
            # Simulated mode
            import uuid
            instance_token = str(uuid.uuid4())[:8]
            instance_uri = admin_uri.replace('admin@', f'instance_{instance_token}@')
            return True, instance_uri, f"Load balancer reserved (simulated): instance_{instance_token}"

        # Build lbadm command
        lbadm_path = self.ssh_config.get('lbadm_path', 'lbadm')
        lb_name = self.lb_config.get('name', 'fm_demo_lb')
        duration = duration or self.lb_config.get('duration', '02:00:00')
        worker_addr = self.lb_config.get('worker_address', '')
        use_export = self.lb_config.get('use_export_format', True)

        # Build command
        cmd_parts = [lbadm_path, '-u', f'"{admin_uri}"', '--reserve', '-l', lb_name, '-d', duration]

        if worker_addr:
            cmd_parts.extend(['-a', worker_addr])

        if use_export:
            cmd_parts.append('-e')

        lbadm_command = ' '.join(cmd_parts)

        # Wrap with conda activation
        remote_command = self._wrap_with_conda(lbadm_command)

        # Execute command
        logger.info(f"Reserving load balancer: {lb_name} for duration: {duration}")
        success, stdout, stderr = self._execute_ssh_command(remote_command)

        if success:
            # Parse instance URI from output
            instance_uri = self._parse_instance_uri(stdout, use_export)

            if instance_uri:
                return True, instance_uri, f"Load balancer reserved: {lb_name}"
            else:
                return False, None, f"Failed to parse instance URI from output: {stdout}"
        else:
            return False, None, f"lbadm reserve failed: {stderr}"
    
    def free_load_balancer(self, instance_uri: str) -> Tuple[bool, str]:
        """
        Free an EJFAT load balancer.

        Args:
            instance_uri: Instance URI for the load balancer

        Returns:
            Tuple of (success, message)
        """
        if not self.enabled:
            # Simulated mode
            return True, "Load balancer freed (simulated)"

        # Build lbadm command with export EJFAT_URI first, then run lbadm without -u
        lbadm_path = self.ssh_config.get('lbadm_path', 'lbadm')

        # Export EJFAT_URI first, then run lbadm --free without -u option
        lbadm_command = f'export EJFAT_URI="{instance_uri}" && {lbadm_path} --free'

        # Wrap with conda activation
        remote_command = self._wrap_with_conda(lbadm_command)

        # Execute command
        logger.info("Freeing load balancer")
        success, stdout, stderr = self._execute_ssh_command(remote_command)

        if success:
            return True, "Load balancer freed successfully"
        else:
            return False, f"lbadm free failed: {stderr}"

    def force_free_by_lbid(self, admin_uri: str, lbid: str) -> Tuple[bool, str]:
        """
        Force free an EJFAT load balancer by LBID using admin privileges.

        Args:
            admin_uri: Admin URI for the EJFAT control plane
            lbid: Load balancer ID to free

        Returns:
            Tuple of (success, message)
        """
        if not self.enabled:
            # Simulated mode
            return True, f"Load balancer {lbid} force freed (simulated)"

        # Build lbadm command
        lbadm_path = self.ssh_config.get('lbadm_path', 'lbadm')

        # Use admin URI with --lbid and --free flags
        lbadm_command = f'{lbadm_path} -u "{admin_uri}" --lbid {lbid} --free'

        # Wrap with conda activation
        remote_command = self._wrap_with_conda(lbadm_command)

        # Execute command
        logger.info(f"Force freeing load balancer with LBID: {lbid}")
        success, stdout, stderr = self._execute_ssh_command(remote_command)

        if success:
            return True, f"Load balancer {lbid} freed successfully"
        else:
            return False, f"lbadm free failed: {stderr}"
    
    def get_status(self, uri: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Get load balancer status.
        
        Args:
            uri: Admin or instance URI
            
        Returns:
            Tuple of (success, status_dict, message)
        """
        if not self.enabled:
            # Simulated mode
            return True, {"status": "simulated"}, "Status (simulated mode)"
        
        # Build lbadm command
        lbadm_path = self.ssh_config.get('lbadm_path', 'lbadm')
        
        cmd_parts = [lbadm_path, '-u', f'"{uri}"', '--status']
        remote_command = ' '.join(cmd_parts)
        
        # Execute command
        logger.info("Getting load balancer status")
        success, stdout, stderr = self._execute_ssh_command(remote_command)
        
        if success:
            # Parse status output (basic version - could be enhanced)
            status_dict = {"raw_output": stdout}
            return True, status_dict, "Status retrieved successfully"
        else:
            return False, None, f"lbadm status failed: {stderr}"
    
    def get_version(self, uri: str) -> Tuple[bool, Optional[str], str]:
        """
        Get E2SAR/lbadm version.

        Args:
            uri: Admin or instance URI

        Returns:
            Tuple of (success, version_string, message)
        """
        if not self.enabled:
            return True, "simulated", "Version (simulated mode)"

        # Build lbadm command
        lbadm_path = self.ssh_config.get('lbadm_path', 'lbadm')

        cmd_parts = [lbadm_path, '-u', f'"{uri}"', '--version']
        remote_command = ' '.join(cmd_parts)

        # Execute command
        logger.info("Getting E2SAR version")
        success, stdout, stderr = self._execute_ssh_command(remote_command)

        if success:
            # Extract version from output
            version_match = re.search(r'E2SAR Version:\s*([^\s]+)', stdout)
            version = version_match.group(1) if version_match else stdout.strip()
            return True, version, "Version retrieved successfully"
        else:
            return False, None, f"lbadm version failed: {stderr}"

    def get_overview(self, admin_uri: str) -> Tuple[bool, list, str]:
        """
        Get overview of all load balancers.

        Args:
            admin_uri: Admin URI for the EJFAT control plane

        Returns:
            Tuple of (success, list of load balancer dicts, message)
            Each dict contains: name, id, senders, workers, expiry
        """
        if not self.enabled:
            # Simulated mode
            import datetime
            simulated_lb = {
                'name': 'fm_demo_lb',
                'id': '28',
                'fpga_lbid': '0',
                'senders': [],
                'workers': [],
                'expiry': (datetime.datetime.now() + datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            return True, [simulated_lb], "Overview (simulated mode)"

        # Build lbadm command
        lbadm_path = self.ssh_config.get('lbadm_path', 'lbadm')

        cmd_parts = [lbadm_path, '-u', f'"{admin_uri}"', '--overview']
        lbadm_command = ' '.join(cmd_parts)

        # Wrap with conda activation
        remote_command = self._wrap_with_conda(lbadm_command)

        # Execute command
        logger.info("Getting load balancer overview")
        success, stdout, stderr = self._execute_ssh_command(remote_command)

        if success:
            # Parse overview output
            load_balancers = self._parse_overview(stdout)
            return True, load_balancers, "Overview retrieved successfully"
        else:
            return False, [], f"lbadm overview failed: {stderr}"

    def _parse_overview(self, output: str) -> list:
        """
        Parse lbadm --overview output into structured data.

        Args:
            output: Raw output from lbadm --overview

        Returns:
            List of dicts, each containing LB information
        """
        load_balancers = []
        current_lb = None

        lines = output.split('\n')
        for line in lines:
            line = line.strip()

            # Match: LB fm_demo_lb ID: 28 FPGA LBID: 0
            lb_match = re.match(r'^LB\s+(\S+)\s+ID:\s+(\d+)\s+FPGA LBID:\s+(\d+)', line)
            if lb_match:
                # Save previous LB if exists
                if current_lb:
                    load_balancers.append(current_lb)

                # Start new LB
                current_lb = {
                    'name': lb_match.group(1),
                    'id': lb_match.group(2),
                    'fpga_lbid': lb_match.group(3),
                    'senders': [],
                    'workers': [],
                    'expiry': ''
                }
                continue

            # Match registered senders (IP addresses)
            if current_lb and 'Registered sender addresses:' in line:
                # Next non-empty lines will contain sender addresses
                # For now, check if there's anything on the same line after the colon
                parts = line.split(':', 1)
                if len(parts) > 1 and parts[1].strip():
                    current_lb['senders'] = [addr.strip() for addr in parts[1].split(',') if addr.strip()]
                continue

            # Match registered workers
            if current_lb and 'Registered workers:' in line:
                # Next non-empty lines will contain worker addresses
                parts = line.split(':', 1)
                if len(parts) > 1 and parts[1].strip():
                    current_lb['workers'] = [addr.strip() for addr in parts[1].split(',') if addr.strip()]
                continue

            # Match expiry time in LB details
            if current_lb:
                expiry_match = re.search(r'expiresat=([^,\s]+)', line)
                if expiry_match:
                    current_lb['expiry'] = expiry_match.group(1)
                    continue

        # Don't forget to add the last LB
        if current_lb:
            load_balancers.append(current_lb)

        return load_balancers


# Convenience functions for use in dashboard
def create_manager(config: Dict) -> LBAdminManager:
    """Create and return LBAdminManager instance."""
    return LBAdminManager(config)
