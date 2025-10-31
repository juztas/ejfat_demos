# DAQ Run Browser

A web-based point-and-click interface for browsing and analyzing particle collider DAQ runs from the streaming data acquisition system.

## Features

- 📊 **Run Inventory**: Automatic discovery and indexing of all DAQ runs
- 📈 **Interactive Visualizations**: Real-time charts for detector data
- 🔍 **Detailed Statistics**: Comprehensive run summaries with metrics
- 📁 **Raw Data Access**: View detector data directly in the browser
- 🔄 **Live Updates**: Refresh inventory to see new runs
- 🎨 **Modern UI**: Clean, responsive interface with tabbed views

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Web Browser (port 8080)                                     │
│  - run_browser.html (UI)                                     │
│  - JavaScript (logic, charts, API calls)                     │
│  - Chart.js (visualizations)                                 │
└───────────────────┬──────────────────────────────────────────┘
                    │
                    │ HTTP/JSON API
                    ▼
┌──────────────────────────────────────────────────────────────┐
│  Python Backend Server (run_browser_server.py)               │
│  - RunInventory: Scans data directory for runs               │
│  - RunBrowserHandler: REST API endpoints                     │
│  - pandas: Data analysis and statistics                      │
└───────────────────┬──────────────────────────────────────────┘
                    │
                    │ File I/O
                    ▼
┌──────────────────────────────────────────────────────────────┐
│  Data Files (CSV format)                                     │
│  - pixel_detector_<run_id>.csv                               │
│  - calorimeter_detector_<run_id>.csv                         │
└──────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Start the Server

```bash
# Start server pointing to your data directory
python run_browser_server.py --data-dir ./test_streaming_data --port 8080
```

Output:
```
============================================================
Run Browser Server
============================================================
Data directory: /path/to/test_streaming_data
Runs found: 2

Server running at: http://localhost:8080
Web UI: http://localhost:8080/run_browser.html

API Endpoints:
  GET /api/runs - List all runs
  GET /api/run/<run_id> - Get run info
  GET /api/run/<run_id>/summary - Get detailed summary
  GET /api/run/<run_id>/data?detector=pixel&limit=100 - Get data
  GET /api/refresh - Refresh run inventory

Press Ctrl+C to stop
============================================================
```

### 2. Open Web UI

Navigate to: **http://localhost:8080/run_browser.html**

### 3. Browse Runs

- **Left sidebar**: List of all runs sorted by date (newest first)
- **Click a run**: View detailed information and visualizations
- **Tabs**:
  - **Overview**: Run summary with combined statistics
  - **Pixel Detector**: Pixel-specific data and hit distribution
  - **Calorimeter**: Calorimeter-specific data, speed/angle distributions
  - **Raw Data**: Load and view raw CSV data (first 50 rows)

## REST API

### List All Runs

```bash
GET /api/runs
```

**Response:**
```json
[
  {
    "run_id": "e4f9b894",
    "pixel_file": "/path/to/pixel_detector_e4f9b894.csv",
    "calorimeter_file": "/path/to/calorimeter_detector_e4f9b894.csv",
    "pixel_file_name": "pixel_detector_e4f9b894.csv",
    "calorimeter_file_name": "calorimeter_detector_e4f9b894.csv",
    "created": "2025-10-30T19:32:43.816661",
    "size_pixel": 189,
    "size_calorimeter": 293
  }
]
```

### Get Run Information

```bash
GET /api/run/<run_id>
```

**Response:** Basic run metadata (same as single entry from `/api/runs`)

### Get Run Summary with Statistics

```bash
GET /api/run/<run_id>/summary
```

**Response:**
```json
{
  "run_id": "e4f9b894",
  "created": "2025-10-30T19:32:43.816661",
  "pixel_file": "...",
  "calorimeter_file": "...",
  "pixel_stats": {
    "total_hits": 123,
    "unique_particles": 45,
    "pixel_range": [100, 5900],
    "time_range": [0.5, 10.2],
    "duration": 9.7,
    "hit_distribution": [2, 3, 5, ...] // 64 bins
  },
  "calorimeter_stats": {
    "total_hits": 123,
    "unique_particles": 45,
    "segment_range": [0, 63],
    "speed_range": [0.3, 1.2],
    "angle_range": [-135.0, 135.0],
    "time_range": [0.8, 10.5],
    "duration": 9.7,
    "hit_distribution": [1, 2, 4, ...], // 64 bins
    "speed_histogram": {
      "counts": [5, 10, 15, ...],
      "bins": [0.3, 0.35, 0.4, ...]
    },
    "angle_histogram": {
      "counts": [3, 8, 12, ...],
      "bins": [-135, -120, -105, ...]
    }
  }
}
```

### Get Raw Data

```bash
GET /api/run/<run_id>/data?detector=<pixel|calorimeter>&limit=<num>
```

**Parameters:**
- `detector`: Either "pixel" or "calorimeter"
- `limit`: Maximum number of rows to return (optional)

**Response:**
```json
[
  {
    "wall_time": 1761867163.023459,
    "simulation_time": 28.050000000000264,
    "particle_id": 34,
    "pixel_number": 5242,
    "hit_time": 28.050000000000264
  },
  ...
]
```

### Refresh Inventory

```bash
GET /api/refresh
```

**Response:**
```json
{
  "status": "success",
  "runs": 2
}
```

## UI Features

### Run List (Sidebar)

- **Sorted by date**: Newest runs at top
- **Run ID**: Short identifier for the run
- **Creation time**: When the run was created
- **File size**: Combined size of pixel and calorimeter files
- **Click to select**: Loads full run details

### Run Details (Main Panel)

#### Header Section
- Run ID and creation timestamp
- File names for pixel and calorimeter detectors

#### Statistics Cards
- **Pixel Hits**: Total number of pixel detector hits
- **Calorimeter Hits**: Total number of calorimeter hits
- **Unique Particles**: Number of distinct particles detected
- **Duration**: How long the run lasted (seconds)

#### Overview Tab
- Combined summary of both detectors
- Bar chart showing hit distribution across 64 bins
- Both pixel (blue) and calorimeter (purple) overlaid

#### Pixel Detector Tab
- Detailed pixel statistics
- Pixel hit distribution chart (64 bins)
- Shows which regions of the detector were most active

#### Calorimeter Tab
- Detailed calorimeter statistics
- **Segment Hit Distribution**: Which calorimeter segments saw hits
- **Particle Speed Distribution**: Histogram of particle speeds
- **Deflection Angle Distribution**: Histogram of deflection angles

#### Raw Data Tab
- Load pixel or calorimeter data (first 50 rows)
- Displays in tabular format with all columns
- Useful for spot-checking data quality

## Visualizations

All charts are interactive (powered by Chart.js):

- **Hover**: See exact values
- **Responsive**: Resize with browser window
- **Color-coded**:
  - Pixel: Blue (rgb(102, 126, 234))
  - Calorimeter: Purple (rgb(118, 75, 162))
  - Speed: Red (rgb(255, 99, 132))
  - Angle: Teal (rgb(75, 192, 192))

## Command-Line Options

```bash
python run_browser_server.py [OPTIONS]

Options:
  --data-dir, -d <path>   Data directory (default: current directory)
  --port, -p <number>     Port to run server on (default: 8080)

Examples:
  # Use default settings (current directory, port 8080)
  python run_browser_server.py

  # Specify data directory
  python run_browser_server.py --data-dir ./experiment_data

  # Use different port
  python run_browser_server.py --port 9000

  # Both options
  python run_browser_server.py -d ./data -p 9000
```

## Data Directory Structure

The run browser expects this file structure:

```
data_directory/
├── pixel_detector_<run_id>.csv
├── calorimeter_detector_<run_id>.csv
├── pixel_detector_<run_id2>.csv
├── calorimeter_detector_<run_id2>.csv
└── ...
```

**Requirements:**
- Files must be named `pixel_detector_*.csv` and `calorimeter_detector_*.csv`
- Each run must have both a pixel and calorimeter file
- Run IDs are extracted from filenames

## Statistics Computed

### Pixel Detector

| Metric | Description |
|--------|-------------|
| Total Hits | Total number of pixel hits |
| Unique Particles | Number of distinct particle IDs |
| Pixel Range | Min and max pixel numbers hit |
| Time Range | Start and end times (simulation time) |
| Duration | Total run duration in seconds |
| Hit Distribution | Histogram of hits across 64 bins |

### Calorimeter

| Metric | Description |
|--------|-------------|
| Total Hits | Total number of calorimeter hits |
| Unique Particles | Number of distinct particle IDs |
| Segment Range | Min and max segment numbers hit |
| Speed Range | Min and max particle speeds |
| Angle Range | Min and max deflection angles |
| Time Range | Start and end times (simulation time) |
| Duration | Total run duration in seconds |
| Hit Distribution | Histogram of hits across 64 segments |
| Speed Histogram | Distribution of particle speeds (20 bins) |
| Angle Histogram | Distribution of deflection angles (20 bins) |

## Integration with Streaming DAQ

The run browser works seamlessly with the streaming DAQ system:

1. **Run experiment** with `StreamingColliderDevice`
2. **DAQ files created** automatically with unique run IDs
3. **Browser detects** new files when you click "Refresh"
4. **View results** immediately after run completes

### Example Workflow

```bash
# Terminal 1: Start run browser
python run_browser_server.py --data-dir ./experiment_data

# Terminal 2: Run Bluesky experiment
python bluesky_streaming_examples.py

# Browser: Click "Refresh" to see new runs
```

## Troubleshooting

### "No runs found"

**Cause:** Data directory is empty or files don't match expected pattern

**Solution:**
- Check data directory path is correct
- Ensure files are named `pixel_detector_*.csv` and `calorimeter_detector_*.csv`
- Verify both pixel and calorimeter files exist for each run

### "Error loading run details"

**Cause:** CSV files are corrupted or have unexpected format

**Solution:**
- Check CSV files have proper headers
- Ensure no missing or malformed data
- Verify files weren't modified after creation

### Server won't start (port in use)

**Cause:** Another process using port 8080

**Solution:**
```bash
# Use different port
python run_browser_server.py --port 9000

# Or kill process on port 8080
lsof -ti:8080 | xargs kill
```

### Charts not rendering

**Cause:** Chart.js not loading from CDN

**Solution:**
- Check internet connection
- Verify browser console for errors
- Try refreshing the page

## Performance

- **Inventory scan**: Fast (milliseconds for hundreds of runs)
- **Run summary**: Computes statistics on-demand (sub-second for typical runs)
- **Raw data loading**: Limited to 50 rows by default to prevent browser slowdown
- **Charts**: Render instantly using Chart.js

**Scalability:**
- Tested with 100+ runs
- File sizes up to 10MB per detector
- Handles 1000+ detector hits without issues

## Browser Compatibility

Tested and working on:
- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)

**Requirements:**
- Modern browser with ES6 support
- JavaScript enabled
- Internet connection (for Chart.js CDN)

## Files

| File | Purpose |
|------|---------|
| `run_browser_server.py` | Python backend server with REST API |
| `run_browser.html` | Web-based UI with JavaScript and visualizations |
| `RUN_BROWSER_README.md` | This documentation |

## Future Enhancements

Potential additions:
- [ ] Search and filter runs by date/criteria
- [ ] Export charts as PNG/SVG
- [ ] Download processed data as CSV
- [ ] Compare multiple runs side-by-side
- [ ] Real-time monitoring (auto-refresh)
- [ ] Authentication for multi-user access
- [ ] Database backend for faster queries
- [ ] Integration with Databroker

## Related Documentation

- `STREAMING_DAQ_README.md`: Streaming DAQ system overview
- `BLUESKY_README.md`: Basic Bluesky integration
- `CLAUDE.md`: Project-level documentation
