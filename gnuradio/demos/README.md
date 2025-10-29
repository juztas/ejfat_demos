# EJFAT GNU Radio Demos

This directory contains demonstration flowgraphs for EJFAT (EIC JLAB Fast Aggregated Transmission) integration with GNU Radio.

## Demo Directories

### 🔬 E2SAR Test Suite

**Location:** `e2sar_test/`

Complete test suite for E2SAR (Experiment to Software Analysis in Realtime) segmenter and reassembler blocks.

**Quick start:**
```bash
cd e2sar_test
./check_e2sar_config.sh  # Verify configuration
./test_e2sar_simple.py    # Run loopback test
```

**Documentation:** See `e2sar_test/README.md` or `e2sar_test/E2SAR_INDEX.md`

---

### 📡 EJFAT Blocks Test

**Location:** `ejfat_blocks_test/`

General EJFAT block testing - validates all EJFAT blocks (source, sink, SHM) with random data.

**Quick start:**
```bash
cd ejfat_blocks_test
gnuradio-companion ejfat_blocks_test.grc
```

**Documentation:** See `ejfat_blocks_test/README.md`

---

### 📻 FM Radio Demos

**Location:** `fm/`

Interactive FM radio receiver and transmitter flowgraphs using RTL-SDR.

**Quick start:**
```bash
cd fm
gnuradio-companion fm_receiver.grc
```

**Documentation:** See `fm/README.md`

---

### 🤖 FM Bluesky Automated Tests

**Location:** `fm_bluesky/`

Automated FM radio testing with Bluesky integration - scans Ottawa FM stations automatically.

**Quick start:**
```bash
cd fm_bluesky
./run_ottawa_fm_quick_test.py
```

**Documentation:** See `fm_bluesky/README.md`

---

### 🎛️ Widget Control Demos

**Location:** `widget/`

GNU Radio widget control via Bluesky - demonstrates remote control of flowgraphs.

**Quick start:**
```bash
cd widget
./run_bluesky_demo.py
```

**Documentation:** See `widget/README_BLUESKY.md`

---

### 🔧 Full System Integration

**Location:** `full_system/`

Production-ready Bluesky experiment framework for controlled experiments with GNU Radio and EJFAT.

**Features:**
- Ophyd devices for hardware abstraction (GNU Radio via XML-RPC, mock devices)
- Custom scan plans (frequency scans, characterization, adaptive scans, 2D grids)
- Live callbacks for real-time feedback and data processing
- Persistent data storage via DataBroker with full metadata capture
- Analysis and visualization tools with multiple export formats (CSV, HDF5, Excel, JSON)

**Quick start (no hardware required):**
```bash
cd full_system
python scripts/cli/run_experiment.py mock_experiment
python scripts/data_access/access_my_data.py
```

**With GNU Radio:**
```bash
# Terminal 1: Start GNU Radio flowgraph
cd widget && python sine_wave_demo.py

# Terminal 2: Run experiment
cd ../full_system
python scripts/cli/run_experiment.py frequency_characterization
```

**Key utilities:**
```bash
python scripts/cli/run_experiment.py list              # List experiments
python scripts/data_access/retrieve_data.py --list     # View saved data
python scripts/testing/test_all_experiments.py --all   # Run tests
```

**Documentation:**
- Complete guide: `full_system/README.md`
- Tutorial: `full_system/docs/tutorial/TUTORIAL_RUNNING_EXPERIMENTS.md`
- Quick reference: `full_system/docs/user/QUICK_REFERENCE.md`
- Data analysis: `full_system/docs/user/DATA_RETRIEVAL_AND_ANALYSIS_GUIDE.md`

---

### 🎨 Custom Blocks & Presentations

**Locations:**
- `custom/` - Custom flowgraphs and API documentation
- `slides/` - Presentation materials

## Getting Started

### 1. Activate Environment

```bash
conda activate gnuradio
```

### 2. Choose Your Demo

**For E2SAR testing (recommended first test):**
```bash
cd e2sar_test
./test_e2sar_simple.py
```

**For Bluesky experiments (no hardware required):**
```bash
cd full_system
python scripts/cli/run_experiment.py mock_experiment
python scripts/data_access/access_my_data.py
```

**For FM radio:**
```bash
cd fm
gnuradio-companion fm_receiver.grc
```

**For general EJFAT blocks:**
```bash
cd ejfat_blocks_test
gnuradio-companion ejfat_blocks_test.grc
```

**For automated FM scanning:**
```bash
cd fm_bluesky
./run_ottawa_fm_quick_test.py
```

**For widget/parameter control:**
```bash
cd widget
./run_bluesky_demo.py
```

## Prerequisites

- GNU Radio environment installed (see `../CLAUDE.md`)
- E2SAR Python bindings (for E2SAR demos)
- gr-ejfat module installed
- RTL-SDR or other hardware (for FM demos)

## Demo Organization

```
demos/
├── README.md (this file)
├── DIRECTORY_STRUCTURE.md     # Detailed directory guide
│
├── e2sar_test/                # E2SAR segmenter/reassembler tests
│   ├── README.md              # Quick start
│   ├── E2SAR_INDEX.md         # Master index
│   ├── test_e2sar_simple.py   # Loopback test
│   └── test_e2sar_loopback.grc
│
├── ejfat_blocks_test/         # General EJFAT block tests
│   ├── README.md
│   ├── ejfat_blocks_test.grc
│   └── ejfat_blocks_test.py
│
├── fm/                        # FM radio demos
│   ├── README.md
│   ├── fm_receiver.grc
│   └── fm_transmitter.grc
│
├── fm_bluesky/                # Automated FM testing
│   ├── README.md
│   ├── run_ottawa_fm_test.py
│   └── run_ottawa_fm_quick_test.py
│
├── widget/                    # Widget control demos
│   ├── README_BLUESKY.md
│   ├── sine_wave_demo.grc
│   └── test_freq_change.py
│
├── full_system/               # Full system integration
│   └── README.md
│
├── custom/                    # Custom blocks & API docs
└── slides/                    # Presentations
```

## Documentation

- **E2SAR Tests:** `e2sar_test/E2SAR_INDEX.md` - Complete guide
- **EJFAT Blocks:** `ejfat_blocks_test/README.md` - Block testing
- **FM Demos:** `fm/RDS_README.md` - FM and RDS information
- **FM Automation:** `fm_bluesky/FM_BLUESKY_README.md` - Automated testing
- **Widget Control:** `widget/README_BLUESKY.md` - Remote control
- **Full System:** `full_system/README.md` - Complete integration
- **Build System:** `../CLAUDE.md` - Environment setup
- **Directory Guide:** `DIRECTORY_STRUCTURE.md` - Detailed organization

## Quick Reference

### E2SAR Loopback Test
```bash
cd e2sar_test && ./test_e2sar_simple.py
```

### EJFAT Blocks Test
```bash
cd ejfat_blocks_test && gnuradio-companion ejfat_blocks_test.grc
```

### FM Radio Receiver
```bash
cd fm && gnuradio-companion fm_receiver.grc
```

### Automated FM Scan
```bash
cd fm_bluesky && ./run_ottawa_fm_quick_test.py
```

### Widget Control Demo
```bash
cd widget && ./run_bluesky_demo.py
```

### Full System Experiments
```bash
cd full_system
python scripts/cli/run_experiment.py mock_experiment        # No hardware test
python scripts/data_access/access_my_data.py                # View latest data
python scripts/data_access/retrieve_data.py --list          # List all runs
```

## Support

For issues:
1. Check demo-specific README files in each directory
2. See troubleshooting sections in documentation
3. Verify environment: `conda list | grep gnuradio`
4. Check E2SAR: `python -c "import e2sar_py; print('OK')"`
5. Check gr-ejfat: `python -c "from gnuradio import ejfat; print('OK')"`

## See Also

- Main documentation: `../README.md`
- Environment setup: `../CLAUDE.md`
- gr-ejfat blocks: `../gr-ejfat/`
- E2SAR repository: https://github.com/JeffersonLab/E2SAR
- GNU Radio: https://www.gnuradio.org/
