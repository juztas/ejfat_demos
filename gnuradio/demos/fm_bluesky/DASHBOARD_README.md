# FM Radio E2SAR Demo Dashboard

A Streamlit-based interactive dashboard for orchestrating the FM Radio E2SAR demo. This dashboard provides a guided, step-by-step interface for demonstrating EJFAT load balancer integration with GNU Radio flowgraphs.

## Overview

This dashboard allows you to:
- Reserve and manage EJFAT load balancer instances
- Start and stop GNU Radio transmitter and receiver flowgraphs
- Monitor system status in real-time
- Follow along with an integrated slide presentation that guides you through each step

## Architecture

```
Dashboard (Streamlit) → GNU Radio Flowgraphs → E2SAR → EJFAT LB
```

**Components:**
- **Dashboard**: Streamlit web interface for control and monitoring
- **Transmitter**: `fm_transmitter_e2sar.py` - Captures FM signals and sends via E2SAR
- **Receiver**: `fm_receiver_e2sar.py` - Receives E2SAR data and plays audio
- **Load Balancer**: EJFAT load balancer for routing packets

## Prerequisites

1. **Conda Environment**: Activate the GNU Radio environment
   ```bash
   conda activate gnuradio
   ```

2. **Python Packages**: Install required packages
   ```bash
   pip install streamlit pyyaml
   ```

3. **Marp CLI** (optional, for regenerating slides):
   ```bash
   npm install -g @marp-team/marp-cli
   ```

4. **E2SAR Setup**: Ensure E2SAR is installed and configured
   - See main repository CLAUDE.md for E2SAR setup instructions

5. **EJFAT Load Balancer**: Have access to an EJFAT admin server
   - Default: `ejfat://admin@192.168.100.1:9876/lb/1?sync=192.168.0.1:12345`
   - Configure in `dashboard_config.yaml` if different

6. **SSH Access** (for real load balancer management):
   - SSH access to a node with `lbadm` installed (default: `wash-dtn1-mgt.es.net`)
   - Valid SSH credentials (key-based authentication recommended)
   - Network connectivity to the remote node
   - Alternatively, set `ssh.enabled: false` in config to use simulated mode

## Quick Start

1. **Navigate to the dashboard directory**:
   ```bash
   cd demos/fm_bluesky
   ```

2. **Launch the dashboard**:
   ```bash
   streamlit run dashboard.py
   ```

3. **Open your browser**:
   - Dashboard will automatically open at `http://localhost:8501`
   - If not, manually navigate to the URL shown in the terminal

4. **Follow the demo steps**:
   - The left sidebar shows the current step and instructions
   - Use the control panel on the right to interact with the demo
   - Navigate through steps using Previous/Next buttons

## Demo Workflow

### Step 1: Reserve Load Balancer
1. Review the Admin URI in the Load Balancer Configuration panel
2. Click **"Reserve LB"** button
3. Wait for Instance URI to populate

### Step 2: Start Transmitter
1. Click **"Start TX"** in the Transmitter panel
2. Wait for status to show "Running"
3. The transmitter begins capturing and transmitting FM signals via E2SAR

### Step 3: Start Receiver
1. Click **"Start RX"** in the Receiver panel
2. Wait for status to show "Running"
3. You should hear audio output from the FM station

### Step 4-5: Monitor and Observe
- Check the System Status panel for real-time information
- Expand System Logs to see detailed activity
- Experiment with the running demo

### Step 6: Cleanup
1. Click **"Stop RX"** to stop the receiver
2. Click **"Stop TX"** to stop the transmitter
3. Click **"Free LB"** to release the load balancer

## Configuration

Edit `dashboard_config.yaml` to customize:

```yaml
# Default URIs
default_admin_uri: "ejfat://admin@192.168.100.1:9876/lb/1?sync=192.168.0.1:12345"
default_instance_uri: ""

# SSH settings for remote lbadm execution
ssh:
  enabled: true                      # Set to false to use simulated LB
  hostname: "wash-dtn1-mgt.es.net"   # Remote node running lbadm
  username: ""                        # SSH username (empty = use current user)
  key_file: ""                        # SSH key file (empty = use default)
  port: 22                            # SSH port
  timeout: 10                         # SSH connection timeout (seconds)
  lbadm_path: "lbadm"                 # Path to lbadm command on remote host

# Load balancer settings
load_balancer:
  name: "fm_demo_lb"                  # Load balancer name for reserve
  duration: "02:00:00"                # Reservation duration [hh:mm:ss]
  worker_address: ""                  # Worker IP (empty = auto-detect)
  use_export_format: true             # Use -e flag to get clean URI output

# Flowgraph paths (relative to fm_bluesky directory)
transmitter_script: "../fm/fm_transmitter_e2sar.py"
receiver_script: "../fm/fm_receiver_e2sar.py"

# Startup delays (seconds)
transmitter_startup_delay: 5
receiver_startup_delay: 3

# Styling
primary_color: "#6B7D4F"
```

### SSH Configuration Options

**`ssh.enabled`**: Enable/disable real SSH-based load balancer management
- `true`: Use SSH to run `lbadm` on remote node (requires SSH access)
- `false`: Use simulated mode (for testing without SSH access)

**`ssh.hostname`**: Remote node running the `lbadm` command
- Default: `wash-dtn1-mgt.es.net`
- Change to your EJFAT control node

**`ssh.username`**: SSH username for authentication
- Empty string (`""`) uses current user
- Specify username if different from local user

**`ssh.key_file`**: Path to SSH private key file
- Empty string (`""`) uses default SSH keys (`~/.ssh/id_rsa`, etc.)
- Specify path for custom key: `/path/to/private_key`

**`ssh.lbadm_path`**: Path to lbadm on remote host
- Default: `lbadm` (searches PATH)
- Specify full path if needed: `/usr/local/bin/lbadm`

**`load_balancer.name`**: Load balancer instance name
- Used when reserving LB with `lbadm --reserve -l <name>`
- Choose a descriptive name for your demo

**`load_balancer.duration`**: Reservation time duration
- Format: `[hh:mm:ss]` (e.g., `02:00:00` = 2 hours)
- Duration the LB remains reserved after allocation

**`load_balancer.worker_address`**: Worker IP address
- Empty string (`""`) lets lbadm auto-detect
- Specify IP if auto-detection fails: `192.168.1.100`

## File Structure

```
fm_bluesky/
├── dashboard.py              # Main Streamlit app
├── dashboard_config.yaml     # Configuration file
├── lbadm_manager.py          # SSH and lbadm command manager
├── slides/
│   ├── demo_slides.md        # Marp markdown source
│   └── demo_slides.html      # Generated HTML slides
├── DASHBOARD_README.md       # This file
└── DASHBOARD_PLAN.md         # Implementation plan
```

## Troubleshooting

### Dashboard won't start
```bash
# Check if streamlit and pyyaml are installed
python -c "import streamlit; import yaml"

# If not installed:
pip install streamlit pyyaml
```

### Transmitter/Receiver won't start
- Verify the flowgraph scripts exist:
  ```bash
  ls -l ../fm/fm_transmitter_e2sar.py
  ls -l ../fm/fm_receiver_e2sar.py
  ```
- Check that the gnuradio conda environment is activated
- Review System Logs in the dashboard for error messages

### SSH Connection Failed

If the dashboard shows "SSH connection failed":

1. **Test SSH manually**:
   ```bash
   ssh wash-dtn1-mgt.es.net echo "SSH test successful"
   ```

2. **Check SSH configuration**:
   - Verify hostname in `dashboard_config.yaml`
   - Ensure SSH keys are set up: `ls ~/.ssh/id_rsa*`
   - Test with specific key: `ssh -i /path/to/key user@hostname`

3. **Check network connectivity**:
   ```bash
   ping wash-dtn1-mgt.es.net
   ```

4. **Use simulated mode** (no SSH required):
   ```yaml
   # In dashboard_config.yaml
   ssh:
     enabled: false
   ```

### Load Balancer Reservation Failed

If `lbadm --reserve` fails:

1. **Check lbadm is installed on remote host**:
   ```bash
   ssh wash-dtn1-mgt.es.net which lbadm
   ```

2. **Verify admin URI format**:
   - Must start with `ejfat://admin@`
   - Example: `ejfat://admin@192.168.100.1:9876/lb/1?sync=192.168.0.1:12345`

3. **Check lbadm output manually**:
   ```bash
   ssh wash-dtn1-mgt.es.net 'lbadm -u "YOUR_ADMIN_URI" --reserve -l test_lb -d 00:10:00 -e'
   ```

4. **Review dashboard logs**:
   - Expand "System Logs" in the dashboard
   - Look for error messages from lbadm

### Load balancer connection fails
- Verify the admin URI is correct in `dashboard_config.yaml`
- Check network connectivity to the EJFAT server
- Ensure E2SAR is properly configured
- Test SSH connection using the "Test SSH Connection" button

### Processes won't stop
- Use the dashboard's Stop buttons first
- If that fails, manually kill processes:
  ```bash
  ps aux | grep "fm_transmitter\|fm_receiver"
  kill <PID>
  ```

## Customization

### Regenerate Slides
If you modify `slides/demo_slides.md`:
```bash
marp slides/demo_slides.md -o slides/demo_slides.html --html
```

### Change Color Scheme
Edit `dashboard_config.yaml`:
```yaml
primary_color: "#YOUR_COLOR"
background_color: "#YOUR_COLOR"
```

### Add Custom Steps
1. Add new entries to the `SLIDES` dictionary in `dashboard.py`
2. Update navigation logic if needed
3. Modify `dashboard_config.yaml` steps section

## Development

### Running in Development Mode
```bash
streamlit run dashboard.py --server.runOnSave true
```
This enables hot-reloading when you edit the code.

### Testing Configuration
```bash
python -c "import yaml; print(yaml.safe_load(open('dashboard_config.yaml')))"
```

### Testing SSH and lbadm

Before running the dashboard, test your SSH and lbadm setup:

```bash
# Test SSH connection
ssh wash-dtn1-mgt.es.net echo "✅ SSH connection successful"

# Check if lbadm is available
ssh wash-dtn1-mgt.es.net which lbadm

# Test lbadm version
ssh wash-dtn1-mgt.es.net lbadm --help

# Test lbadm_manager module
python << 'EOF'
from lbadm_manager import LBAdminManager
import yaml

with open('dashboard_config.yaml') as f:
    config = yaml.safe_load(f)

manager = LBAdminManager(config)
print("Testing SSH connection...")
success, message = manager.test_connection()
print(f"Result: {message}")
EOF
```

## Resources

- **Streamlit Documentation**: https://docs.streamlit.io/
- **Marp Documentation**: https://marp.app/
- **E2SAR GitHub**: https://github.com/JeffersonLab/E2SAR
- **GNU Radio Wiki**: https://wiki.gnuradio.org/

## Support

For issues or questions:
1. Check the System Logs in the dashboard
2. Review the troubleshooting section above
3. Consult the main repository documentation (CLAUDE.md)
4. Check E2SAR and GNU Radio documentation

## License

Part of the EJFAT demos repository. See main repository for license information.
