#!/usr/bin/env python3
"""
Extract individual station audio clips from the accumulated WAV file.

This script reads the timestamps from a scan's Bluesky documents and extracts
the corresponding audio segments from the long accumulated WAV file that the
FM receiver was writing to during the scan.
"""

import wave
import argparse
import os
import msgpack
from pathlib import Path


def extract_audio_segments(scan_dir, source_wav, audio_duration=5):
    """
    Extract audio segments for each station from the accumulated WAV file.

    Parameters
    ----------
    scan_dir : str
        Path to the scan directory containing the msgpack file
    source_wav : str
        Path to the accumulated WAV file
    audio_duration : float
        Duration of audio to extract per station (seconds)
    """
    # Find the msgpack file in the scan directory
    msgpack_files = list(Path(scan_dir).glob('*.msgpack'))
    if not msgpack_files:
        print(f"No msgpack files found in {scan_dir}")
        return

    msgpack_file = msgpack_files[0]
    print(f"Reading scan data from: {msgpack_file}")

    # Read the scan documents
    with open(msgpack_file, 'rb') as f:
        unpacker = msgpack.Unpacker(f, raw=False)
        documents = list(unpacker)

    # Extract start time and events
    start_doc = None
    events = []

    for doc in documents:
        doc_type, doc_data = doc
        if doc_type == 'start':
            start_doc = doc_data
        elif doc_type == 'event':
            events.append(doc_data)

    if not start_doc:
        print("No start document found")
        return

    scan_start_time = start_doc['time']
    print(f"Scan started at: {scan_start_time}")
    print(f"Found {len(events)} station events")

    # Open source WAV file
    print(f"\nOpening source WAV file: {source_wav}")
    with wave.open(source_wav, 'rb') as source:
        params = source.getparams()
        framerate = params.framerate
        nchannels = params.nchannels
        total_frames = source.getnframes()
        total_duration = total_frames / framerate

        print(f"  Sample rate: {framerate} Hz")
        print(f"  Channels: {nchannels}")
        print(f"  Total duration: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")
        print(f"  Total frames: {total_frames:,}")

        # Create audio directory
        audio_dir = os.path.join(scan_dir, 'audio')
        os.makedirs(audio_dir, exist_ok=True)

        # Extract audio for each event
        print(f"\nExtracting {audio_duration} second clips...")
        for i, event in enumerate(events, 1):
            # Calculate time offset from scan start
            event_time = event['timestamps']['frequency']
            time_offset = event_time - scan_start_time

            # Calculate frame position in the WAV file
            start_frame = int(time_offset * framerate)
            frames_to_extract = int(audio_duration * framerate)

            # Make sure we don't read past the end
            if start_frame + frames_to_extract > total_frames:
                frames_to_extract = total_frames - start_frame

            if start_frame < 0 or start_frame >= total_frames:
                print(f"  [{i:2d}] {event['data']['frequency']:.1f} MHz - Skipping (time offset {time_offset:.1f}s out of range)")
                continue

            # Read the audio data
            source.setpos(start_frame)
            audio_data = source.readframes(frames_to_extract)

            # Create output filename
            station_name = event['data']['station_name'].replace('/', '-').replace(' ', '_')
            audio_filename = f"{event['data']['frequency']:.1f}MHz_{station_name}.wav"
            audio_path = os.path.join(audio_dir, audio_filename)

            # Write extracted audio
            with wave.open(audio_path, 'wb') as dest:
                dest.setparams(params)
                dest.writeframes(audio_data)

            print(f"  [{i:2d}] {event['data']['frequency']:.1f} MHz - {station_name:40s} @ {time_offset:6.1f}s → {audio_filename}")

    print(f"\nExtracted {len(events)} audio clips to: {audio_dir}/")


def main():
    parser = argparse.ArgumentParser(
        description='Extract station audio clips from accumulated WAV file'
    )
    parser.add_argument('scan_dir', help='Scan directory (e.g., fm_scan_20251102_011249)')
    parser.add_argument('source_wav', help='Source WAV file (e.g., fm_e2sar.wav)')
    parser.add_argument('--duration', type=float, default=5,
                       help='Audio duration per station in seconds (default: 5)')

    args = parser.parse_args()

    extract_audio_segments(args.scan_dir, args.source_wav, args.duration)


if __name__ == '__main__':
    main()
