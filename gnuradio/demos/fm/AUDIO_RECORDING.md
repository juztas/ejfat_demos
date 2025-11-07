# FM Station Scanner with Audio Recording

## Overview

The enhanced FM station scanner (`scan_and_record_audio.py`) extends the original digital detection scanner to also record audio snippets from each station. The audio files are stored alongside the Bluesky experiment documents and can be played back through the web browser.

## How It Works

### Audio Recording Process

1. **FM Receiver**: You must have an FM receiver running that continuously writes audio to a WAV file (e.g., `fm_transceiver.wav`)

2. **Scanner**: The scanner script:
   - Connects to the digital detector's XML-RPC server (port 8080)
   - For each station:
     - Tunes the detector to the frequency
     - Waits for the dwell time (default: 10 seconds)
     - Reads the digital indicator and signal level
     - Copies the current audio from the receiver's WAV file
     - Saves it with a unique filename in the scan's audio directory
     - Records all data in Bluesky documents with references to the audio files

3. **Storage Structure**:
   ```
   fm_scan_YYYYMMDD_HHMMSS/
   ├── audio/
   │   ├── 88.5MHz_CKCU-FM.wav
   │   ├── 89.9MHz_CIHT-FM_(Hot_89.9).wav
   │   ├── 90.7MHz_CFFX-FM_(Move_90.7).wav
   │   └── ...
   └── <uid>.msgpack          # Bluesky documents with audio file references
   ```

### Browser Integration

The scan browser has been enhanced to:
- Display an "Audio" column in the station table
- Show HTML5 audio players for each station that has recorded audio
- Serve audio files through the scan server's `/api/audio/` endpoint

## Usage

### Running a Scan with Audio Recording

```bash
# First, start the FM receiver (continuously writing audio to fm_transceiver.wav)
python fm_receiver_e2sar.py &

# Wait for it to start...
sleep 5

# Then start the digital detector
python fm_digital_detector_e2sar.py &

# Wait for it to start...
sleep 5

# Run the scan with audio recording
python scan_and_record_audio.py --dwell 10 --audio-source fm_transceiver.wav
```

### Command Line Options

```
--dwell SECONDS           Dwell time per frequency (default: 10)
--audio-duration SECONDS  Audio recording duration per station (default: 5)
--detector-host HOST      Digital detector XML-RPC server hostname (default: localhost)
--detector-port PORT      Digital detector XML-RPC server port (default: 8080)
--audio-source PATH       Path to live audio WAV file (default: fm_transceiver.wav)
--no-record              Disable data recording (default: recording enabled)
```

### Viewing Results

```bash
# Start the scan browser server
python scan_server.py

# Open browser
open http://localhost:8000/fm_scan_browser.html
```

The browser will:
1. Automatically discover all `fm_scan_*` directories
2. Load the scan data from msgpack files
3. Display the Audio column with playback controls
4. Allow you to listen to the recorded audio for each station

## Data Schema

The Bluesky documents include a new `audio_file` field:

```python
{
    'frequency': 88.5,              # MHz
    'signal_level': -25.3,          # dB
    'digital_detected': False,      # Boolean
    'station_name': 'CKCU-FM',      # String
    'station_format': 'Campus/Community',
    'station_location': 'Ottawa',
    'audio_file': '88.5MHz_CKCU-FM.wav'  # Filename (external reference)
}
```

The `audio_file` field is marked as `'external': 'FILESTORE:'` in the data schema, indicating it's a reference to an external file rather than embedded data.

## Technical Details

### Audio File Naming

Audio files are named using the format:
```
{frequency}MHz_{station_name}.wav
```

Special characters in station names are sanitized:
- Spaces become underscores
- Slashes become hyphens

Examples:
- `88.5MHz_CKCU-FM.wav`
- `89.9MHz_CIHT-FM_(Hot_89.9).wav`
- `101.1MHz_CIBO-FM_(CBC_Radio_One).wav`

### Server API

The scan server provides three endpoints:

1. **`GET /api/scans`**: List all available scan directories
2. **`GET /api/scan/{directory}/{file}.msgpack`**: Get scan data (converted to JSON)
3. **`GET /api/audio/{directory}/audio/{file}.wav`**: Serve audio file

### Browser Features

- **Audio Players**: HTML5 `<audio>` elements with controls
- **Compact UI**: Small audio controls (30px height) to fit in table rows
- **Conditional Display**: Shows "N/A" if no audio file is available
- **CORS Support**: Server includes proper CORS headers for cross-origin access

## Limitations

1. **Live Audio Requirement**: The FM receiver must be running and continuously writing to a WAV file
2. **Snapshot Recording**: Only captures the audio that's in the file at the moment of copying (not a time-aligned recording)
3. **Storage**: Each scan can generate 20+ WAV files (~100KB each), ensure sufficient disk space
4. **Synchronization**: There's a slight delay between tuning and audio recording

## Future Enhancements

Potential improvements:
1. Add XML-RPC control to the FM receiver to dynamically set the output filename
2. Implement time-aligned recording (record exactly during the dwell period)
3. Add audio compression options (MP3, Opus)
4. Include audio spectrograms in the browser
5. Add audio analysis metrics (SNR, modulation detection)
