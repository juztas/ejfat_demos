#!/usr/bin/env python3
"""
FM Radio E2SAR Demo Dashboard
A Streamlit-based interactive dashboard for orchestrating the FM Radio E2SAR demo.
"""

import streamlit as st
import subprocess
import os
import signal
import uuid
import yaml
from pathlib import Path
from datetime import datetime
import logging
import time
import threading
import base64

# Import lbadm manager
from lbadm_manager import LBAdminManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="FM Radio E2SAR Demo",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load configuration
config_path = Path(__file__).parent / "dashboard_config.yaml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Get default admin URI from environment variables
# Priority: EJFAT_URI_BETA > EJFAT_URI > config file
default_admin_uri = os.environ.get('EJFAT_URI_BETA') or os.environ.get('EJFAT_URI') or config.get('default_admin_uri', '')

# Update config with environment variable if found
if default_admin_uri:
    config['default_admin_uri'] = default_admin_uri

# Initialize LBAdmin manager
lbadm_manager = LBAdminManager(config)

# Custom CSS styling
st.markdown(f"""
<style>
    /* Primary green theme */
    .stButton>button {{
        background-color: {config['primary_color']};
        color: white;
        border-radius: 8px;
        padding: 6px 16px;
        border: none;
        font-weight: 500;
    }}
    .stButton>button:hover {{
        background-color: #5A6D3F;
    }}
    .stButton>button:disabled {{
        background-color: #CCCCCC;
        color: #666666;
    }}
    /* Card-like containers */
    .element-container {{
        border-radius: 8px;
    }}
    /* Headers */
    h1 {{
        color: {config['primary_color']};
    }}
    h2 {{
        color: {config['text_primary']};
    }}
    /* Code block wrapping */
    .stCodeBlock {{
        overflow-x: auto;
    }}
    .stCodeBlock code {{
        white-space: pre-wrap !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        word-break: break-all !important;
    }}
    .stCodeBlock pre {{
        white-space: pre-wrap !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        word-break: break-all !important;
        max-width: 100% !important;
    }}
    /* Ensure code blocks respect container width */
    [data-testid="stCode"] {{
        max-width: 100% !important;
    }}
    [data-testid="stCode"] > div {{
        max-width: 100% !important;
    }}
    [data-testid="stCode"] pre {{
        max-width: 100% !important;
    }}
    /* Center text in duration input */
    input[aria-label="Duration"] {{
        text-align: center !important;
        font-family: monospace !important;
    }}
    /* Style duration label to match input height */
    .duration-label {{
        display: flex !important;
        align-items: center !important;
        height: 38px !important;
        padding: 6px 12px !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        color: {config['text_primary']} !important;
        margin: 0 !important;
    }}
    /* Reduce vertical spacing for more compact layout */
    .block-container {{
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
    }}
    h1 {{
        margin-top: 0 !important;
        margin-bottom: 0.25rem !important;
        font-size: 1.75rem !important;
    }}
    h2 {{
        margin-top: 0.25rem !important;
        margin-bottom: 0.25rem !important;
        font-size: 1.25rem !important;
    }}
    h3 {{
        margin-top: 0.25rem !important;
        margin-bottom: 0.25rem !important;
        font-size: 1rem !important;
    }}
    /* Reduce spacing between elements */
    .element-container {{
        margin-top: 0 !important;
        margin-bottom: 0.0625rem !important;
    }}
    /* Reduce divider spacing */
    hr {{
        margin-top: 0.25rem !important;
        margin-bottom: 0.25rem !important;
    }}
    /* Make metrics more compact */
    [data-testid="stMetricValue"] {{
        font-size: 1rem !important;
    }}
    [data-testid="stMetricLabel"] {{
        font-size: 0.875rem !important;
    }}
    [data-testid="metric-container"] {{
        padding: 0.25rem !important;
    }}
    /* Match text input and button heights and alignment */
    .stTextInput input {{
        height: 38px !important;
        padding: 6px 16px !important;
    }}
    .stButton>button {{
        height: 38px !important;
        padding: 6px 16px !important;
        margin: 0 !important;
    }}
    /* Ensure vertical alignment in columns */
    .stTextInput > div {{
        margin-bottom: 0 !important;
    }}
    .stTextInput > label {{
        margin-bottom: 0.25rem !important;
    }}
    /* Sidebar logo styling - prevent clipping and ensure proper sizing */
    [data-testid="stSidebar"] img {{
        max-width: 100% !important;
        height: auto !important;
        object-fit: contain !important;
    }}
    /* Ensure sidebar images aren't clipped */
    [data-testid="stSidebar"] [data-testid="stImage"] {{
        overflow: visible !important;
    }}
    /* Logo container alignment */
    .logo-container {{
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        width: 100% !important;
        margin-bottom: 1rem !important;
    }}
    /* Make selected tab bold */
    button[aria-selected="true"] {{
        font-weight: 700 !important;
    }}
    button[aria-selected="false"] {{
        font-weight: 400 !important;
    }}
    /* DTN endpoint row styling for proper alignment */
    .dtn-row {{
        display: flex !important;
        align-items: center !important;
        padding: 8px 12px !important;
        margin-bottom: 0 !important;
        margin-top: 0 !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 0 !important;
        background-color: #F9FAFB !important;
    }}
    .dtn-row:first-of-type {{
        border-top-left-radius: 6px !important;
        border-top-right-radius: 6px !important;
    }}
    .dtn-row:last-of-type {{
        border-bottom-left-radius: 6px !important;
        border-bottom-right-radius: 6px !important;
    }}
    .dtn-row:not(:last-of-type) {{
        border-bottom: none !important;
    }}
    .dtn-row:hover {{
        background-color: #F3F4F6 !important;
        border-color: #D1D5DB !important;
        z-index: 1 !important;
        position: relative !important;
    }}
    /* Ensure checkboxes align properly */
    .dtn-row [data-testid="stCheckbox"] {{
        display: flex !important;
        align-items: center !important;
        margin: 0 !important;
        padding: 0 !important;
    }}
    /* Align text vertically in DTN rows */
    .dtn-row .stMarkdown {{
        display: flex !important;
        align-items: center !important;
        height: 38px !important;
        margin: 0 !important;
        padding: 0 !important;
    }}
    /* Match button heights in DTN rows to global standard */
    .dtn-row .stButton>button {{
        height: 38px !important;
        padding: 6px 16px !important;
    }}
    /* Remove vertical spacing within DTN rows */
    .dtn-row .element-container {{
        margin-bottom: 0 !important;
        margin-top: 0 !important;
        padding-bottom: 0 !important;
        padding-top: 0 !important;
    }}
    .dtn-row [data-testid="column"] {{
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }}
    /* Vertical centering for Speed Test page elements */
    [data-testid="column"] {{
        display: flex !important;
        align-items: center !important;
    }}
    /* Ensure number inputs align vertically */
    .stNumberInput {{
        display: flex !important;
        align-items: center !important;
    }}
    .stNumberInput > div {{
        margin-bottom: 0 !important;
    }}
    .stNumberInput input {{
        height: 38px !important;
        padding: 6px 16px !important;
    }}
    /* Ensure checkboxes align vertically */
    [data-testid="stCheckbox"] {{
        display: flex !important;
        align-items: center !important;
        height: 38px !important;
    }}
    /* Ensure markdown text aligns vertically */
    .stMarkdown {{
        display: flex !important;
        align-items: center !important;
        height: 38px !important;
    }}
    /* Hide Streamlit menu and default UI elements */
    #MainMenu {{
        visibility: hidden;
    }}
    header {{
        visibility: hidden;
    }}
    footer {{
        visibility: hidden;
    }}
    .stDeployButton {{
        visibility: hidden;
    }}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.current_step = 1
    st.session_state.lb_reserved = False
    st.session_state.admin_uri = config['default_admin_uri']
    st.session_state.admin_uri_full = config['default_admin_uri']  # Store full URI separately
    st.session_state.instance_uri = config['default_instance_uri']
    st.session_state.instance_uri_full = config['default_instance_uri']  # Store full URI separately
    st.session_state.ssh_hostname = config.get('ssh', {}).get('hostname', 'wash-dtn1-mgt.es.net')
    st.session_state.tx_running = False
    st.session_state.rx_running = False
    st.session_state.tx_process = None
    st.session_state.rx_process = None
    st.session_state.logs = []
    st.session_state.ssh_connected = None  # None = not tested, True/False = test result
    st.session_state.lb_name = None  # Track LB name for freeing
    st.session_state.obfuscate_uri = True  # Default to obfuscated view
    st.session_state.lb_duration = "1:00:00"  # Default duration: 1 hour
    st.session_state.monitoring_active = False  # Track if monitoring is active
    st.session_state.lb_overview = []  # Store LB overview data
    st.session_state.last_monitor_update = 0  # Timestamp of last monitor update
    st.session_state.last_ui_refresh = 0  # Timestamp of last UI refresh
    st.session_state.confirm_delete_lbid = None  # Track which LB is pending deletion

def validate_duration_format(duration_str):
    """
    Validate and format duration string to HH:MM:SS format.

    Args:
        duration_str: Duration string (e.g., "1:00:00", "01:00:00", "2:30:15")

    Returns:
        Tuple of (is_valid, formatted_duration, error_message)
    """
    import re

    # Remove extra whitespace
    duration_str = duration_str.strip()

    # Match HH:MM:SS or H:MM:SS pattern
    match = re.match(r'^(\d{1,2}):(\d{2}):(\d{2})$', duration_str)

    if not match:
        return False, duration_str, "Invalid format. Use HH:MM:SS (e.g., 1:00:00)"

    hours, minutes, seconds = match.groups()
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)

    # Validate ranges
    if minutes > 59:
        return False, duration_str, "Minutes must be 0-59"
    if seconds > 59:
        return False, duration_str, "Seconds must be 0-59"
    if hours > 99:
        return False, duration_str, "Hours must be 0-99"

    # Format with leading zeros for hours
    formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return True, formatted, ""

def obfuscate_uri_token(uri):
    """
    Obfuscate the token in an EJFAT URI.
    Shows first 4 and last 4 characters of token with ------ in between.

    Args:
        uri: Full URI (e.g., ejfats://nuYrE4ME8sB1hiK1ilhDklJFfrrJlZ1@ejfat-lb.es.net:18008/lb/)

    Returns:
        Obfuscated URI (e.g., ejfats://nuYr------lZ1@ejfat-lb.es.net:18008/lb/)
    """
    if not uri:
        return uri

    import re
    # Match pattern: protocol://token@host
    match = re.match(r'(ejfats?://)(.*?)(@.*)', uri)
    if match:
        protocol = match.group(1)
        token = match.group(2)
        rest = match.group(3)

        # Obfuscate token if long enough
        if len(token) > 8:
            obfuscated_token = f"{token[:4]}------{token[-4:]}"
            return f"{protocol}{obfuscated_token}{rest}"

    return uri

def log_message(msg):
    """Add a timestamped message to the logs."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] {msg}")
    # Keep only last max_log_lines
    max_lines = config.get('max_log_lines', 100)
    st.session_state.logs = st.session_state.logs[-max_lines:]

def reserve_load_balancer():
    """Reserve EJFAT load balancer using lbadm via SSH."""
    try:
        admin_uri = st.session_state.admin_uri_full  # Use full URI for command
        duration = st.session_state.get('lb_duration', '1:00:00')

        # Validate duration format
        is_valid, formatted_duration, error_msg = validate_duration_format(duration)
        if not is_valid:
            st.error(f"Invalid duration format: {error_msg}")
            log_message(f"❌ Invalid duration format: {error_msg}")
            return

        log_message(f"🔄 Reserving load balancer for {formatted_duration}...")

        # Use lbadm_manager to reserve with duration
        success, instance_uri, message = lbadm_manager.reserve_load_balancer(admin_uri, duration=formatted_duration)

        if success and instance_uri:
            st.session_state.instance_uri = instance_uri
            st.session_state.instance_uri_full = instance_uri  # Store full instance URI
            st.session_state.lb_reserved = True
            st.session_state.lb_name = config['load_balancer']['name']
            log_message(f"✅ {message}")
            log_message(f"📝 Instance URI: {instance_uri}")

            # Auto-advance to next step
            if st.session_state.current_step == 1:
                st.session_state.current_step = 2

            st.success(message)
            st.rerun()
        else:
            st.error(f"Failed to reserve LB: {message}")
            log_message(f"❌ LB reservation failed: {message}")

    except Exception as e:
        st.error(f"Failed to reserve LB: {e}")
        log_message(f"❌ LB reservation failed: {e}")

def free_load_balancer():
    """Free EJFAT load balancer using lbadm via SSH."""
    try:
        instance_uri = st.session_state.instance_uri_full  # Use full URI for command

        if not instance_uri:
            st.warning("No instance URI to free")
            return

        log_message(f"🔄 Freeing load balancer...")

        # Use lbadm_manager to free
        success, message = lbadm_manager.free_load_balancer(instance_uri)

        if success:
            st.session_state.instance_uri = ''
            st.session_state.instance_uri_full = ''  # Clear full instance URI
            st.session_state.lb_reserved = False
            st.session_state.lb_name = None
            log_message(f"✅ {message}")
            st.success(message)
            st.rerun()
        else:
            st.error(f"Failed to free LB: {message}")
            log_message(f"❌ LB free failed: {message}")

    except Exception as e:
        st.error(f"Failed to free LB: {e}")
        log_message(f"❌ LB free failed: {e}")

def test_ssh_connection():
    """Test SSH connection to remote host."""
    try:
        log_message(f"🔄 Testing SSH connection...")
        success, message = lbadm_manager.test_connection()

        st.session_state.ssh_connected = success

        if success:
            log_message(f"✅ {message}")
            st.success(message)
        else:
            log_message(f"❌ {message}")
            st.error(message)

        st.rerun()

    except Exception as e:
        st.session_state.ssh_connected = False
        st.error(f"SSH test failed: {e}")
        log_message(f"❌ SSH test failed: {e}")

def start_transmitter():
    """Start FM transmitter subprocess."""
    fm_dir = Path(__file__).parent
    tx_script = fm_dir / config['transmitter_script']

    try:
        # Activate conda environment and start process
        cmd = f"source /opt/anaconda3/bin/activate gnuradio && python {tx_script}"

        proc = subprocess.Popen(
            cmd,
            shell=True,
            cwd=str(fm_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            executable='/bin/bash',
            preexec_fn=os.setsid
        )

        # Update session state
        st.session_state.tx_process = proc
        st.session_state.tx_running = True
        log_message(f"✅ Transmitter started (PID: {proc.pid})")

        # Auto-advance to next step
        if st.session_state.current_step == 2:
            st.session_state.current_step = 3

        st.success("Transmitter started successfully!")
        st.rerun()

    except Exception as e:
        st.error(f"Failed to start transmitter: {e}")
        log_message(f"❌ Transmitter failed: {e}")

def stop_transmitter():
    """Stop FM transmitter subprocess."""
    proc = st.session_state.get('tx_process')
    if proc:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            proc.wait(timeout=5)
            st.session_state.tx_running = False
            st.session_state.tx_process = None
            log_message("✅ Transmitter stopped")
            st.success("Transmitter stopped")
            st.rerun()
        except Exception as e:
            st.error(f"Error stopping transmitter: {e}")
            log_message(f"❌ Error stopping transmitter: {e}")

def start_receiver():
    """Start FM receiver subprocess."""
    fm_dir = Path(__file__).parent
    rx_script = fm_dir / config['receiver_script']

    try:
        # Activate conda environment and start process
        cmd = f"source /opt/anaconda3/bin/activate gnuradio && python {rx_script}"

        proc = subprocess.Popen(
            cmd,
            shell=True,
            cwd=str(fm_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            executable='/bin/bash',
            preexec_fn=os.setsid
        )

        # Update session state
        st.session_state.rx_process = proc
        st.session_state.rx_running = True
        log_message(f"✅ Receiver started (PID: {proc.pid})")

        # Auto-advance to next step
        if st.session_state.current_step == 3:
            st.session_state.current_step = 4

        st.success("Receiver started successfully!")
        st.rerun()

    except Exception as e:
        st.error(f"Failed to start receiver: {e}")
        log_message(f"❌ Receiver failed: {e}")

def stop_receiver():
    """Stop FM receiver subprocess."""
    proc = st.session_state.get('rx_process')
    if proc:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            proc.wait(timeout=5)
            st.session_state.rx_running = False
            st.session_state.rx_process = None
            log_message("✅ Receiver stopped")
            st.success("Receiver stopped")
            st.rerun()
        except Exception as e:
            st.error(f"Error stopping receiver: {e}")
            log_message(f"❌ Error stopping receiver: {e}")

def open_transmitter_flowgraph():
    """Open transmitter flowgraph in GNU Radio Companion."""
    fm_dir = Path(__file__).parent
    tx_grc = fm_dir / config.get('transmitter_grc', '../../fm/fm_transmitter_e2sar.grc')

    try:
        # Activate conda environment and launch gnuradio-companion
        cmd = f"source /opt/anaconda3/bin/activate gnuradio && gnuradio-companion {tx_grc}"

        subprocess.Popen(
            cmd,
            shell=True,
            cwd=str(fm_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            executable='/bin/bash'
        )

        log_message(f"✅ Opened transmitter flowgraph: {tx_grc.name}")
        st.success("Transmitter flowgraph opened in GNU Radio Companion!")

    except Exception as e:
        st.error(f"Failed to open flowgraph: {e}")
        log_message(f"❌ Failed to open TX flowgraph: {e}")

def open_receiver_flowgraph():
    """Open receiver flowgraph in GNU Radio Companion."""
    fm_dir = Path(__file__).parent
    rx_grc = fm_dir / config.get('receiver_grc', '../../fm/fm_receiver_e2sar.grc')

    try:
        # Activate conda environment and launch gnuradio-companion
        cmd = f"source /opt/anaconda3/bin/activate gnuradio && gnuradio-companion {rx_grc}"

        subprocess.Popen(
            cmd,
            shell=True,
            cwd=str(fm_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            executable='/bin/bash'
        )

        log_message(f"✅ Opened receiver flowgraph: {rx_grc.name}")
        st.success("Receiver flowgraph opened in GNU Radio Companion!")

    except Exception as e:
        st.error(f"Failed to open flowgraph: {e}")
        log_message(f"❌ Failed to open RX flowgraph: {e}")

def monitor_load_balancers():
    """Monitor load balancers and update overview (runs on main thread)."""
    try:
        admin_uri = st.session_state.admin_uri_full  # Use full URI for command

        # Use lbadm_manager to get overview
        success, lb_list, message = lbadm_manager.get_overview(admin_uri)

        if success:
            st.session_state.lb_overview = lb_list
            st.session_state.last_monitor_update = time.time()

            if len(lb_list) > 0:
                log_message(f"✅ {message}")
                log_message(f"📊 Found {len(lb_list)} load balancer(s)")
            else:
                log_message(f"✅ {message}")
                log_message(f"📊 No active load balancers found")
        else:
            log_message(f"❌ Overview failed: {message}")

    except Exception as e:
        log_message(f"❌ Monitor failed: {e}")

def start_monitoring():
    """Fetch load balancer overview once."""
    log_message("🔄 Fetching load balancer overview...")
    # Fetch data once
    monitor_load_balancers()
    st.session_state.monitoring_active = True

def stop_monitoring():
    """Clear monitoring data and status."""
    st.session_state.monitoring_active = False
    st.session_state.lb_overview = []
    st.session_state.last_monitor_update = 0
    log_message("⏸️ Monitoring data cleared")

def force_free_load_balancer(lbid: str, lb_name: str):
    """Force free a load balancer by LBID using admin privileges."""
    try:
        admin_uri = st.session_state.admin_uri_full  # Use full URI for command

        log_message(f"🔄 Force freeing load balancer {lb_name} (ID: {lbid})...")

        # Use lbadm_manager to force free by LBID
        success, message = lbadm_manager.force_free_by_lbid(admin_uri, lbid)

        if success:
            log_message(f"✅ {message}")
            st.success(message)

            # Refresh the overview after deletion
            monitor_load_balancers()

            # Clear confirmation state
            st.session_state.confirm_delete_lbid = None
            st.rerun()
        else:
            st.error(f"Failed to free LB: {message}")
            log_message(f"❌ LB free failed: {message}")

    except Exception as e:
        st.error(f"Failed to free LB: {e}")
        log_message(f"❌ LB free failed: {e}")

# Define slides as markdown strings
SLIDES = {
    1: """
# FM Radio E2SAR Demo
## Welcome

This demo will guide you through transmitting and receiving FM radio signals
using the E2SAR data plane and EJFAT load balancer.

**What you'll learn:**
- How to reserve an EJFAT load balancer
- How to transmit FM signals via E2SAR
- How to receive and decode the signal

---

**Click "Reserve LB" to begin!**
""",
    2: """
# Step 1: Reserve Load Balancer
## Action Required ⚡

Click the **"Reserve LB"** button in the control panel above.

**What's happening:**
- Contacts EJFAT admin server
- Allocates a load balancer instance
- Returns an instance URI for data transmission

**Next:** Once reserved, the Instance URI field will populate automatically.
""",
    3: """
# Step 2: Start Transmitter
## Action Required ⚡

Click the **"Start TX"** button in the Transmitter panel.

**What's happening:**
- Launches `fm_transmitter_e2sar.py` GNU Radio flowgraph
- Initializes signal source
- Connects to E2SAR segmenter with your Instance URI
- Begins capturing FM signals at 98.5 MHz (default)

**Next:** Wait for "Status: Running" indicator
""",
    4: """
# Step 3: Start Receiver
## Action Required ⚡

Click the **"Start RX"** button in the Receiver panel.

**What's happening:**
- Launches `fm_receiver_e2sar.py` GNU Radio flowgraph
- Initializes E2SAR reassembler to receive data
- Connects to your load balancer instance
- Begins FM demodulation and audio playback

**Next:** You should hear audio from the FM station!
""",
    5: """
# Step 4: Demo Running
## What You're Seeing 🎉

**Signal Flow:**
```
Signal Source → GNU Radio TX → E2SAR Segmenter →
EJFAT Load Balancer → E2SAR Reassembler →
GNU Radio RX → Audio Output
```

**Key Concepts:**
- **E2SAR Segmenter:** Breaks GNU Radio data into EJFAT packets
- **Load Balancer:** Routes packets to receiver(s)
- **E2SAR Reassembler:** Reconstructs original signal

**Enjoy the audio!**
""",
    6: """
# Step 5: Monitor Status
## Observing the System 📊

**Check the Status Panel:**
- LB Status: Should show "Reserved"
- TX Process: Should show "Running"
- RX Process: Should show "Running"
- Demo Step: 5/7

**System Logs:**
Expand the logs panel to see:
- Process startup messages
- E2SAR connection status

**Next:** When ready, proceed to cleanup
""",
    7: """
# Step 6: Cleanup
## Action Required ⚡

**What to do:**
1. Click **"Stop RX"** to stop the receiver
2. Click **"Stop TX"** to stop the transmitter
3. Click **"Free LB"** to release the load balancer

**What's happening:**
- Gracefully shuts down GNU Radio flowgraphs
- Stops E2SAR segmenter/reassembler
- Releases load balancer resources
""",
}

# Header Component Function
def render_header():
    """Render the System Status header at the top of the page."""
    st.title("🎙️ FM Radio EJFAT / E2SAR Demo Dashboard")

    # System Status Panel (at top for horizontal space)
    st.header("📊 System Status")

    col_stat1, col_stat2, col_stat3, col_stat4, col_stat5 = st.columns(5)

    with col_stat1:
        st.metric("LB Status", "Reserved ✅" if st.session_state.get('lb_reserved') else "Free ⚪")

    with col_stat2:
        st.metric("TX Process", "Running" if st.session_state.get('tx_running') else "Stopped")

    with col_stat3:
        st.metric("RX Process", "Running" if st.session_state.get('rx_running') else "Stopped")

    with col_stat4:
        total_steps = len(SLIDES)
        st.metric("Demo Step", f"{st.session_state.get('current_step', 1)}/{total_steps}")

    with col_stat5:
        # Log viewer
        with st.expander("📜 Logs", expanded=False):
            logs = st.session_state.get('logs', [])
            if logs:
                st.text_area("System Logs", value="\n".join(logs[-20:]), height=200, disabled=True, label_visibility="collapsed")
            else:
                st.info("No logs yet")

    st.divider()

# Main App Layout
render_header()

# Sidebar with slide navigation
with st.sidebar:
    st.header("📖 Demo Guide")

    current_step = st.session_state.get('current_step', 1)
    total_steps = len(SLIDES)

    # Navigation controls
    col1, col2 = st.columns(2)

    with col1:
        if st.button("⬅️ Previous", disabled=current_step <= 1):
            st.session_state.current_step = current_step - 1
            st.rerun()

    with col2:
        if st.button("Next ➡️", disabled=current_step >= total_steps):
            st.session_state.current_step = current_step + 1
            st.rerun()

    st.write(f"**Step {current_step} of {total_steps}**")

    if st.button("🔄 Reset Demo"):
        st.session_state.current_step = 1
        st.rerun()

    st.divider()

    # Display current slide
    st.markdown(SLIDES.get(current_step, "No content available"))

# Main content area - Tabbed interface
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🌐 Load Balancer Configuration", "📡 Gnuradio Control", "☁️ Bluesky Control", "🚀 Speed Test", "📊 Load Balancer Monitor"])

# TAB 1: Load Balancer Configuration
with tab1:
    # Admin Hostname input with Test SSH button inline
    col_host, col_test = st.columns([3, 1])

    # Get current SSH hostname for status display
    ssh_hostname = st.session_state.get('ssh_hostname', config.get('ssh', {}).get('hostname', 'wash-dtn1-mgt.es.net'))

    # Prepare status text
    if config.get('ssh', {}).get('enabled', True):
        ssh_status = st.session_state.get('ssh_connected', None)

        if ssh_status is None:
            status_text = f"🔘 Not tested"
        elif ssh_status:
            status_text = f"✅ Connected"
        else:
            status_text = f"❌ Connection failed"
    else:
        status_text = "🔘 SSH disabled"

    # Row 1: Labels/Status
    with col_host:
        st.markdown("**Admin Hostname**")

    with col_test:
        st.markdown(f"**{status_text}**")

    # Row 2: Input field and button
    with col_host:
        ssh_hostname = st.text_input(
            "Admin Hostname",
            value=ssh_hostname,
            help="Remote host for SSH connection (e.g., wash-dtn1-mgt.es.net)",
            key="ssh_hostname_input",
            label_visibility="collapsed"
        )
        # Update session state and config dynamically
        st.session_state.ssh_hostname = ssh_hostname
        config['ssh']['hostname'] = ssh_hostname

    with col_test:
        if config.get('ssh', {}).get('enabled', True):
            if st.button("🔍 Test SSH", key="test_ssh_btn", use_container_width=True):
                test_ssh_connection()

    # Admin URI input with obfuscation toggle
    # Add label row above both elements
    st.markdown("**EJFAT Admin URI**")

    col_uri, col_toggle = st.columns([10, 1])

    with col_uri:
        # Single source of truth: store only the full URI
        if 'admin_uri_full' not in st.session_state:
            st.session_state.admin_uri_full = st.session_state.get('admin_uri', config['default_admin_uri'])

        # Derived value: calculate display URI from source of truth + toggle state
        is_obfuscated = st.session_state.get('obfuscate_uri', True)
        display_uri = obfuscate_uri_token(st.session_state.admin_uri_full) if is_obfuscated else st.session_state.admin_uri_full

        # Dynamic key changes when obfuscation toggles, forcing widget recreation
        admin_uri = st.text_input(
            "EJFAT Admin URI",
            value=display_uri,
            help="URI for E2SAR admin/control plane (from EJFAT_URI_BETA or EJFAT_URI env var)",
            key=f"admin_uri_input_{is_obfuscated}",
            disabled=is_obfuscated,  # Only allow editing when not obfuscated
            label_visibility="collapsed"
        )

        # Update source of truth when user edits (only when obfuscation is off)
        if not is_obfuscated and admin_uri != st.session_state.admin_uri_full:
            st.session_state.admin_uri_full = admin_uri

        # Convenience: keep admin_uri in sync for backward compatibility
        st.session_state.admin_uri = st.session_state.admin_uri_full

    with col_toggle:
        # Toggle button for obfuscation
        toggle_icon = "🔒" if st.session_state.get('obfuscate_uri', True) else "👁️"
        if st.button(toggle_icon, key="toggle_obfuscate", help="Toggle URI obfuscation", use_container_width=True):
            # Simply flip the toggle - widgets will recreate with new keys
            st.session_state.obfuscate_uri = not st.session_state.get('obfuscate_uri', True)
            st.rerun()

    # Instance URI input (full width, below admin URI)
    # Add label above input to match other labels
    st.markdown("**Instance URI**")

    # Single source of truth: store only the full URI
    if 'instance_uri_full' not in st.session_state:
        st.session_state.instance_uri_full = st.session_state.get('instance_uri', '')

    # Derived value: calculate display URI from source of truth + toggle state
    is_obfuscated = st.session_state.get('obfuscate_uri', True)
    display_instance_uri = obfuscate_uri_token(st.session_state.instance_uri_full) if is_obfuscated else st.session_state.instance_uri_full

    # Dynamic key changes when obfuscation toggles OR when instance URI changes, forcing widget recreation
    # Include a hash of the full URI in the key to ensure widget recreates when value changes
    instance_uri_hash = hash(st.session_state.instance_uri_full) if st.session_state.instance_uri_full else 0
    instance_uri = st.text_input(
        "Instance URI",
        value=display_instance_uri,
        disabled=True,  # Instance URI is always read-only (set by reserve operation)
        help="URI assigned after reserving load balancer",
        key=f"instance_uri_input_{is_obfuscated}_{instance_uri_hash}",
        label_visibility="collapsed"
    )

    # Convenience: keep instance_uri in sync for backward compatibility
    st.session_state.instance_uri = st.session_state.instance_uri_full

    # Reserve LB section with duration input and Free LB button
    col_label, col_duration, col_reserve, col_free, col_spacer = st.columns([0.5, 0.7, 1.5, 1.5, 0.8])

    with col_label:
        st.markdown('<div class="duration-label">Duration</div>', unsafe_allow_html=True)

    with col_duration:
        duration_input = st.text_input(
            "Duration",
            value=st.session_state.get('lb_duration', '1:00:00'),
            help="Load balancer reservation duration in HH:MM:SS format (e.g., 1:00:00 for 1 hour)",
            key="duration_input",
            disabled=st.session_state.get('lb_reserved', False),
            max_chars=8,
            label_visibility="collapsed"
        )
        # Update session state with duration
        st.session_state.lb_duration = duration_input

        # Validate and show feedback
        is_valid, formatted_duration, error_msg = validate_duration_format(duration_input)
        if not is_valid and duration_input:
            st.error(error_msg)

    with col_reserve:
        if st.button("🔒 Reserve LB", disabled=st.session_state.get('lb_reserved', False), use_container_width=True):
            reserve_load_balancer()

    with col_free:
        if st.button("🔓 Free LB", disabled=not st.session_state.get('lb_reserved', False), use_container_width=True):
            free_load_balancer()

    with col_spacer:
        pass  # Empty column for spacing

    # Display reserve command directly
    reserve_cmd = lbadm_manager.get_reserve_command(st.session_state.admin_uri_full, st.session_state.get('lb_duration', '1:00:00'))
    # Obfuscate URI in command display if enabled
    display_reserve_cmd = reserve_cmd
    if st.session_state.get('obfuscate_uri', True):
        full_uri = st.session_state.get('admin_uri_full', '')
        if full_uri:
            obfuscated = obfuscate_uri_token(full_uri)
            display_reserve_cmd = reserve_cmd.replace(full_uri, obfuscated)
    st.code(display_reserve_cmd, language="bash")

    # Display free command directly
    free_cmd = lbadm_manager.get_free_command(st.session_state.get('instance_uri_full', ''))
    # Obfuscate URI in command display if enabled
    display_free_cmd = free_cmd
    if st.session_state.get('obfuscate_uri', True):
        instance_uri = st.session_state.get('instance_uri_full', '')
        if instance_uri:
            obfuscated = obfuscate_uri_token(instance_uri)
            display_free_cmd = free_cmd.replace(instance_uri, obfuscated)
    st.code(display_free_cmd, language="bash")

# TAB 2: Gnuradio Control
with tab2:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Transmitter")
        tx_status = st.session_state.get('tx_running', False)
        st.metric("Status", "Running ✅" if tx_status else "Stopped ⏸️")

        col_tx1, col_tx2 = st.columns(2)
        with col_tx1:
            if st.button("▶️ Start TX", disabled=tx_status):
                start_transmitter()
        with col_tx2:
            if st.button("⏹️ Stop TX", disabled=not tx_status):
                stop_transmitter()

        # Show Flowgraph button
        if st.button("📊 Show TX Flowgraph", use_container_width=True):
            open_transmitter_flowgraph()

    with col2:
        st.subheader("Receiver")
        rx_status = st.session_state.get('rx_running', False)
        st.metric("Status", "Running ✅" if rx_status else "Stopped ⏸️")

        col_rx1, col_rx2 = st.columns(2)
        with col_rx1:
            if st.button("▶️ Start RX", disabled=rx_status):
                start_receiver()
        with col_rx2:
            if st.button("⏹️ Stop RX", disabled=not rx_status):
                stop_receiver()

        # Show Flowgraph button
        if st.button("📊 Show RX Flowgraph", use_container_width=True):
            open_receiver_flowgraph()

# TAB 3: Bluesky Control
with tab3:
    st.info("Coming soon")

# TAB 4: Speed Test
with tab4:
    st.header("🚀 Network Speed Test")

    # DTN endpoints list
    dtn_endpoints = [
        "cern773-dtn1.es.net",
        "denv-dtn1.es.net",
        "hous-dtn1.es.net",
        "star-dtn1.es.net",
        "sunn-dtn1.es.net",
        "wash-dtn1.es.net"
    ]

    # Special endpoint with nodes multiplier
    perlmutter_endpoint = "perlmutter.nersc.gov"

    # Initialize session state for DTN endpoint selection, test status, rates, sockets, and jobs
    if 'dtn_enabled' not in st.session_state:
        st.session_state.dtn_enabled = {dtn: False for dtn in dtn_endpoints}
        st.session_state.dtn_enabled[perlmutter_endpoint] = False
    if 'dtn_test_status' not in st.session_state:
        st.session_state.dtn_test_status = {dtn: None for dtn in dtn_endpoints}
        st.session_state.dtn_test_status[perlmutter_endpoint] = None
    if 'dtn_tx_rate' not in st.session_state:
        st.session_state.dtn_tx_rate = {dtn: 1.0 for dtn in dtn_endpoints}
        st.session_state.dtn_tx_rate[perlmutter_endpoint] = 1.0
    if 'dtn_tx_sockets' not in st.session_state:
        st.session_state.dtn_tx_sockets = {dtn: 4 for dtn in dtn_endpoints}
        st.session_state.dtn_tx_sockets[perlmutter_endpoint] = 4
    if 'dtn_rx_sockets' not in st.session_state:
        st.session_state.dtn_rx_sockets = {dtn: 4 for dtn in dtn_endpoints}
        st.session_state.dtn_rx_sockets[perlmutter_endpoint] = 4
    if 'dtn_tx_jobs' not in st.session_state:
        st.session_state.dtn_tx_jobs = {dtn: 1 for dtn in dtn_endpoints}
        st.session_state.dtn_tx_jobs[perlmutter_endpoint] = 1
    if 'dtn_rx_jobs' not in st.session_state:
        st.session_state.dtn_rx_jobs = {dtn: 1 for dtn in dtn_endpoints}
        st.session_state.dtn_rx_jobs[perlmutter_endpoint] = 1
    if 'perlmutter_nodes' not in st.session_state:
        st.session_state.perlmutter_nodes = 1

    # Display column headers once at the top - now includes Nodes, Tx Jobs, and Rx Jobs columns
    col_checkbox_hdr, col_host_hdr, col_nodes_hdr, col_tx_rate_hdr, col_tx_jobs_hdr, col_total_rate_hdr, col_tx_sockets_hdr, col_rx_sockets_hdr, col_rx_jobs_hdr, col_test_hdr = st.columns([0.3, 1.4, 0.5, 0.7, 0.5, 0.8, 0.7, 0.7, 0.5, 1])

    with col_checkbox_hdr:
        st.markdown("")  # Empty for alignment

    with col_host_hdr:
        st.markdown("**Endpoint**")

    with col_nodes_hdr:
        st.markdown("**Nodes**")

    with col_tx_rate_hdr:
        st.markdown("**Tx Rate (Gbps)**")

    with col_tx_jobs_hdr:
        st.markdown("**Tx Jobs**")

    with col_total_rate_hdr:
        st.markdown("**Total Rate (Gbps)**")

    with col_tx_sockets_hdr:
        st.markdown("**Tx Sockets**")

    with col_rx_sockets_hdr:
        st.markdown("**Rx Sockets**")

    with col_rx_jobs_hdr:
        st.markdown("**Rx Jobs**")

    with col_test_hdr:
        st.markdown("**Status**")

    # Create rows for each DTN endpoint
    for dtn_name in dtn_endpoints:
        # Column layout with all columns including Nodes, Tx Jobs, and Rx Jobs
        col_checkbox, col_host, col_nodes, col_tx_rate, col_tx_jobs, col_total_rate, col_tx_sockets, col_rx_sockets, col_rx_jobs, col_test = st.columns([0.3, 1.4, 0.5, 0.7, 0.5, 0.8, 0.7, 0.7, 0.5, 1])

        # Get test status for this endpoint
        test_status = st.session_state.dtn_test_status.get(dtn_name, None)

        if test_status is None:
            status_text = ""
        elif test_status:
            status_text = "✅ Passed"
        else:
            status_text = "❌ Failed"

        # Checkbox
        with col_checkbox:
            enabled = st.checkbox(
                "Enable",
                value=st.session_state.dtn_enabled.get(dtn_name, False),
                key=f"checkbox_{dtn_name}",
                label_visibility="collapsed"
            )
            st.session_state.dtn_enabled[dtn_name] = enabled

        # Hostname
        with col_host:
            st.markdown(f"{dtn_name}")

        # Nodes column (hidden for DTN endpoints - just empty space)
        with col_nodes:
            st.markdown("")  # Empty - nodes not applicable for DTN endpoints

        # Tx Rate Input
        with col_tx_rate:
            tx_rate = st.number_input(
                f"Tx Rate for {dtn_name}",
                value=st.session_state.dtn_tx_rate.get(dtn_name, 1.0),
                min_value=0.1,
                max_value=20.0,  # Enforce 20 Gbps max per Tx Rate
                step=0.1,
                format="%.1f",
                key=f"tx_rate_{dtn_name}",
                label_visibility="collapsed"
            )
            st.session_state.dtn_tx_rate[dtn_name] = tx_rate
            # Warn if at or near limit
            if tx_rate >= 20.0:
                st.caption("⚠️ Max limit")

        # Tx Jobs Input
        with col_tx_jobs:
            tx_jobs = st.number_input(
                f"Tx Jobs for {dtn_name}",
                value=st.session_state.dtn_tx_jobs.get(dtn_name, 1),
                min_value=1,
                max_value=128,
                step=1,
                key=f"tx_jobs_{dtn_name}",
                label_visibility="collapsed"
            )
            st.session_state.dtn_tx_jobs[dtn_name] = tx_jobs

        # Total Rate (calculated)
        with col_total_rate:
            total_rate = tx_rate * tx_jobs
            # Enforce 90 Gbps limit for DTN endpoints
            if total_rate > 90.0:
                st.markdown(f"⚠️ **{total_rate:.1f}** (exceeds 90 Gbps limit)")
            else:
                st.markdown(f"{total_rate:.1f}")

        # Tx Sockets Input
        with col_tx_sockets:
            tx_sockets = st.number_input(
                f"Tx Sockets for {dtn_name}",
                value=st.session_state.dtn_tx_sockets.get(dtn_name, 4),
                min_value=1,
                max_value=64,
                step=1,
                key=f"tx_sockets_{dtn_name}",
                label_visibility="collapsed"
            )
            st.session_state.dtn_tx_sockets[dtn_name] = tx_sockets

        # Rx Sockets Input
        with col_rx_sockets:
            rx_sockets = st.number_input(
                f"Rx Sockets for {dtn_name}",
                value=st.session_state.dtn_rx_sockets.get(dtn_name, 4),
                min_value=1,
                max_value=64,
                step=1,
                key=f"rx_sockets_{dtn_name}",
                label_visibility="collapsed"
            )
            st.session_state.dtn_rx_sockets[dtn_name] = rx_sockets

        # Rx Jobs Input
        with col_rx_jobs:
            rx_jobs = st.number_input(
                f"Rx Jobs for {dtn_name}",
                value=st.session_state.dtn_rx_jobs.get(dtn_name, 1),
                min_value=1,
                max_value=128,
                step=1,
                key=f"rx_jobs_{dtn_name}",
                label_visibility="collapsed"
            )
            st.session_state.dtn_rx_jobs[dtn_name] = rx_jobs

        # Status
        with col_test:
            st.markdown(f"{status_text}")

    # Add Perlmutter row with nodes multiplier (same column layout as DTN endpoints)
    col_checkbox_perlm, col_host_perlm, col_nodes_perlm, col_tx_rate_perlm, col_tx_jobs_perlm, col_total_rate_perlm, col_tx_sockets_perlm, col_rx_sockets_perlm, col_rx_jobs_perlm, col_test_perlm = st.columns([0.3, 1.4, 0.5, 0.7, 0.5, 0.8, 0.7, 0.7, 0.5, 1])

    # Get test status for perlmutter
    test_status_perlm = st.session_state.dtn_test_status.get(perlmutter_endpoint, None)

    if test_status_perlm is None:
        status_text_perlm = ""
    elif test_status_perlm:
        status_text_perlm = "✅ Passed"
    else:
        status_text_perlm = "❌ Failed"

    # Checkbox
    with col_checkbox_perlm:
        enabled_perlm = st.checkbox(
            "Enable",
            value=st.session_state.dtn_enabled.get(perlmutter_endpoint, False),
            key=f"checkbox_{perlmutter_endpoint}",
            label_visibility="collapsed"
        )
        st.session_state.dtn_enabled[perlmutter_endpoint] = enabled_perlm

    # Hostname
    with col_host_perlm:
        st.markdown(f"{perlmutter_endpoint}")

    # Nodes Input (special for Perlmutter) - visible for this row only
    with col_nodes_perlm:
        nodes_perlm = st.number_input(
            f"Nodes for {perlmutter_endpoint}",
            value=st.session_state.perlmutter_nodes,
            min_value=1,
            max_value=128,
            step=1,
            key=f"nodes_{perlmutter_endpoint}",
            label_visibility="collapsed"
        )
        st.session_state.perlmutter_nodes = nodes_perlm

    # Tx Rate Input
    with col_tx_rate_perlm:
        tx_rate_perlm = st.number_input(
            f"Tx Rate for {perlmutter_endpoint}",
            value=st.session_state.dtn_tx_rate.get(perlmutter_endpoint, 1.0),
            min_value=0.1,
            max_value=20.0,  # Enforce 20 Gbps max per Tx Rate
            step=0.1,
            format="%.1f",
            key=f"tx_rate_{perlmutter_endpoint}",
            label_visibility="collapsed"
        )
        st.session_state.dtn_tx_rate[perlmutter_endpoint] = tx_rate_perlm
        # Warn if at or near limit
        if tx_rate_perlm >= 20.0:
            st.caption("⚠️ Max limit")

    # Tx Jobs Input
    with col_tx_jobs_perlm:
        tx_jobs_perlm = st.number_input(
            f"Tx Jobs for {perlmutter_endpoint}",
            value=st.session_state.dtn_tx_jobs.get(perlmutter_endpoint, 1),
            min_value=1,
            max_value=128,
            step=1,
            key=f"tx_jobs_{perlmutter_endpoint}",
            label_visibility="collapsed"
        )
        st.session_state.dtn_tx_jobs[perlmutter_endpoint] = tx_jobs_perlm

    # Total Rate (calculated: tx_rate * tx_jobs * nodes)
    with col_total_rate_perlm:
        total_rate_perlm = tx_rate_perlm * tx_jobs_perlm * nodes_perlm
        # Enforce 180 Gbps limit for Perlmutter
        if total_rate_perlm > 180.0:
            st.markdown(f"⚠️ **{total_rate_perlm:.1f}** (exceeds 180 Gbps limit)")
        else:
            st.markdown(f"{total_rate_perlm:.1f}")

    # Tx Sockets Input (will be multiplied by nodes in aggregate)
    with col_tx_sockets_perlm:
        tx_sockets_perlm = st.number_input(
            f"Tx Sockets for {perlmutter_endpoint}",
            value=st.session_state.dtn_tx_sockets.get(perlmutter_endpoint, 4),
            min_value=1,
            max_value=64,
            step=1,
            key=f"tx_sockets_{perlmutter_endpoint}",
            label_visibility="collapsed"
        )
        st.session_state.dtn_tx_sockets[perlmutter_endpoint] = tx_sockets_perlm

    # Rx Sockets Input (will be multiplied by nodes in aggregate)
    with col_rx_sockets_perlm:
        rx_sockets_perlm = st.number_input(
            f"Rx Sockets for {perlmutter_endpoint}",
            value=st.session_state.dtn_rx_sockets.get(perlmutter_endpoint, 4),
            min_value=1,
            max_value=64,
            step=1,
            key=f"rx_sockets_{perlmutter_endpoint}",
            label_visibility="collapsed"
        )
        st.session_state.dtn_rx_sockets[perlmutter_endpoint] = rx_sockets_perlm

    # Rx Jobs Input
    with col_rx_jobs_perlm:
        rx_jobs_perlm = st.number_input(
            f"Rx Jobs for {perlmutter_endpoint}",
            value=st.session_state.dtn_rx_jobs.get(perlmutter_endpoint, 1),
            min_value=1,
            max_value=128,
            step=1,
            key=f"rx_jobs_{perlmutter_endpoint}",
            label_visibility="collapsed"
        )
        st.session_state.dtn_rx_jobs[perlmutter_endpoint] = rx_jobs_perlm

    # Status
    with col_test_perlm:
        st.markdown(f"{status_text_perlm}")

    # Add aggregate summary row
    st.divider()

    col_checkbox_sum, col_host_sum, col_nodes_sum, col_tx_rate_sum, col_tx_jobs_sum, col_total_rate_sum, col_tx_sockets_sum, col_rx_sockets_sum, col_rx_jobs_sum, col_test_sum = st.columns([0.3, 1.4, 0.5, 0.7, 0.5, 0.8, 0.7, 0.7, 0.5, 1])

    # Calculate aggregates
    total_aggregate_rate = 0.0
    total_aggregate_tx_sockets = 0
    total_aggregate_rx_sockets = 0

    for dtn_name in dtn_endpoints:
        if st.session_state.dtn_enabled.get(dtn_name, False):
            tx_rate = st.session_state.dtn_tx_rate.get(dtn_name, 1.0)
            tx_jobs = st.session_state.dtn_tx_jobs.get(dtn_name, 1)
            rx_jobs = st.session_state.dtn_rx_jobs.get(dtn_name, 1)
            tx_sockets = st.session_state.dtn_tx_sockets.get(dtn_name, 4)
            rx_sockets = st.session_state.dtn_rx_sockets.get(dtn_name, 4)

            # Sum total rates (based on tx jobs)
            total_aggregate_rate += tx_rate * tx_jobs

            # Sum tx sockets × tx jobs
            total_aggregate_tx_sockets += tx_sockets * tx_jobs

            # Sum rx sockets × rx jobs
            total_aggregate_rx_sockets += rx_sockets * rx_jobs

    # Add perlmutter contribution (multiplied by nodes)
    if st.session_state.dtn_enabled.get(perlmutter_endpoint, False):
        tx_rate_perlm = st.session_state.dtn_tx_rate.get(perlmutter_endpoint, 1.0)
        tx_jobs_perlm = st.session_state.dtn_tx_jobs.get(perlmutter_endpoint, 1)
        rx_jobs_perlm = st.session_state.dtn_rx_jobs.get(perlmutter_endpoint, 1)
        nodes_perlm = st.session_state.perlmutter_nodes
        tx_sockets_perlm = st.session_state.dtn_tx_sockets.get(perlmutter_endpoint, 4)
        rx_sockets_perlm = st.session_state.dtn_rx_sockets.get(perlmutter_endpoint, 4)

        # Sum total rates (tx_rate × tx_jobs × nodes)
        total_aggregate_rate += tx_rate_perlm * tx_jobs_perlm * nodes_perlm

        # Sum tx sockets × tx_jobs × nodes
        total_aggregate_tx_sockets += tx_sockets_perlm * tx_jobs_perlm * nodes_perlm

        # Sum rx sockets × rx_jobs × nodes
        total_aggregate_rx_sockets += rx_sockets_perlm * rx_jobs_perlm * nodes_perlm

    with col_checkbox_sum:
        st.markdown("")

    with col_host_sum:
        st.markdown("**Total (Enabled)**")

    with col_nodes_sum:
        st.markdown("")  # Empty - nodes column for alignment

    with col_tx_rate_sum:
        st.markdown("")

    with col_tx_jobs_sum:
        st.markdown("")

    with col_total_rate_sum:
        st.markdown(f"**{total_aggregate_rate:.1f}**")

    with col_tx_sockets_sum:
        st.markdown(f"**{total_aggregate_tx_sockets}**")

    with col_rx_sockets_sum:
        st.markdown(f"**{total_aggregate_rx_sockets}**")

    with col_rx_jobs_sum:
        st.markdown("")

    with col_test_sum:
        st.markdown("")

    # Check for limit violations
    violations = []

    for dtn_name in dtn_endpoints:
        if st.session_state.dtn_enabled.get(dtn_name, False):
            tx_rate = st.session_state.dtn_tx_rate.get(dtn_name, 1.0)
            tx_jobs = st.session_state.dtn_tx_jobs.get(dtn_name, 1)
            total_rate = tx_rate * tx_jobs
            if total_rate > 90.0:
                violations.append(f"{dtn_name}: {total_rate:.1f} Gbps (limit: 90 Gbps)")

    if st.session_state.dtn_enabled.get(perlmutter_endpoint, False):
        tx_rate_perlm = st.session_state.dtn_tx_rate.get(perlmutter_endpoint, 1.0)
        tx_jobs_perlm = st.session_state.dtn_tx_jobs.get(perlmutter_endpoint, 1)
        nodes_perlm = st.session_state.perlmutter_nodes
        total_rate_perlm = tx_rate_perlm * tx_jobs_perlm * nodes_perlm
        if total_rate_perlm > 180.0:
            violations.append(f"{perlmutter_endpoint}: {total_rate_perlm:.1f} Gbps (limit: 180 Gbps)")

    if violations:
        st.warning("⚠️ **Rate Limit Violations:**\n\n" + "\n\n".join([f"- {v}" for v in violations]))

# TAB 5: Load Balancer Monitor
with tab5:
    # Monitor control buttons
    monitoring_active = st.session_state.get('monitoring_active', False)

    col_monitor1, col_monitor2 = st.columns(2)

    with col_monitor1:
        if st.button("▶️ Start Monitoring", disabled=monitoring_active, use_container_width=True):
            start_monitoring()
            st.rerun()

    with col_monitor2:
        if st.button("⏹️ Stop Monitoring", disabled=not monitoring_active, use_container_width=True):
            stop_monitoring()
            st.rerun()

    # Show monitoring status
    if monitoring_active:
        st.success("✅ Load balancer data fetched")
    else:
        st.info("⏸️ No data fetched yet")

    # Display monitor command
    st.caption("💻 SSH Command:")
    monitor_cmd = lbadm_manager.get_overview_command(st.session_state.admin_uri_full)
    # Obfuscate URI in command display if enabled
    display_monitor_cmd = monitor_cmd
    if st.session_state.get('obfuscate_uri', True):
        full_uri = st.session_state.get('admin_uri_full', '')
        if full_uri:
            obfuscated = obfuscate_uri_token(full_uri)
            display_monitor_cmd = monitor_cmd.replace(full_uri, obfuscated)
    st.code(display_monitor_cmd, language="bash")

    st.divider()

    # Display load balancer overview
    lb_overview = st.session_state.get('lb_overview', [])
    last_update = st.session_state.get('last_monitor_update', 0)

    if last_update > 0:
        # Show last update time
        update_time = datetime.fromtimestamp(last_update).strftime("%H:%M:%S")
        st.caption(f"Last updated: {update_time}")

    if lb_overview:
        # Create a panel for each load balancer
        st.subheader(f"Active Load Balancers ({len(lb_overview)})")

        for lb in lb_overview:
            with st.container():
                col_name, col_id, col_senders, col_workers, col_expiry, col_remaining, col_delete = st.columns([2, 1, 2, 2, 2, 1.5, 0.5])

                with col_name:
                    st.markdown(f"**{lb['name']}**")

                with col_id:
                    st.markdown(f"ID: {lb['id']}")

                with col_senders:
                    senders = lb.get('senders', [])
                    if senders:
                        st.markdown(f"**Senders:** {', '.join(senders)}")
                    else:
                        st.markdown("**Senders:** None")

                with col_workers:
                    workers = lb.get('workers', [])
                    if workers:
                        st.markdown(f"**Workers:** {', '.join(workers)}")
                    else:
                        st.markdown("**Workers:** None")

                with col_expiry:
                    expiry = lb.get('expiry', '')
                    if expiry:
                        st.markdown(f"**Expires:** {expiry}")
                    else:
                        st.markdown("**Expires:** N/A")

                with col_remaining:
                    expiry = lb.get('expiry', '')
                    if expiry:
                        try:
                            # Try parsing ISO 8601 format with Z (e.g., "2025-10-14T12:30:45Z")
                            if 'T' in expiry:
                                expiry_time = datetime.strptime(expiry, "%Y-%m-%dT%H:%M:%SZ")
                            else:
                                # Fallback to space-separated format (e.g., "2025-10-14 12:30:45")
                                expiry_time = datetime.strptime(expiry, "%Y-%m-%d %H:%M:%S")

                            current_time = datetime.now()
                            remaining = expiry_time - current_time

                            # Format remaining time
                            if remaining.total_seconds() > 0:
                                # Calculate hours, minutes, seconds
                                total_seconds = int(remaining.total_seconds())
                                hours = total_seconds // 3600
                                minutes = (total_seconds % 3600) // 60
                                seconds = total_seconds % 60
                                st.markdown(f"**Remaining:** {hours}h {minutes}m {seconds}s")
                            else:
                                st.markdown("**Remaining:** ⚠️ Expired")
                        except Exception as e:
                            # If parsing fails, show the error for debugging
                            st.markdown(f"**Remaining:** N/A (format: {expiry[:20]}...)")
                    else:
                        st.markdown("**Remaining:** N/A")

                with col_delete:
                    # Trash icon to force free this LB
                    if st.button("🗑️", key=f"delete_{lb['id']}", help=f"Force free {lb['name']}"):
                        st.session_state.confirm_delete_lbid = lb['id']
                        st.rerun()

                # Show confirmation dialog if this LB is pending deletion
                if st.session_state.get('confirm_delete_lbid') == lb['id']:
                    st.warning(f"⚠️ Are you sure you want to force free **{lb['name']}** (ID: {lb['id']})?")
                    col_confirm, col_cancel = st.columns(2)

                    with col_confirm:
                        if st.button("✅ Confirm", key=f"confirm_{lb['id']}", use_container_width=True):
                            force_free_load_balancer(lb['id'], lb['name'])

                    with col_cancel:
                        if st.button("❌ Cancel", key=f"cancel_{lb['id']}", use_container_width=True):
                            st.session_state.confirm_delete_lbid = None
                            st.rerun()

                st.divider()
    elif last_update > 0:
        # Monitoring has run but no LBs found
        st.warning("⚠️ No active load balancers found")
    else:
        # Not yet monitored
        st.info("Click 'Start Monitoring' to view active load balancers")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #9CA3AF; padding: 20px;'>
    <p>FM Radio E2SAR Demo Dashboard | Built with Streamlit</p>
    <p>For help, see the demo guide in the sidebar</p>
</div>
""", unsafe_allow_html=True)
