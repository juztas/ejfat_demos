# FM Radio E2SAR Demo Dashboard - Implementation Plan

**Framework:** Streamlit
**Date:** 2025-10-14
**Status:** Ready for implementation

---

## Executive Summary

Build a **Streamlit-based dashboard** to orchestrate the FM Radio E2SAR demo. Streamlit offers:
- **Simple Python-only development** (~100-150 lines of code)
- **Modern UI out of the box** (matches reference design aesthetic)
- **Built-in components** for buttons, text inputs, status displays
- **Native markdown support** for Marp slide integration
- **Session state** for tracking demo workflow steps

---

## Architecture Overview

### Technology Stack
- **Frontend:** Streamlit (Python web framework)
- **Backend:** Python subprocess management
- **Slides:** Marp markdown (exported to HTML, embedded in Streamlit)
- **E2SAR Integration:** e2sar_py library (when available) or direct URI management
- **Process Control:** Python subprocess + XML-RPC for GRC control

### File Structure
```
demos/fm_bluesky/
├── dashboard.py              # Main Streamlit app (100-150 lines)
├── dashboard_config.yaml     # Configuration file
├── slides/
│   ├── demo_slides.md        # Marp markdown source
│   └── demo_slides.html      # Generated HTML (marp cli)
├── utils/
│   ├── process_manager.py    # Process management helpers
│   └── e2sar_manager.py      # E2SAR/LB management (optional)
└── DASHBOARD_PLAN.md         # This file
```

---

## Component Design

### 1. Main Dashboard Layout

Streamlit uses a **columnar layout** with built-in components:

```python
import streamlit as st

# Page config
st.set_page_config(
    page_title="FM Radio E2SAR Demo",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling (matches reference design)
st.markdown("""
<style>
    /* Primary green theme */
    .stButton>button {
        background-color: #6B7D4F;
        color: white;
        border-radius: 24px;
        padding: 12px 32px;
        border: none;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #5A6D3F;
    }
    /* Card-like containers */
    .element-container {
        background: white;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
</style>
""", unsafe_allow_html=True)
```

### 2. Load Balancer Control Panel

**Component:** Streamlit columns + text inputs + buttons

```python
st.header("🌐 Load Balancer Configuration")

col1, col2 = st.columns(2)

with col1:
    admin_uri = st.text_input(
        "EJFAT Admin URI",
        value=st.session_state.get('admin_uri', 'ejfat://admin@192.168.100.1:9876'),
        help="URI for E2SAR admin/control plane"
    )

with col2:
    instance_uri = st.text_input(
        "Instance URI",
        value=st.session_state.get('instance_uri', ''),
        disabled=not st.session_state.get('lb_reserved', False),
        help="URI assigned after reserving load balancer"
    )

# Reserve/Free buttons
col3, col4, col5 = st.columns([1, 1, 3])

with col3:
    if st.button("🔒 Reserve LB", disabled=st.session_state.get('lb_reserved', False)):
        reserve_load_balancer()

with col4:
    if st.button("🔓 Free LB", disabled=not st.session_state.get('lb_reserved', False)):
        free_load_balancer()
```

**Features:**
- Text inputs are editable
- Instance URI disabled until LB is reserved
- Button states automatically managed by session state
- Color-coded status indicators

### 3. Transmitter/Receiver Control Panel

**Component:** Streamlit buttons + status indicators

```python
st.header("📡 Flowgraph Control")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Transmitter")
    tx_status = st.session_state.get('tx_running', False)
    st.metric("Status", "Running" if tx_status else "Stopped",
              delta="Active" if tx_status else None)

    col_tx1, col_tx2 = st.columns(2)
    with col_tx1:
        if st.button("▶️ Start TX", disabled=tx_status):
            start_transmitter()
    with col_tx2:
        if st.button("⏹️ Stop TX", disabled=not tx_status):
            stop_transmitter()

with col2:
    st.subheader("Receiver")
    rx_status = st.session_state.get('rx_running', False)
    st.metric("Status", "Running" if rx_status else "Stopped",
              delta="Active" if rx_status else None)

    col_rx1, col_rx2 = st.columns(2)
    with col_rx1:
        if st.button("▶️ Start RX", disabled=rx_status):
            start_receiver()
    with col_rx2:
        if st.button("⏹️ Stop RX", disabled=not rx_status):
            stop_receiver()
```

**Features:**
- `st.metric()` provides built-in status display with optional delta indicator
- Buttons disabled based on process state
- Clean two-column layout

### 4. Status & Feedback Display

**Component:** Streamlit status containers + expanders

```python
st.header("📊 System Status")

# Status overview (card-style)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("LB Status", "Reserved" if st.session_state.get('lb_reserved') else "Free",
              delta="Connected" if st.session_state.get('lb_reserved') else None)

with col2:
    st.metric("TX Process", "Running" if st.session_state.get('tx_running') else "Stopped")

with col3:
    st.metric("RX Process", "Running" if st.session_state.get('rx_running') else "Stopped")

with col4:
    st.metric("Demo Step", f"{st.session_state.get('current_step', 1)}/7")

# Log viewer (collapsible)
with st.expander("📜 System Logs", expanded=False):
    log_placeholder = st.empty()
    logs = st.session_state.get('logs', [])
    log_placeholder.text_area("Logs", value="\n".join(logs[-20:]), height=200)

# Real-time status using st.status
with st.status("Processing...", expanded=True) as status:
    st.write("Transmitter: ✅ Ready")
    st.write("Receiver: ✅ Ready")
    status.update(label="All systems operational", state="complete")
```

**Features:**
- `st.metric()` for key performance indicators (KPIs)
- `st.expander()` for collapsible log viewer
- `st.status()` for real-time operation feedback
- Automatic styling matches modern dashboard aesthetic

### 5. Narration Window with Marp Slides

**Component:** HTML iframe + navigation controls

#### Step 1: Generate HTML from Marp markdown

```bash
# Install Marp CLI (one-time setup)
npm install -g @marp-team/marp-cli

# Generate HTML from markdown
marp slides/demo_slides.md -o slides/demo_slides.html --html
```

#### Step 2: Embed in Streamlit

```python
st.header("📖 Demo Narration")

# Current slide/step
current_step = st.session_state.get('current_step', 1)
total_steps = 7  # Total number of slides

# Navigation controls
col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

with col1:
    if st.button("⬅️ Previous", disabled=current_step <= 1):
        st.session_state.current_step = current_step - 1
        st.rerun()

with col2:
    st.write(f"**Step {current_step} of {total_steps}**")

with col4:
    if st.button("➡️ Next", disabled=current_step >= total_steps):
        st.session_state.current_step = current_step + 1
        st.rerun()

with col5:
    if st.button("🔄 Reset"):
        st.session_state.current_step = 1
        st.rerun()

# Display current slide
# Option 1: Load full HTML and extract slide by index
with open('slides/demo_slides.html', 'r') as f:
    slides_html = f.read()
    # Use JavaScript to navigate to slide index
    slide_html = f"""
    <iframe src="slides/demo_slides.html#page={current_step}"
            width="100%" height="500" frameborder="0"></iframe>
    """
    st.components.v1.html(slide_html, height=500)

# Option 2: Pre-split slides into separate HTML files
# st.components.v1.html(open(f'slides/slide_{current_step}.html').read(), height=500)
```

**Alternative (Simpler): Markdown directly in Streamlit**

```python
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
""",
    2: """
# Step 1: Reserve Load Balancer
## Action Required

Click the **"Reserve LB"** button in the control panel above.

**What's happening:**
- Contacts EJFAT admin server
- Allocates a load balancer instance
- Returns an instance URI for data transmission

**Next:** Once reserved, the Instance URI field will populate automatically.
""",
    # ... more slides
}

# Display current slide
st.markdown(SLIDES[current_step])
```

**Features:**
- Navigate through demo steps
- Synchronized with workflow progress
- Beautiful presentation-quality slides (Marp)
- Or simpler inline markdown (Streamlit native)

---

## Session State Management

Streamlit's `st.session_state` tracks demo progress:

```python
# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.current_step = 1
    st.session_state.lb_reserved = False
    st.session_state.admin_uri = 'ejfat://admin@192.168.100.1:9876'
    st.session_state.instance_uri = ''
    st.session_state.tx_running = False
    st.session_state.rx_running = False
    st.session_state.tx_process = None
    st.session_state.rx_process = None
    st.session_state.logs = []
```

---

## Process Management

```python
import subprocess
import os
import signal
from pathlib import Path

def start_transmitter():
    """Start FM transmitter subprocess."""
    fm_dir = Path(__file__).parent.parent / "fm"
    tx_script = fm_dir / "fm_transmitter_e2sar.py"

    try:
        # Start process
        proc = subprocess.Popen(
            ["python", str(tx_script)],
            cwd=str(fm_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )

        # Update session state
        st.session_state.tx_process = proc
        st.session_state.tx_running = True
        st.session_state.logs.append(f"✅ Transmitter started (PID: {proc.pid})")

        # Auto-advance to next step
        if st.session_state.current_step == 2:  # Step 2 is "Start Transmitter"
            st.session_state.current_step = 3

        st.success("Transmitter started successfully!")
        st.rerun()

    except Exception as e:
        st.error(f"Failed to start transmitter: {e}")
        st.session_state.logs.append(f"❌ Transmitter failed: {e}")

def stop_transmitter():
    """Stop FM transmitter subprocess."""
    proc = st.session_state.get('tx_process')
    if proc:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            proc.wait(timeout=3)
            st.session_state.tx_running = False
            st.session_state.tx_process = None
            st.session_state.logs.append("✅ Transmitter stopped")
            st.success("Transmitter stopped")
            st.rerun()
        except Exception as e:
            st.error(f"Error stopping transmitter: {e}")

def start_receiver():
    """Start FM receiver subprocess."""
    # Similar to start_transmitter()
    pass

def stop_receiver():
    """Stop FM receiver subprocess."""
    # Similar to stop_transmitter()
    pass
```

---

## E2SAR Load Balancer Management

### Option 1: Using e2sar_py library (when available)

```python
def reserve_load_balancer():
    """Reserve EJFAT load balancer using e2sar_py."""
    try:
        import e2sar_py

        admin_uri = st.session_state.admin_uri

        # Parse admin URI
        ejfat_uri = e2sar_py.EjfatURI(uri=admin_uri, tt=e2sar_py.EjfatURI.TokenType.admin)

        # Reserve LB (placeholder - need actual API)
        # instance_token = reserve_lb_via_control_plane(ejfat_uri)

        # For now, simulate:
        instance_uri = admin_uri.replace('admin@', 'instance123@')

        st.session_state.instance_uri = instance_uri
        st.session_state.lb_reserved = True
        st.session_state.logs.append(f"✅ Load balancer reserved: {instance_uri}")

        # Auto-advance to next step
        if st.session_state.current_step == 1:
            st.session_state.current_step = 2

        st.success("Load balancer reserved!")
        st.rerun()

    except Exception as e:
        st.error(f"Failed to reserve LB: {e}")
        st.session_state.logs.append(f"❌ LB reservation failed: {e}")

def free_load_balancer():
    """Free EJFAT load balancer."""
    try:
        # Call LB API to release
        st.session_state.instance_uri = ''
        st.session_state.lb_reserved = False
        st.session_state.logs.append("✅ Load balancer freed")
        st.success("Load balancer freed")
        st.rerun()

    except Exception as e:
        st.error(f"Failed to free LB: {e}")
```

### Option 2: Manual URI management (simpler fallback)

```python
def reserve_load_balancer():
    """Simulate LB reservation by generating instance URI."""
    import uuid

    admin_uri = st.session_state.admin_uri

    # Generate instance token
    instance_token = str(uuid.uuid4())[:8]

    # Create instance URI from admin URI
    instance_uri = admin_uri.replace('admin@', f'instance_{instance_token}@')

    st.session_state.instance_uri = instance_uri
    st.session_state.lb_reserved = True
    st.session_state.logs.append(f"✅ Load balancer reserved: {instance_uri}")

    # Auto-advance to next step
    if st.session_state.current_step == 1:
        st.session_state.current_step = 2

    st.success(f"Load balancer reserved! Token: {instance_token}")
    st.rerun()
```

---

## Marp Slides Definition

**File:** `slides/demo_slides.md`

```markdown
---
marp: true
theme: default
paginate: true
style: |
  section {
    background-color: #FAFAFA;
    font-family: 'Inter', 'Roboto', sans-serif;
  }
  h1 {
    color: #6B7D4F;
    font-weight: bold;
  }
  h2 {
    color: #1A1A1A;
    font-weight: 600;
  }
---

# FM Radio E2SAR Demo
## Welcome

This interactive demo will guide you through:
- Reserving an EJFAT load balancer
- Transmitting FM radio signals via E2SAR
- Receiving and decoding the signal

**Duration:** ~5-10 minutes
**Prerequisites:** GNU Radio, E2SAR, RTL-SDR (or simulated source)

---

# Step 1: Reserve Load Balancer
## Action Required ⚡

**What to do:**
1. Review the Admin URI in the control panel
2. Click the **"Reserve LB"** button

**What's happening:**
- Contacts EJFAT admin server at the specified URI
- Allocates a dedicated load balancer instance
- Returns an Instance URI for your data transmission session

**Next:** Once reserved, the Instance URI field will automatically populate.

---

# Step 2: Start Transmitter
## Action Required ⚡

**What to do:**
Click the **"Start TX"** button in the Transmitter panel

**What's happening:**
- Launches `fm_transmitter_e2sar.py` GNU Radio flowgraph
- Initializes RTL-SDR (or signal source)
- Connects to E2SAR segmenter with your Instance URI
- Begins capturing FM signals at 98.5 MHz (default)

**Next:** Wait for "Status: Running" indicator

---

# Step 3: Start Receiver
## Action Required ⚡

**What to do:**
Click the **"Start RX"** button in the Receiver panel

**What's happening:**
- Launches `fm_receiver_e2sar.py` GNU Radio flowgraph
- Initializes E2SAR reassembler to receive data
- Connects to your load balancer instance
- Begins FM demodulation and audio playback

**Next:** You should hear audio from the FM station!

---

# Step 4: Demo Running
## What You're Seeing 🎉

**Signal Flow:**
```
RTL-SDR → GNU Radio TX → E2SAR Segmenter →
EJFAT Load Balancer → E2SAR Reassembler →
GNU Radio RX → Audio Output
```

**Key Concepts:**
- **E2SAR Segmenter:** Breaks GNU Radio data into EJFAT packets
- **Load Balancer:** Routes packets to receiver(s)
- **E2SAR Reassembler:** Reconstructs original signal

**Try:** Change the frequency in the Transmitter GUI to tune to different FM stations!

---

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
- Packet transmission statistics

**Next:** Experiment with the demo, then proceed to cleanup

---

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

**Next:** Review what you learned!

---

# Conclusion
## Summary 🎓

**What you accomplished:**
✅ Reserved an EJFAT load balancer
✅ Transmitted FM radio via E2SAR data plane
✅ Received and decoded the signal
✅ Experienced real-time network load balancing

**Key Takeaways:**
- E2SAR enables efficient data streaming over EJFAT
- Load balancers provide scalable, fault-tolerant routing
- GNU Radio integrates seamlessly with E2SAR blocks

**Thank you for trying the FM Radio E2SAR Demo!**

---
```

---

## Configuration File

**File:** `dashboard_config.yaml`

```yaml
# FM Radio E2SAR Demo Dashboard Configuration

# Default URIs
default_admin_uri: "ejfat://admin@192.168.100.1:9876/lb/1?sync=192.168.0.1:12345"
default_instance_uri: ""

# Flowgraph paths (relative to this config file)
transmitter_script: "../fm/fm_transmitter_e2sar.py"
receiver_script: "../fm/fm_receiver_e2sar.py"

# Startup delays (seconds)
transmitter_startup_delay: 5
receiver_startup_delay: 3

# XML-RPC configuration (for remote control)
xmlrpc_host: "localhost"
xmlrpc_port: 8080

# Demo workflow steps
steps:
  1: "Reserve Load Balancer"
  2: "Start Transmitter"
  3: "Start Receiver"
  4: "Demo Running"
  5: "Monitor Status"
  6: "Cleanup"
  7: "Summary"

# Styling (CSS overrides)
primary_color: "#6B7D4F"    # Olive/sage green
background_color: "#FAFAFA"
card_background: "#FFFFFF"
text_primary: "#1A1A1A"
text_secondary: "#9CA3AF"

# Logging
log_level: "INFO"
max_log_lines: 100
```

---

## Implementation Steps

### Phase 1: Basic Dashboard (30 minutes)
1. ✅ Install Streamlit: `pip install streamlit`
2. ✅ Create `dashboard.py` with basic layout
3. ✅ Add session state initialization
4. ✅ Implement Load Balancer panel (UI only)
5. ✅ Implement Transmitter/Receiver panels (UI only)
6. ✅ Add status display

### Phase 2: Process Management (30 minutes)
7. ✅ Implement `start_transmitter()` subprocess logic
8. ✅ Implement `start_receiver()` subprocess logic
9. ✅ Implement `stop_transmitter()` and `stop_receiver()`
10. ✅ Add process monitoring and status updates
11. ✅ Implement log capture and display

### Phase 3: Load Balancer Integration (20 minutes)
12. ✅ Implement `reserve_load_balancer()` (with/without e2sar_py)
13. ✅ Implement `free_load_balancer()`
14. ✅ Add URI validation
15. ✅ Test LB reservation flow

### Phase 4: Slides Integration (30 minutes)
16. ✅ Create `demo_slides.md` with Marp
17. ✅ Generate HTML: `marp slides/demo_slides.md -o slides/demo_slides.html --html`
18. ✅ Embed slides in Streamlit (iframe or native markdown)
19. ✅ Implement navigation controls
20. ✅ Synchronize slides with demo steps

### Phase 5: Styling & Polish (20 minutes)
21. ✅ Apply custom CSS (match reference design)
22. ✅ Add icons and visual indicators
23. ✅ Test responsiveness
24. ✅ Add error handling and validation
25. ✅ Load configuration from YAML

### Phase 6: Testing & Documentation (20 minutes)
26. ✅ End-to-end testing
27. ✅ Create README for dashboard usage
28. ✅ Add inline help text
29. ✅ Final polish and bug fixes

**Total Estimated Time:** ~2.5 hours

---

## Running the Dashboard

```bash
# Navigate to dashboard directory
cd demos/fm_bluesky

# Install dependencies (one-time)
pip install streamlit pyyaml

# Optional: Install Marp CLI for slide generation
npm install -g @marp-team/marp-cli
marp slides/demo_slides.md -o slides/demo_slides.html --html

# Run dashboard
streamlit run dashboard.py

# Dashboard will open in browser at http://localhost:8501
```

---

## Advantages of Streamlit Approach

### vs PyQt5
- **~80% less code** (100 lines vs 500+)
- **No UI file compilation** (no .ui files or QtDesigner)
- **Automatic styling** (modern by default)
- **Easier debugging** (Python-only, no signals/slots)
- **Hot reload** (changes reflect immediately)

### vs Jupyter Notebook
- **Professional UI** (not notebook-style)
- **Better for demos** (single-page app vs cells)
- **Easy deployment** (can share URL)
- **Cleaner state management** (session_state vs globals)

### vs Flask/FastAPI
- **No HTML/CSS/JS** (pure Python)
- **Faster development** (built-in components)
- **Reactive by design** (automatic re-renders)

---

## Next Steps After Implementation

1. **Add real E2SAR LB API calls** (once e2sar_py is available)
2. **Add XML-RPC control** for frequency tuning from dashboard
3. **Add real-time metrics** (data rate, packet loss, latency)
4. **Add visualization** (spectrum waterfall, constellation diagram)
5. **Add multi-user support** (for classroom demos)
6. **Package as Docker container** (for easy deployment)

---

## References

- **Streamlit Docs:** https://docs.streamlit.io/
- **Marp Docs:** https://marp.app/
- **E2SAR GitHub:** https://github.com/JeffersonLab/E2SAR
- **GNU Radio Wiki:** https://wiki.gnuradio.org/

---

**Status:** Plan complete, ready for implementation
**Estimated LOC:** ~150 Python + ~100 Markdown (slides)
**Complexity:** Low (thanks to Streamlit!)
