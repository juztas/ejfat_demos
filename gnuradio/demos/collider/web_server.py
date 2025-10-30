#!/usr/bin/env python3
"""
Simple HTTP server to serve the collider control web interface
"""

import http.server
import socketserver
import os

PORT = 8001
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Add CORS headers to allow cross-origin requests
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print("=" * 60)
        print("Particle Collider Web Interface Server")
        print("=" * 60)
        print(f"\nServing at: http://localhost:{PORT}")
        print(f"Open in browser: http://localhost:{PORT}/collider_control.html")
        print("\nMake sure the particle collider simulation is running!")
        print("Press Ctrl+C to stop the server.")
        print("=" * 60 + "\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped.")
