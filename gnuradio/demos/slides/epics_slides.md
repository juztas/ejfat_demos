---
marp: true
theme: default
paginate: true
---

# Does EPICS Provide DSP Composition?

**Short answer: No**

EPICS DAQ (Experimental Physics and Industrial Control System) does not provide DSP composition like GNU Radio.

---

## 🧩 EPICS: Control, not Composition

EPICS is primarily a **control and data acquisition framework** designed for:

- Managing devices (magnets, beamline components, detectors)
- Acquiring process variables (voltages, temperatures, counts)
- Providing distributed control via Channel Access or PVAccess
- Orchestrating data flow and state machines through IOCs

---

## What EPICS is NOT designed for

EPICS doesn't provide signal processing blocks like:

- FFTs
- Filters
- Mixers
- Decimators
- Modulators

These are handled by DSP frameworks:
- GNU Radio
- LabVIEW DSP toolkit
- Simulink DSP blocks

---

## 🧠 Where DSP fits in practice

In a typical setup:

**EPICS** → Controls and monitors a DSP system

**Actual DSP** → Handled by:
- Custom FPGA firmware
- External DAQ software (XDAQ, MIDAS, custom C++)
- GPU or CPU-based real-time processing nodes

EPICS exposes processed results or control knobs as process variables.

---

## ⚙️ Integration Possibilities

To integrate DSP with EPICS:

1. Use **StreamDevice** or **asynDriver** to interface with external DSP
2. Wrap a **GNU Radio flowgraph** and publish via pvAccess
3. Use **pvaPy** or **EPICS7's pvDataCPP** to bridge DSP streams

**EPICS acts as the supervisor — not the signal chef.**

---

# areaDetector for Signal Processing

areaDetector is a modular EPICS framework for handling array data.

**Key insight**: It doesn't care what's inside arrays — photons, voltages, FFT bins, or any numeric data!

---

## 🎥 What areaDetector provides

- Standard **plugin architecture** for data processing
- **Data flow model** with NDArray objects (multi-dimensional arrays)
- Support for **hardware drivers** and **software filters**

**In essence**: areaDetector is a stream processing pipeline.

---

## 🧩 Typical Processing Chain

| Stage | Plugin | Function |
|-------|--------|----------|
| Input | NDPluginDriver | Acquire raw waveform data |
| Filtering | NDPluginProcess | Arithmetic, offsets, averaging |
| Transform | NDPluginFFT | Compute FFTs or power spectra |
| Analysis | NDPluginStats | Extract mean, variance, centroid |
| Thresholding | NDPluginROI | Define regions of interest |
| Output | NDPluginStdArrays | Stream via EPICS PVs or save to disk |

---

## ⚙️ Adapting areaDetector for DSP

1. **Use NDArray as your "signal packet"**
   - 1×N arrays for time-domain data
   - 2×N for complex IQ pairs

2. **Write a custom driver**
   - Pull data from digitiser, SDR, FPGA, or simulator

3. **Use or extend existing plugins**
   - NDPluginFFT, NDPluginProcess, NDPluginStats

---

## Example: Spectrum Analyser

Build a reconfigurable spectrum analyser:

1. Custom ADDriver reads 1,024-sample frames → NDArrays
2. NDPluginFFT produces amplitude spectra
3. NDPluginStats extracts peak frequency
4. NDPluginOverlay highlights dominant peaks
5. Results displayed in viewer and available as PVs

---

## 🪄 Why this approach is powerful

- **Zero-copy data flow** between plugins
- **Metadata (NDAttributes)** travels with data
- **Reconfigure pipelines at runtime** — add/remove plugins dynamically
- **Native integration** with EPICS PVs, GUIs, and archivers

---

## 🧩 Caveats

- **Not real-time DSP** — soft real-time; latency depends on scheduling
- Throughput fine for **MHz-range** data, not GHz-class radio streams
- Complex DSP often needs **custom plugin code** or **GPU acceleration**

---

# pvaPy and DSP Pipelines

**pvaPy** = Python interface to EPICS PVAccess

Opens a powerful back door for building/extending signal processing pipelines.

---

## 🧩 What pvaPy provides

- Create, publish, and subscribe to EPICS PVAccess (PVA) data streams
- Access **NTNDArray** (areaDetector-style array structures)
- Embed **Python code** inside EPICS data flow

**Think of it as**: Pythonic glue layer for EPICS7 and areaDetector

---

## 🧠 Why pvaPy enables DSP

| Component | Role | Example |
|-----------|------|---------|
| areaDetector | Source of data | Camera, digitiser, waveform |
| PVAccess network | Transport layer | Transmits NDArrays |
| pvaPy | Python endpoint | Receives as NumPy arrays |
| Python DSP library | Processing engine | NumPy, SciPy, CuPy, PyTorch |
| pvaPy (again) | Publisher | Pushes processed result back |

---

## Processing Chain Example

```
ADC → areaDetector → PVAccess → pvaPy DSP → PVAccess → GUI/Archiver
```

**pvaPy acts as a programmable DSP node inside the EPICS network.**

---

## Example: Real-Time FFT in pvaPy

```python
from pvaccess import *
import numpy as np

def process(pv):
    data = pv['value']
    samples = np.array(data, dtype=np.float32)
    spectrum = np.abs(np.fft.fft(samples))
    print("Peak frequency bin:", np.argmax(spectrum))

channel = Channel('MY:WAVEFORM')
channel.subscribe(process)
channel.startMonitor()
```

---

## 🧮 pvaPy as DSP "Glue Layer"

Insert pvaPy anywhere in your data chain:

- Between FPGA digitiser and areaDetector
- Between NDPluginFFT and downstream consumers
- As standalone analysis service:
  - Subscribe to waveform PV
  - Perform Python-based DSP
  - Publish new PVs (e.g., "Dominant frequency", "RMS noise")

---

## 🚀 Advantages of pvaPy for DSP

- 🧠 **Python ecosystem access** — SciPy, NumPy, TensorFlow, PyTorch, CuPy
- ⚡ **Rapid prototyping** — add features without recompiling IOCs
- 🧩 **EPICS-native interoperability** — seamless publish/subscribe
- 🌐 **Scalability** — distribute DSP tasks across networked nodes
- 👀 **Visibility** — monitor intermediate results as EPICS PVs

---

## 🧨 Limitations

- Python means **soft real-time**, not deterministic low-latency
- Best for **analysis or secondary processing**, not core control loops
- Heavy DSP may require **GPU offloading** (CuPy, Numba)
- For "radio-style" DSP composition, integrate **GNU Radio** with EPICS

---

## pvaPy Pipeline Architecture

```
┌─────────────┐     ┌──────────┐     ┌─────────────┐
│ areaDetector│────▶│ PVAccess │────▶│ pvaPy DSP   │
│   Source    │     │ Network  │     │  Processor  │
└─────────────┘     └──────────┘     └─────────────┘
                                            │
                                            ▼
┌─────────────┐     ┌──────────┐     ┌─────────────┐
│  Control    │◀────│ PVAccess │◀────│  pvaPy      │
│    GUI      │     │ Network  │     │  Publisher  │
└─────────────┘     └──────────┘     └─────────────┘
```

---

# Visual Composition of pvaPy Pipelines

**Question**: Is there a visual way to compose pvaPy pipelines?

**Short answer**: No standard visual composer exists (like GNU Radio Companion), but it's possible to build one.

---

## ✅ What currently exists

- Streaming frameworks built on pvaPy (discussed in literature)
- People build pipelines in **code**, not via visual composer
- areaDetector plugin chains can be understood visually, but not edited graphically

---

## ⚠️ Challenges for Visual Composer

- **Dynamic structure** — pipelines may not have rigid graph structure
- **Heterogeneous operations** — Python, compiled libraries, I/O operations
- **State & side effects** — filters with memory, buffers, accumulations
- **Latency, threading, scheduling** — execution order and timing matter
- **EPICS integration** — nodes interact with PVs, metadata, network

---

## 🛠 How to Build Visual Composer

1. **Represent pipeline as graph** of nodes and edges
2. **Associate each node** with Python function or class
3. **Use GUI framework** for drag/drop (Qt, web-based)
4. **Backend**: instantiate graph in pvaPy
5. **Live editing** — add/remove nodes on the fly
6. **Monitoring** — embedded plots, throughput indicators

---

## 🧪 Minimal Prototype Idea

Using Python + Jupyter:

- Use **ipywidgets** and **ipycanvas** for visual node placement
- Represent nodes as objects with `process(input_data) → output_data`
- Convert visual structure to chain of pvaPy Channel monitors
- Use **matplotlib** or **bqplot** for intermediate signal plots

Not industrial-grade, but good for experimentation!

---

## ✅ Summary

- **No mature visual composer** for pvaPy pipelines exists publicly
- Streaming pipelines do exist, typically expressed in **code**
- **Building a visual composer is feasible** using GUI/web frameworks
- Would need to handle dynamic wiring, state, scheduling, and EPICS integration

**pvaPy turns EPICS from a control system into a programmable, Python-driven signal processing network.**
