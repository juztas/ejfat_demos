#!/usr/bin/env python3
"""
Simple HTTP server to serve FM scan browser and provide scan directory listings.
"""

import os
import glob
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import mimetypes

class ScanServerHandler(SimpleHTTPRequestHandler):
    """Extended HTTP handler that can list available scans."""

    def do_HEAD(self):
        """Handle HEAD requests (same as GET but without body)."""
        self.do_GET()

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)

        # API endpoint to list scans
        if parsed_path.path == '/api/scans':
            self.handle_list_scans()
        # API endpoint to get scan data
        elif parsed_path.path.startswith('/api/scan/'):
            self.handle_get_scan(parsed_path.path)
        # API endpoint to serve audio files
        elif parsed_path.path.startswith('/api/audio/'):
            self.handle_get_audio(parsed_path.path)
        # Serve static files
        else:
            super().do_GET()

    def handle_list_scans(self):
        """List all available scan directories."""
        try:
            # Find all fm_scan_* directories
            scan_dirs = glob.glob('fm_scan_*/')

            scans = []
            for scan_dir in sorted(scan_dirs, reverse=True):
                # Find msgpack files in the directory
                msgpack_files = glob.glob(os.path.join(scan_dir, '*.msgpack'))

                if msgpack_files:
                    # Get directory info
                    dir_name = scan_dir.rstrip('/')
                    mtime = os.path.getmtime(scan_dir)

                    scans.append({
                        'directory': dir_name,
                        'files': [os.path.basename(f) for f in msgpack_files],
                        'timestamp': mtime,
                        'file_count': len(msgpack_files)
                    })

            # Send JSON response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(scans).encode())

        except Exception as e:
            self.send_error(500, f"Error listing scans: {e}")

    def handle_get_scan(self, path):
        """Serve a specific scan file, converting msgpack to JSON."""
        try:
            import msgpack

            # Extract scan directory and filename from path
            # Format: /api/scan/fm_scan_YYYYMMDD_HHMMSS/filename.msgpack
            parts = path.split('/')
            if len(parts) >= 5:
                scan_dir = parts[3]
                filename = parts[4]
                filepath = os.path.join(scan_dir, filename)

                if os.path.exists(filepath) and filepath.endswith('.msgpack'):
                    # Read and parse msgpack file
                    documents = []
                    with open(filepath, 'rb') as f:
                        unpacker = msgpack.Unpacker(f, raw=False)
                        for doc in unpacker:
                            documents.append(doc)

                    # Convert to JSON
                    content = json.dumps(documents).encode()

                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', len(content))
                    self.end_headers()
                    self.wfile.write(content)
                else:
                    self.send_error(404, "Scan file not found")
            else:
                self.send_error(400, "Invalid scan path")

        except Exception as e:
            self.send_error(500, f"Error serving scan: {e}")

    def handle_get_audio(self, path):
        """Serve audio files from scan directories with HTTP range support."""
        try:
            # Extract scan directory and audio filename from path
            # Format: /api/audio/fm_scan_YYYYMMDD_HHMMSS/audio/filename.wav
            parts = path.split('/')
            if len(parts) >= 6:
                scan_dir = parts[3]
                # parts[4] should be 'audio'
                audio_filename = parts[5]
                audio_path = os.path.join(scan_dir, 'audio', audio_filename)

                if os.path.exists(audio_path) and audio_path.endswith('.wav'):
                    # Get file size
                    file_size = os.path.getsize(audio_path)

                    # Check for Range header (for seeking/buffering)
                    range_header = self.headers.get('Range')

                    if range_header:
                        # Parse range header (format: "bytes=start-end")
                        byte_range = range_header.replace('bytes=', '').split('-')
                        start = int(byte_range[0]) if byte_range[0] else 0
                        end = int(byte_range[1]) if byte_range[1] else file_size - 1

                        # Ensure valid range
                        start = max(0, min(start, file_size - 1))
                        end = max(start, min(end, file_size - 1))
                        length = end - start + 1

                        # Send partial content
                        self.send_response(206)  # Partial Content
                        self.send_header('Content-Type', 'audio/wav')
                        self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                        self.send_header('Content-Length', str(length))
                        self.send_header('Accept-Ranges', 'bytes')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()

                        # Send the requested byte range (skip for HEAD requests)
                        if self.command != 'HEAD':
                            with open(audio_path, 'rb') as f:
                                f.seek(start)
                                self.wfile.write(f.read(length))
                    else:
                        # Send entire file
                        self.send_response(200)
                        self.send_header('Content-Type', 'audio/wav')
                        self.send_header('Content-Length', str(file_size))
                        self.send_header('Accept-Ranges', 'bytes')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()

                        # Stream the file in chunks to avoid loading entire file into memory
                        # Skip body for HEAD requests
                        if self.command != 'HEAD':
                            with open(audio_path, 'rb') as f:
                                chunk_size = 64 * 1024  # 64KB chunks
                                while True:
                                    chunk = f.read(chunk_size)
                                    if not chunk:
                                        break
                                    self.wfile.write(chunk)
                else:
                    self.send_error(404, "Audio file not found")
            else:
                self.send_error(400, "Invalid audio path")

        except Exception as e:
            self.send_error(500, f"Error serving audio: {e}")

    def end_headers(self):
        """Add CORS headers to all responses."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()


def run_server(port=8000):
    """Run the HTTP server."""
    server_address = ('', port)
    httpd = HTTPServer(server_address, ScanServerHandler)

    print("=" * 70)
    print("FM Scan Browser Server")
    print("=" * 70)
    print(f"Server running at: http://localhost:{port}/")
    print(f"Open browser at:   http://localhost:{port}/fm_scan_browser.html")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 70)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='FM Scan Browser Server')
    parser.add_argument('--port', type=int, default=8000,
                       help='Port to run server on (default: 8000)')

    args = parser.parse_args()

    # Change to the script's directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    run_server(args.port)
