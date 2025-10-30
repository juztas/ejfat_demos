#!/usr/bin/env python3
"""
Particle Collider Simulation

Models a particle collider with:
- Target at origin with radius 1
- Particles injected from (-1, 0) at random intervals (0.5-1.0s)
- Deflection proportional to particle speed
- Random deflection angles between -270 and 270 degrees
- Particle speeds randomized between 0.5 and 1.0
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Circle
from matplotlib.widgets import Slider, Button, RangeSlider
from collections import deque
import time
import csv
import json
from datetime import datetime
import os
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import threading

# DAQ system
from calorimeter_daq import CalorimeterDAQ


class Particle:
    """Represents a single particle in the collider"""

    def __init__(self, speed, injection_time, particle_id):
        self.particle_id = particle_id
        self.position = np.array([-1.0, 0.0])  # Start at (-1, 0)
        self.speed = speed
        self.velocity = np.array([speed, 0.0])  # Initially moving toward center
        self.deflected = False
        self.active = True
        self.trail = deque(maxlen=50)  # Store position history for trail

        # Data collection fields
        self.injection_time = injection_time
        self.deflection_time = None
        self.deflection_angle = None
        self.deflection_position = None
        self.exit_time = None

        # Pixel detector detection
        self.pixel_radius = 1.8  # Center of pixel detector (between 1.7 and 1.9)
        self.hit_pixel = False
        self.pixel_hit_time = None
        self.pixel_number = None  # Which pixel (0-6399) was hit

        # Calorimeter detection
        self.calorimeter_radius = 2.15  # Center of calorimeter (between 2.0 and 2.3)
        self.hit_calorimeter = False
        self.calorimeter_hit_time = None
        self.calorimeter_segment = None  # Which segment (0-127) was hit
        self.fade_duration = 0.2  # Fade out over 0.2 seconds
        self.alpha = 1.0  # Transparency (1.0 = opaque, 0.0 = transparent)

    def update(self, dt, current_time):
        """Update particle position and check for deflection"""
        if not self.active:
            return

        # Handle fading after hitting calorimeter
        if self.hit_calorimeter:
            time_since_hit = current_time - self.calorimeter_hit_time
            if time_since_hit >= self.fade_duration:
                # Fade complete, deactivate particle
                self.active = False
                self.exit_time = current_time
                self.alpha = 0.0
                return
            else:
                # Update alpha for fading (linear fade from 1.0 to 0.0)
                self.alpha = 1.0 - (time_since_hit / self.fade_duration)
            return  # Don't move particle while fading

        # Store current position in trail
        self.trail.append(self.position.copy())

        # Update position
        self.position += self.velocity * dt

        # Check if particle reached the origin (center)
        distance = np.linalg.norm(self.position)

        # Deflect when particle reaches very close to origin (0, 0)
        if distance <= 0.05 and not self.deflected:
            # Snap to origin and deflect
            self.position = np.array([0.0, 0.0])
            self.deflect(current_time)

        # Check if particle reached the pixel detector (after deflection)
        if self.deflected and not self.hit_pixel and distance >= self.pixel_radius:
            # Calculate which pixel was hit (100 pixels per calorimeter segment)
            angle_rad = np.arctan2(self.position[1], self.position[0])
            angle_deg = np.degrees(angle_rad)

            # Map angle from [-135°, 135°] to pixel [0, 6399]
            # Total pixels: 64 segments * 100 pixels/segment = 6400 pixels
            if -135 <= angle_deg <= 135:
                # Normalize to [0, 270]
                normalized_angle = angle_deg + 135
                # Map to pixel [0, 6399]
                self.pixel_number = int(normalized_angle / 270 * 6400)
                # Ensure in bounds
                self.pixel_number = max(0, min(6399, self.pixel_number))
                self.hit_pixel = True
                self.pixel_hit_time = current_time

        # Check if particle reached the calorimeter (after deflection)
        if self.deflected and distance >= self.calorimeter_radius:
            # Stop at calorimeter center and start fading
            # Normalize position to exact calorimeter radius
            direction = self.position / distance
            self.position = direction * self.calorimeter_radius

            # Calculate which calorimeter segment was hit
            angle_rad = np.arctan2(self.position[1], self.position[0])
            angle_deg = np.degrees(angle_rad)

            # Map angle from [-135°, 135°] to segment [0, 63]
            # Calorimeter spans from -135° to 135° (270° total)
            if -135 <= angle_deg <= 135:
                # Normalize to [0, 270]
                normalized_angle = angle_deg + 135
                # Map to segment [0, 63]
                self.calorimeter_segment = int(normalized_angle / 270 * 64)
                # Ensure in bounds
                self.calorimeter_segment = max(0, min(63, self.calorimeter_segment))

            self.hit_calorimeter = True
            self.calorimeter_hit_time = current_time
            self.velocity = np.array([0.0, 0.0])  # Stop moving

        # Deactivate if particle somehow goes too far (failsafe)
        if distance > 3.0:
            if self.active:
                self.exit_time = current_time
            self.active = False

    def deflect(self, current_time):
        """Deflect particle at random angle proportional to speed"""
        self.deflected = True
        self.deflection_time = current_time
        self.deflection_position = self.position.copy()

        # Random deflection angle from 135° clockwise to -135°
        # This covers the right half of the circle
        angle_degrees = np.random.uniform(-135, 135)
        angle = angle_degrees * np.pi / 180.0
        self.deflection_angle = angle_degrees

        # Deflection magnitude proportional to speed
        deflection_speed = self.speed * 1.5  # Amplify for visibility

        # Set new velocity based on deflection angle
        self.velocity = np.array([
            deflection_speed * np.cos(angle),
            deflection_speed * np.sin(angle)
        ])

    def get_data(self):
        """Return particle data as dictionary for logging"""
        return {
            'particle_id': self.particle_id,
            'speed': self.speed,
            'injection_time': self.injection_time,
            'deflection_time': self.deflection_time,
            'deflection_angle': self.deflection_angle,
            'deflection_position_x': self.deflection_position[0] if self.deflection_position is not None else None,
            'deflection_position_y': self.deflection_position[1] if self.deflection_position is not None else None,
            'exit_time': self.exit_time,
            'lifetime': self.exit_time - self.injection_time if self.exit_time else None
        }


class DataLogger:
    """Handles data collection and logging to files"""

    def __init__(self, base_filename=None):
        if base_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"collider_data_{timestamp}"

        self.base_filename = base_filename
        self.csv_filename = f"{base_filename}.csv"
        self.json_filename = f"{base_filename}.json"
        self.summary_filename = f"{base_filename}_summary.txt"

        self.particle_data = []
        self.start_time = datetime.now()

        # Initialize CSV file
        self._init_csv()

        print(f"Data logging to: {self.csv_filename}")

    def _init_csv(self):
        """Initialize CSV file with headers"""
        with open(self.csv_filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'particle_id', 'speed', 'injection_time', 'deflection_time',
                'deflection_angle', 'deflection_position_x', 'deflection_position_y',
                'exit_time', 'lifetime'
            ])

    def log_particle(self, particle):
        """Log a completed particle's data"""
        data = particle.get_data()
        self.particle_data.append(data)

        # Append to CSV
        with open(self.csv_filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                data['particle_id'], data['speed'], data['injection_time'],
                data['deflection_time'], data['deflection_angle'],
                data['deflection_position_x'], data['deflection_position_y'],
                data['exit_time'], data['lifetime']
            ])

    def save_summary(self, collider):
        """Save simulation summary statistics"""
        if not self.particle_data:
            return

        speeds = [p['speed'] for p in self.particle_data]
        angles = [p['deflection_angle'] for p in self.particle_data if p['deflection_angle'] is not None]
        lifetimes = [p['lifetime'] for p in self.particle_data if p['lifetime'] is not None]

        summary = {
            'simulation_start': self.start_time.isoformat(),
            'simulation_end': datetime.now().isoformat(),
            'total_particles': len(self.particle_data),
            'total_time': collider.time_elapsed,
            'statistics': {
                'speed': {
                    'mean': float(np.mean(speeds)),
                    'std': float(np.std(speeds)),
                    'min': float(np.min(speeds)),
                    'max': float(np.max(speeds))
                },
                'deflection_angle': {
                    'mean': float(np.mean(angles)) if angles else None,
                    'std': float(np.std(angles)) if angles else None,
                    'min': float(np.min(angles)) if angles else None,
                    'max': float(np.max(angles)) if angles else None
                },
                'lifetime': {
                    'mean': float(np.mean(lifetimes)) if lifetimes else None,
                    'std': float(np.std(lifetimes)) if lifetimes else None,
                    'min': float(np.min(lifetimes)) if lifetimes else None,
                    'max': float(np.max(lifetimes)) if lifetimes else None
                }
            },
            'parameters': {
                'speed_min': collider.speed_min,
                'speed_max': collider.speed_max,
                'interval_min': collider.interval_min,
                'interval_max': collider.interval_max
            }
        }

        # Save JSON
        with open(self.json_filename, 'w') as f:
            json.dump(summary, f, indent=2)

        # Save text summary
        with open(self.summary_filename, 'w') as f:
            f.write("Particle Collider Simulation Summary\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Simulation Start: {summary['simulation_start']}\n")
            f.write(f"Simulation End: {summary['simulation_end']}\n")
            f.write(f"Total Time: {summary['total_time']:.2f} seconds\n")
            f.write(f"Total Particles: {summary['total_particles']}\n\n")

            f.write("Speed Statistics:\n")
            f.write(f"  Mean: {summary['statistics']['speed']['mean']:.3f}\n")
            f.write(f"  Std:  {summary['statistics']['speed']['std']:.3f}\n")
            f.write(f"  Min:  {summary['statistics']['speed']['min']:.3f}\n")
            f.write(f"  Max:  {summary['statistics']['speed']['max']:.3f}\n\n")

            if angles:
                f.write("Deflection Angle Statistics (degrees):\n")
                f.write(f"  Mean: {summary['statistics']['deflection_angle']['mean']:.2f}\n")
                f.write(f"  Std:  {summary['statistics']['deflection_angle']['std']:.2f}\n")
                f.write(f"  Min:  {summary['statistics']['deflection_angle']['min']:.2f}\n")
                f.write(f"  Max:  {summary['statistics']['deflection_angle']['max']:.2f}\n\n")

            if lifetimes:
                f.write("Particle Lifetime Statistics (seconds):\n")
                f.write(f"  Mean: {summary['statistics']['lifetime']['mean']:.3f}\n")
                f.write(f"  Std:  {summary['statistics']['lifetime']['std']:.3f}\n")
                f.write(f"  Min:  {summary['statistics']['lifetime']['min']:.3f}\n")
                f.write(f"  Max:  {summary['statistics']['lifetime']['max']:.3f}\n")

        print(f"\nSimulation summary saved to:")
        print(f"  CSV: {self.csv_filename}")
        print(f"  JSON: {self.json_filename}")
        print(f"  Summary: {self.summary_filename}")


class ParticleCollider:
    """Main collider simulation"""

    def __init__(self, data_logger=None):
        self.target_radius = 1.0
        self.particles = []
        self.time_elapsed = 0
        self.particle_count = 0
        self.data_logger = data_logger
        self.paused = False

        # Configurable parameters (must be set before calling _random_interval)
        self.speed_min = 0.5
        self.speed_max = 1.0
        self.interval_min = 0.5
        self.interval_max = 1.0

        # Initialize injection timing
        self.last_injection_time = 0
        self.next_injection_interval = self._random_interval()

        # Calorimeter segmentation: 64 segments from -135° to 135°
        self.num_calorimeter_segments = 64
        self.calorimeter_counts = np.zeros(self.num_calorimeter_segments, dtype=int)

        # Pixel detector tracking
        self.recent_pixel_hits = deque(maxlen=5)  # Keep last 5 pixel hits

        # Initialize Calorimeter DAQ
        self.calorimeter_daq = CalorimeterDAQ(
            sample_rate=10000,
            num_channels=self.num_calorimeter_segments,
            buffer_duration=10.0,
            noise_floor_db=-80,
            filter_cutoff_fraction=0.1
        )

    def _random_interval(self):
        """Generate random injection interval"""
        return np.random.uniform(self.interval_min, self.interval_max)

    def _random_speed(self):
        """Generate random particle speed"""
        return np.random.uniform(self.speed_min, self.speed_max)

    def inject_particle(self):
        """Inject a new particle into the collider"""
        speed = self._random_speed()
        particle = Particle(speed, self.time_elapsed, self.particle_count + 1)
        self.particles.append(particle)
        self.particle_count += 1
        print(f"Injected particle #{self.particle_count} with speed {speed:.2f}")

    def update(self, dt):
        """Update all particles and handle injections"""
        if self.paused:
            return

        self.time_elapsed += dt

        # Check if it's time to inject a new particle
        if self.time_elapsed - self.last_injection_time >= self.next_injection_interval:
            self.inject_particle()
            self.last_injection_time = self.time_elapsed
            self.next_injection_interval = self._random_interval()

        # Update all active particles
        for particle in self.particles:
            was_not_hit_calorimeter = not particle.hit_calorimeter
            was_not_hit_pixel = not particle.hit_pixel
            particle.update(dt, self.time_elapsed)

            # Check if particle just hit the pixel detector
            if particle.hit_pixel and was_not_hit_pixel and particle.pixel_number is not None:
                # Record the pixel hit
                self.recent_pixel_hits.append({
                    'pixel': particle.pixel_number,
                    'time': particle.pixel_hit_time,
                    'particle_id': particle.particle_id
                })

            # Check if particle just hit the calorimeter
            if particle.hit_calorimeter and was_not_hit_calorimeter and particle.calorimeter_segment is not None:
                # Increment the count for this segment
                self.calorimeter_counts[particle.calorimeter_segment] += 1

                # Inject pulse into DAQ
                # Amplitude proportional to particle speed
                self.calorimeter_daq.inject_pulse(
                    channel=particle.calorimeter_segment,
                    time=particle.calorimeter_hit_time,
                    amplitude=particle.speed
                )

        # Log and remove inactive particles (keep last 20 for visualization)
        active_particles = [p for p in self.particles if p.active]
        inactive_particles = [p for p in self.particles if not p.active]

        # Log newly inactive particles
        if self.data_logger:
            logged_particles = [p for p in inactive_particles if p.exit_time is not None]
            for particle in logged_particles:
                if particle.exit_time is not None and particle not in getattr(self, '_logged_particles', set()):
                    self.data_logger.log_particle(particle)
                    if not hasattr(self, '_logged_particles'):
                        self._logged_particles = set()
                    self._logged_particles.add(particle)

        # Keep only recent inactive particles
        if len(inactive_particles) > 20:
            inactive_particles = inactive_particles[-20:]

        self.particles = active_particles + inactive_particles

        # Update DAQ
        self.calorimeter_daq.update(dt)

    def reset(self):
        """Reset the simulation"""
        self.particles = []
        self.time_elapsed = 0
        self.particle_count = 0
        self.last_injection_time = 0
        self.next_injection_interval = self._random_interval()
        self.calorimeter_counts = np.zeros(self.num_calorimeter_segments, dtype=int)
        self.recent_pixel_hits.clear()
        if hasattr(self, '_logged_particles'):
            self._logged_particles.clear()
        self.calorimeter_daq.reset()
        print("Simulation reset")


class CORSXMLRPCRequestHandler(SimpleXMLRPCRequestHandler):
    """Custom XML-RPC request handler with CORS support for browser access"""

    def end_headers(self):
        # Add CORS headers to allow browser access
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        """Handle preflight OPTIONS request"""
        self.send_response(200)
        self.end_headers()


class ColliderRPCServer:
    """XML-RPC server for remote control of the collider"""

    def __init__(self, collider, visualizer=None, host='localhost', port=8000):
        self.collider = collider
        self.visualizer = visualizer
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None

    def start(self):
        """Start the XML-RPC server in a separate thread"""
        self.server = SimpleXMLRPCServer(
            (self.host, self.port),
            requestHandler=CORSXMLRPCRequestHandler,
            allow_none=True,
            logRequests=False
        )

        # Register functions
        self.server.register_function(self.set_speed_min, 'set_speed_min')
        self.server.register_function(self.set_speed_max, 'set_speed_max')
        self.server.register_function(self.set_interval_min, 'set_interval_min')
        self.server.register_function(self.set_interval_max, 'set_interval_max')
        self.server.register_function(self.pause, 'pause')
        self.server.register_function(self.resume, 'resume')
        self.server.register_function(self.reset, 'reset')
        self.server.register_function(self.get_status, 'get_status')
        self.server.register_function(self.get_statistics, 'get_statistics')

        # Start server in background thread
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()

        print(f"XML-RPC server started on http://{self.host}:{self.port}")
        print(f"Web interface available at: http://{self.host}:{self.port + 1}/collider_control.html")

    def stop(self):
        """Stop the XML-RPC server"""
        if self.server:
            self.server.shutdown()
            print("XML-RPC server stopped")

    # RPC Methods
    def set_speed_min(self, value):
        """Set minimum particle speed"""
        if 0.1 <= value <= 1.0 and value < self.collider.speed_max:
            self.collider.speed_min = value
            print(f"[XML-RPC] Set speed_min = {value:.2f}")
            # Update range slider if visualizer is available (without triggering callback)
            if self.visualizer and hasattr(self.visualizer, 'slider_speed_range'):
                slider = self.visualizer.slider_speed_range
                slider.eventson = False  # Disable events temporarily
                slider.set_val((value, self.collider.speed_max))
                slider.eventson = True   # Re-enable events
                # Mark slider for redraw (animation loop will handle it)
                if hasattr(self.visualizer, 'fig'):
                    # Note: Can't call flush_events() from background thread on macOS
                    # The animation loop will redraw on next frame
                    pass
            return {"success": True, "value": value}
        return {"success": False, "error": "Invalid value"}

    def set_speed_max(self, value):
        """Set maximum particle speed"""
        if 0.1 <= value <= 1.5 and value > self.collider.speed_min:
            self.collider.speed_max = value
            # Update range slider if visualizer is available (without triggering callback)
            if self.visualizer and hasattr(self.visualizer, 'slider_speed_range'):
                slider = self.visualizer.slider_speed_range
                slider.eventson = False  # Disable events temporarily
                slider.set_val((self.collider.speed_min, value))
                slider.eventson = True   # Re-enable events
                # Mark slider for redraw (animation loop will handle it)
                if hasattr(self.visualizer, 'fig'):
                    # Note: Can't call flush_events() from background thread on macOS
                    # The animation loop will redraw on next frame
                    pass
            return {"success": True, "value": value}
        return {"success": False, "error": "Invalid value"}

    def set_interval_min(self, value):
        """Set minimum injection interval"""
        if 0.1 <= value <= 2.0 and value < self.collider.interval_max:
            self.collider.interval_min = value
            # Update range slider if visualizer is available (without triggering callback)
            if self.visualizer and hasattr(self.visualizer, 'slider_interval_range'):
                slider = self.visualizer.slider_interval_range
                slider.eventson = False  # Disable events temporarily
                slider.set_val((value, self.collider.interval_max))
                slider.eventson = True   # Re-enable events
                # Mark slider for redraw (animation loop will handle it)
                if hasattr(self.visualizer, 'fig'):
                    # Note: Can't call flush_events() from background thread on macOS
                    # The animation loop will redraw on next frame
                    pass
            return {"success": True, "value": value}
        return {"success": False, "error": "Invalid value"}

    def set_interval_max(self, value):
        """Set maximum injection interval"""
        if 0.1 <= value <= 2.0 and value > self.collider.interval_min:
            self.collider.interval_max = value
            # Update range slider if visualizer is available (without triggering callback)
            if self.visualizer and hasattr(self.visualizer, 'slider_interval_range'):
                slider = self.visualizer.slider_interval_range
                slider.eventson = False  # Disable events temporarily
                slider.set_val((self.collider.interval_min, value))
                slider.eventson = True   # Re-enable events
                # Mark slider for redraw (animation loop will handle it)
                if hasattr(self.visualizer, 'fig'):
                    # Note: Can't call flush_events() from background thread on macOS
                    # The animation loop will redraw on next frame
                    pass
            return {"success": True, "value": value}
        return {"success": False, "error": "Invalid value"}

    def pause(self):
        """Pause the simulation"""
        self.collider.paused = True
        # Update button if visualizer is available
        if self.visualizer and hasattr(self.visualizer, 'button_pause'):
            self.visualizer.button_pause.label.set_text('Resume')
            # Mark button for redraw (animation loop will handle it)
            if hasattr(self.visualizer, 'fig'):
                # Note: Can't call flush_events() from background thread on macOS
                pass
        return {"success": True, "paused": True}

    def resume(self):
        """Resume the simulation"""
        self.collider.paused = False
        # Update button if visualizer is available
        if self.visualizer and hasattr(self.visualizer, 'button_pause'):
            self.visualizer.button_pause.label.set_text('Pause')
            # Mark button for redraw (animation loop will handle it)
            if hasattr(self.visualizer, 'fig'):
                # Note: Can't call flush_events() from background thread on macOS
                pass
        return {"success": True, "paused": False}

    def reset(self):
        """Reset the simulation"""
        self.collider.reset()
        return {"success": True}

    def get_status(self):
        """Get current simulation status"""
        active_count = sum(1 for p in self.collider.particles if p.active)
        return {
            "time_elapsed": self.collider.time_elapsed,
            "particle_count": self.collider.particle_count,
            "active_particles": active_count,
            "paused": self.collider.paused,
            "speed_min": self.collider.speed_min,
            "speed_max": self.collider.speed_max,
            "interval_min": self.collider.interval_min,
            "interval_max": self.collider.interval_max
        }

    def get_statistics(self):
        """Get simulation statistics"""
        if not self.collider.particles:
            return {"error": "No particles yet"}

        speeds = [p.speed for p in self.collider.particles if hasattr(p, 'speed')]
        deflection_angles = [p.deflection_angle for p in self.collider.particles
                            if hasattr(p, 'deflection_angle') and p.deflection_angle is not None]

        stats = {
            "total_particles": self.collider.particle_count,
            "current_particles": len(self.collider.particles)
        }

        if speeds:
            stats["speed"] = {
                "mean": float(np.mean(speeds)),
                "min": float(np.min(speeds)),
                "max": float(np.max(speeds))
            }

        if deflection_angles:
            stats["deflection_angle"] = {
                "mean": float(np.mean(deflection_angles)),
                "min": float(np.min(deflection_angles)),
                "max": float(np.max(deflection_angles))
            }

        return stats


class ColliderVisualizer:
    """Handles visualization of the collider"""

    def __init__(self, collider):
        self.collider = collider
        self.fig = plt.figure(figsize=(14, 10))

        # Create bar chart area (calorimeter histogram) - leftmost
        self.ax_hist = plt.axes([0.02, 0.30, 0.13, 0.65])

        # Create main plot area (collider visualization) - center
        self.ax = plt.axes([0.20, 0.30, 0.50, 0.65])

        # Create DAQ waterfall display area - rightmost
        self.ax_daq = plt.axes([0.75, 0.30, 0.22, 0.65])

        self.setup_plot()
        self.setup_histogram()
        self.setup_daq_display()
        self.setup_controls()

        # Create separate figure for sparklines (oscilloscope traces)
        self.fig_sparklines = plt.figure(figsize=(16, 12))
        self.fig_sparklines.suptitle('Calorimeter DAQ Channels (0-63)', fontsize=14)
        self.setup_sparklines()

    def setup_plot(self):
        """Setup the plot area"""
        self.ax.set_xlim(-2.5, 2.5)  # Centered view
        self.ax.set_ylim(-2.5, 2.5)
        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlabel('X Position')
        self.ax.set_ylabel('Y Position')
        self.ax.set_title('Particle Collider Simulation')

        # Draw deflection angle range from origin (0,0)
        # Particles scatter from 135° clockwise to -135° (right half of circle)
        angle_min = -135  # degrees (lower left)
        angle_max = 135   # degrees (upper left)

        # Draw wedge showing deflection range
        from matplotlib.patches import Wedge, Arc
        # Wedge from -135° to 135° (counter-clockwise) covers the right half
        total_deflection_angle = angle_max - angle_min  # 270 degrees
        wedge = Wedge((0, 0), 2.0, angle_min, angle_max,
                     facecolor='pink', alpha=0.2, edgecolor='red',
                     linewidth=2, linestyle='--', label=f'Deflection Range ({total_deflection_angle}°)')
        self.ax.add_patch(wedge)

        # Draw calorimeter (light green semi-circle around the perimeter)
        calorimeter_inner_radius = 2.0
        calorimeter_outer_radius = 2.3

        # Draw pixel detector (yellow semi-circle 0.1 unit inside calorimeter)
        pixel_outer_radius = calorimeter_inner_radius - 0.1  # 1.9
        pixel_inner_radius = pixel_outer_radius - 0.2  # 1.7
        pixel_wedge = Wedge((0, 0), pixel_outer_radius, angle_min, angle_max,
                           width=pixel_outer_radius - pixel_inner_radius,
                           facecolor='yellow', alpha=0.3, edgecolor='orange',
                           linewidth=2, label='Pixel Detector')
        self.ax.add_patch(pixel_wedge)
        calorimeter_wedge = Wedge((0, 0), calorimeter_outer_radius, angle_min, angle_max,
                                 width=calorimeter_outer_radius - calorimeter_inner_radius,
                                 facecolor='lightgreen', alpha=0.3, edgecolor='green',
                                 linewidth=2, label='Calorimeter (64 segments)')
        self.ax.add_patch(calorimeter_wedge)

        # Draw segment boundaries in the calorimeter
        num_segments = 64
        segment_angle_size = 270 / num_segments  # degrees per segment

        for i in range(num_segments + 1):
            # Calculate angle for this segment boundary
            # Segments span from -135° to +135°
            segment_angle_deg = -135 + (i * segment_angle_size)
            segment_angle_rad = np.deg2rad(segment_angle_deg)

            # Draw line from inner to outer radius
            x_inner = calorimeter_inner_radius * np.cos(segment_angle_rad)
            y_inner = calorimeter_inner_radius * np.sin(segment_angle_rad)
            x_outer = calorimeter_outer_radius * np.cos(segment_angle_rad)
            y_outer = calorimeter_outer_radius * np.sin(segment_angle_rad)

            self.ax.plot([x_inner, x_outer], [y_inner, y_outer],
                        'green', linewidth=0.5, alpha=0.5)

        # Draw boundary lines for deflection range
        radius_line = 2.0
        # Upper boundary at 135°
        angle_upper_rad = np.deg2rad(135)
        x_upper = radius_line * np.cos(angle_upper_rad)
        y_upper = radius_line * np.sin(angle_upper_rad)
        self.ax.plot([0, x_upper], [0, y_upper], 'r-', linewidth=2, alpha=0.6)

        # Lower boundary at -135°
        angle_lower_rad = np.deg2rad(-135)
        x_lower = radius_line * np.cos(angle_lower_rad)
        y_lower = radius_line * np.sin(angle_lower_rad)
        self.ax.plot([0, x_lower], [0, y_lower], 'r-', linewidth=2, alpha=0.6)

        # Mark the origin as the scattering center
        self.ax.plot(0, 0, 'r+', markersize=15, markeredgewidth=2.5, label='Origin (0,0) - Scatter Point')

        # Draw small target circle at origin to show collision point
        target = Circle((0, 0), 0.1,
                       fill=True, facecolor='red', alpha=0.4, edgecolor='red', linewidth=2)
        self.ax.add_patch(target)

        # Draw injection point at (-1, 0)
        self.ax.plot(-1, 0, 'go', markersize=10)

        # Calorimeter centerline radius and pixel detector centerline radius
        calorimeter_centerline = 2.15
        pixel_centerline = 1.8

        # Add Calorimeter label at (1.75, 2) with line to calorimeter arc centerline
        cal_label_x, cal_label_y = 1.75, 2.0
        self.ax.text(cal_label_x, cal_label_y, 'Calorimeter', fontsize=10, color='green',
                    verticalalignment='bottom', horizontalalignment='left')
        # Calculate endpoint at calorimeter centerline radius
        cal_distance = np.sqrt(cal_label_x**2 + cal_label_y**2)
        cal_end_x = cal_label_x / cal_distance * calorimeter_centerline
        cal_end_y = cal_label_y / cal_distance * calorimeter_centerline
        self.ax.plot([cal_label_x, cal_end_x], [cal_label_y, cal_end_y], 'g-', linewidth=1, alpha=0.6)

        # Add Pixel Detector label at (-0.5, -1.2) with line to pixel detector arc centerline
        pix_label_x, pix_label_y = -0.5, -1.2
        self.ax.text(pix_label_x, pix_label_y, 'Pixel Detector', fontsize=10, color='orange',
                    verticalalignment='top', horizontalalignment='left')
        # Calculate endpoint at pixel detector centerline radius
        pix_distance = np.sqrt(pix_label_x**2 + pix_label_y**2)
        pix_end_x = pix_label_x / pix_distance * pixel_centerline
        pix_end_y = pix_label_y / pix_distance * pixel_centerline
        self.ax.plot([pix_label_x, pix_end_x], [pix_label_y, pix_end_y], 'orange', linewidth=1, alpha=0.6)

        # Initialize particle plots
        self.trail_lines = []
        self.particle_markers = []

    def setup_histogram(self):
        """Setup the calorimeter histogram"""
        from matplotlib.ticker import MaxNLocator

        self.ax_hist.set_xlabel('Hit Count')
        self.ax_hist.set_ylabel('Segment Number')
        self.ax_hist.set_title('Calorimeter Hits')
        self.ax_hist.grid(True, alpha=0.3, axis='x')

        # Initialize bar chart
        segments = np.arange(self.collider.num_calorimeter_segments)
        self.hist_bars = self.ax_hist.barh(segments, self.collider.calorimeter_counts,
                                           color='green', alpha=0.7, height=1.0)

        # Set y-axis limits and labels
        self.ax_hist.set_ylim(-1, self.collider.num_calorimeter_segments)
        self.ax_hist.invert_yaxis()  # Segment 0 at top

        # Only show some tick labels to avoid clutter
        tick_positions = [0, 16, 32, 48, 63]
        self.ax_hist.set_yticks(tick_positions)
        self.ax_hist.set_yticklabels(tick_positions)

        # Force x-axis to show only integer values
        self.ax_hist.xaxis.set_major_locator(MaxNLocator(integer=True))

    def setup_daq_display(self):
        """Setup DAQ waterfall display"""
        self.ax_daq.set_xlabel('Channel (0-63)')
        self.ax_daq.set_ylabel('Time (rows, 0.1s per row)')
        self.ax_daq.set_title('Calorimeter Events')

        # Create waterfall image plot
        # Start with zeros (will be updated from DAQ)
        waterfall_data = self.collider.calorimeter_daq.waterfall_buffer

        self.daq_image = self.ax_daq.imshow(
            waterfall_data,
            aspect='auto',
            cmap='viridis',
            interpolation='nearest',
            origin='lower',  # Bottom row = newest
            vmin=0.0,  # Fixed color scale minimum
            vmax=1.5,  # Fixed color scale maximum (saturates above this)
            extent=[0, 64, 0, 200]  # [left, right, bottom, top]
        )

        # Add colorbar
        from matplotlib.colorbar import Colorbar
        cbar = plt.colorbar(self.daq_image, ax=self.ax_daq, label='Amplitude')
        cbar.set_label('Amplitude (saturates at 1.5)', rotation=270, labelpad=20)

        # Set x-axis ticks to show channel numbers
        self.ax_daq.set_xticks([0, 16, 32, 48, 63])
        self.ax_daq.set_xticklabels(['0', '16', '32', '48', '63'])

        # Set y-axis limits
        self.ax_daq.set_ylim(0, 200)

    def setup_sparklines(self):
        """Setup 64-channel stacked oscilloscope display"""
        # Create single plot for all 64 traces
        # Leave space on left for vertical sliders
        self.ax_sparklines = self.fig_sparklines.add_axes([0.15, 0.08, 0.83, 0.88])

        # Create time axis for 1000 samples
        # In trigger mode: 1000 samples at 10 kHz = 100 ms
        # In free-running mode: 5 samples at 5 Hz = 1000 ms = 1 second
        self.sparkline_time = np.arange(1000) / 10000 * 1000  # milliseconds (for trigger mode)
        self.sparkline_time_freerun = np.arange(self.collider.calorimeter_daq.free_running_display_samples) * 200  # milliseconds (for free-running: 5 Hz = 200ms per sample)

        # Vertical spacing between traces
        self.trace_offset = 1.5

        # Initialize 64 traces with vertical offset
        self.sparkline_lines = []
        self.sparkline_trigger_lines = []

        for ch in range(64):
            # Vertical offset for this channel
            offset = ch * self.trace_offset

            # Plot initial empty trace at offset
            line, = self.ax_sparklines.plot(self.sparkline_time,
                                           np.zeros(1000) + offset,
                                           'g-', linewidth=0.5, alpha=0.8)
            self.sparkline_lines.append(line)

            # Add trigger level line for this channel
            trigger_line = self.ax_sparklines.axhline(
                offset + self.collider.calorimeter_daq.trigger_level,
                color='r', linestyle='--', linewidth=0.5, alpha=0.3
            )
            self.sparkline_trigger_lines.append(trigger_line)

            # Add channel label on left side
            self.ax_sparklines.text(-5, offset + 0.75, f'{ch}',
                                   fontsize=7, verticalalignment='center',
                                   color='black', fontweight='bold')

        # Initial time span (default to 1 second = 1000 ms)
        self.time_span = 1000.0  # milliseconds

        # Set axis limits
        label_offset = self.time_span * 0.02  # 2% of span for labels
        self.ax_sparklines.set_xlim(-label_offset, self.time_span)
        self.ax_sparklines.set_ylim(-1, 64 * self.trace_offset)

        # Labels
        self.ax_sparklines.set_xlabel('Time (ms)', fontsize=10)
        self.ax_sparklines.set_ylabel('Channel Number', fontsize=10)
        self.ax_sparklines.grid(True, alpha=0.2, axis='x')

        # Remove y-ticks (we have channel labels instead)
        self.ax_sparklines.set_yticks([])

        # Add mode toggle button (trigger vs free-running) - upper right corner, half width
        ax_mode_button = self.fig_sparklines.add_axes([0.88, 0.94, 0.05, 0.03])
        from matplotlib.widgets import Button
        self.button_scope_mode = Button(ax_mode_button, 'Trigger Mode', color='lightgoldenrodyellow', hovercolor='0.975')
        self.button_scope_mode.on_clicked(self.toggle_scope_mode)

        # Add vertical time span slider on left (range depends on mode: trigger 0.1-1000ms, free-running 100-60000ms)
        ax_timespan = self.fig_sparklines.add_axes([0.02, 0.15, 0.02, 0.70])
        self.slider_timespan = Slider(
            ax_timespan, 'Time\nSpan\n(ms)', 0.1, 1000.0,
            valinit=self.time_span,
            valstep=0.1,
            orientation='vertical'
        )
        self.slider_timespan.on_changed(self.update_timespan)
        self.slider_timespan_ax = ax_timespan  # Keep reference to recreate slider when mode changes

        # Add vertical trigger level slider on left
        ax_trigger = self.fig_sparklines.add_axes([0.08, 0.15, 0.02, 0.70])
        self.slider_trigger_level = Slider(
            ax_trigger, 'Trigger\nLevel', 0.0, 1.5,
            valinit=self.collider.calorimeter_daq.trigger_level,
            valstep=0.05,
            orientation='vertical'
        )
        self.slider_trigger_level.on_changed(self.update_trigger_level)

    def setup_controls(self):
        """Setup interactive controls"""
        # Control panel area
        control_color = 'lightgoldenrodyellow'

        # Vertical sliders between Hits and Collider plots
        slider_width = 0.02  # Slider thickness
        slider_height = 0.65  # Match plot height
        slider_bottom = 0.30  # Match plot bottom

        # Speed range slider (vertical, leftmost)
        ax_speed_range = plt.axes([0.16, slider_bottom, slider_width, slider_height])
        self.slider_speed_range = RangeSlider(
            ax_speed_range, 'Speed\nRange', 0.1, 1.5,
            valinit=(self.collider.speed_min, self.collider.speed_max),
            valstep=0.05,
            orientation='vertical'
        )
        self.slider_speed_range.on_changed(self.update_speed_range)

        # Interval range slider (vertical, rightmost before collider plot)
        ax_interval_range = plt.axes([0.19, slider_bottom, slider_width, slider_height])
        self.slider_interval_range = RangeSlider(
            ax_interval_range, 'Interval\nRange', 0.1, 2.0,
            valinit=(self.collider.interval_min, self.collider.interval_max),
            valstep=0.1,
            orientation='vertical'
        )
        self.slider_interval_range.on_changed(self.update_interval_range)

        # Buttons (horizontal row) - positioned below simulation plot, left of pixel detector
        button_height = 0.04
        button_width = 0.12
        button_y = 0.19  # Below simulation plot (0.30), above pixel detector (0.14)
        button_x_start = 0.20  # Aligned with left edge of simulation plot

        # Pause/Resume button
        ax_pause = plt.axes([button_x_start, button_y, button_width, button_height])
        self.button_pause = Button(ax_pause, 'Pause', color=control_color, hovercolor='0.975')
        self.button_pause.on_clicked(self.toggle_pause)

        # Reset button
        ax_reset = plt.axes([button_x_start + 0.14, button_y, button_width, button_height])
        self.button_reset = Button(ax_reset, 'Reset', color=control_color, hovercolor='0.975')
        self.button_reset.on_clicked(self.reset_simulation)

        # Save summary button (if data logger exists)
        if self.collider.data_logger:
            ax_save = plt.axes([button_x_start + 0.28, button_y, button_width, button_height])
            self.button_save = Button(ax_save, 'Save', color=control_color, hovercolor='0.975')
            self.button_save.on_clicked(self.save_summary)

        # Pixel detector hits textbox - right-aligned under Calorimeter Events
        from matplotlib.widgets import TextBox
        ax_pixel_text = plt.axes([0.75, 0.14, 0.22, 0.09])  # Match waterfall x position and width
        ax_pixel_text.axis('off')
        self.pixel_text = ax_pixel_text.text(
            0.05, 0.95, '',
            fontsize=11,  # Increased from 7 (1.5x for better readability)
            verticalalignment='top',
            horizontalalignment='left',
            transform=ax_pixel_text.transAxes,
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8)
        )

    def update_speed_range(self, val):
        """Update speed range (min and max)"""
        speed_min, speed_max = val
        self.collider.speed_min = speed_min
        self.collider.speed_max = speed_max
        print(f"Speed range: {speed_min:.2f} - {speed_max:.2f}")

    def update_interval_range(self, val):
        """Update interval range (min and max)"""
        interval_min, interval_max = val
        self.collider.interval_min = interval_min
        self.collider.interval_max = interval_max
        print(f"Interval range: {interval_min:.2f} - {interval_max:.2f}")

    def update_trigger_level(self, val):
        """Update DAQ trigger level for sparklines"""
        self.collider.calorimeter_daq.trigger_level = val
        # Update trigger level lines in all sparklines (offset by channel)
        for ch, trigger_line in enumerate(self.sparkline_trigger_lines):
            offset = ch * self.trace_offset
            trigger_line.set_ydata([offset + val, offset + val])
        print(f"Trigger level: {val:.2f}")

    def update_timespan(self, val):
        """Update oscilloscope time span (trigger mode)"""
        self.time_span = val
        # Update x-axis limits
        label_offset = val * 0.02  # 2% of span for labels
        self.ax_sparklines.set_xlim(-label_offset, val)
        print(f"Time span: {val:.1f} ms")

    def update_timespan_freerun(self, val):
        """Update oscilloscope time span (free-running mode)"""
        # val is in seconds, convert to milliseconds
        self.time_span = val * 1000.0

        # Calculate required buffer size for this time span at 5 Hz
        num_samples = int(self.time_span / 200)  # 200ms per sample at 5 Hz
        self.collider.calorimeter_daq.free_running_display_samples = num_samples

        # Resize free-running buffer
        self.collider.calorimeter_daq.free_running_buffer = np.zeros(
            (self.collider.calorimeter_daq.num_channels, num_samples),
            dtype=np.float32
        )
        self.collider.calorimeter_daq.free_running_sample_count = 0

        # Update time axis for new buffer size
        self.sparkline_time_freerun = np.arange(num_samples) * 200

        # Update x-axis limits
        label_offset = self.time_span * 0.02  # 2% of span for labels
        self.ax_sparklines.set_xlim(-label_offset, self.time_span)
        print(f"Time span: {val:.1f} s ({self.time_span:.0f} ms, {num_samples} samples)")

    def toggle_scope_mode(self, event):
        """Toggle between trigger mode and free-running mode"""
        self.collider.calorimeter_daq.free_running = not self.collider.calorimeter_daq.free_running
        if self.collider.calorimeter_daq.free_running:
            self.button_scope_mode.label.set_text('Free Running')

            # Set default time span to 50 seconds for free-running
            self.time_span = 50000.0  # 50 seconds

            # Calculate required buffer size for this time span at 5 Hz
            num_samples = int(self.time_span / 200)  # 200ms per sample at 5 Hz
            self.collider.calorimeter_daq.free_running_display_samples = num_samples

            # Reset free-running buffer with new size (clears old data)
            self.collider.calorimeter_daq.free_running_buffer = np.zeros(
                (self.collider.calorimeter_daq.num_channels, num_samples),
                dtype=np.float32
            )
            # Start at decimation-1 so next sample goes to index 0 immediately
            self.collider.calorimeter_daq.free_running_sample_count = self.collider.calorimeter_daq.free_running_decimation - 1

            # Update time axis for new buffer size
            self.sparkline_time_freerun = np.arange(num_samples) * 200

            # Immediately clear all sparkline displays to show baseline
            for ch in range(64):
                offset = ch * self.trace_offset
                self.sparkline_lines[ch].set_ydata(np.zeros(num_samples) + offset)

            # Adjust x-axis
            label_offset = self.time_span * 0.02
            self.ax_sparklines.set_xlim(-label_offset, self.time_span)

            # Recreate vertical time span slider with free-running range (100ms to 60 seconds)
            self.slider_timespan.disconnect_events()
            self.slider_timespan_ax.clear()
            self.slider_timespan = Slider(
                self.slider_timespan_ax, 'Time\nSpan\n(s)', 0.1, 60.0,
                valinit=self.time_span / 1000.0,  # Convert to seconds for display
                valstep=0.1,
                orientation='vertical'
            )
            self.slider_timespan.on_changed(self.update_timespan_freerun)

            print(f"Oscilloscope mode: Free Running (5 Hz update, {self.time_span/1000:.1f}s display)")
        else:
            self.button_scope_mode.label.set_text('Trigger Mode')
            # Re-arm all triggers and clear old data
            self.collider.calorimeter_daq.trigger_armed.fill(True)
            self.collider.calorimeter_daq.trigger_capturing.fill(False)
            self.collider.calorimeter_daq.trigger_has_data.fill(False)
            self.collider.calorimeter_daq.trigger_samples.fill(0.0)
            self.collider.calorimeter_daq.trigger_sample_count.fill(0)

            # Restore time span to 1000ms default for trigger mode
            self.time_span = 1000.0

            # Restore x-axis to current time span setting
            label_offset = self.time_span * 0.02
            self.ax_sparklines.set_xlim(-label_offset, self.time_span)

            # Immediately clear all sparkline displays to show baseline
            for ch in range(64):
                offset = ch * self.trace_offset
                self.sparkline_lines[ch].set_ydata(np.zeros(1000) + offset)

            # Recreate vertical time span slider with trigger range (0.1ms to 1000ms)
            self.slider_timespan.disconnect_events()
            self.slider_timespan_ax.clear()
            self.slider_timespan = Slider(
                self.slider_timespan_ax, 'Time\nSpan\n(ms)', 0.1, 1000.0,
                valinit=self.time_span,
                valstep=0.1,
                orientation='vertical'
            )
            self.slider_timespan.on_changed(self.update_timespan)

            print("Oscilloscope mode: Triggered")

    def toggle_pause(self, event):
        """Toggle simulation pause state"""
        self.collider.paused = not self.collider.paused
        self.button_pause.label.set_text('Resume' if self.collider.paused else 'Pause')
        print(f"Simulation {'paused' if self.collider.paused else 'resumed'}")

    def reset_simulation(self, event):
        """Reset the simulation"""
        self.collider.reset()

    def save_summary(self, event):
        """Save simulation summary"""
        if self.collider.data_logger:
            self.collider.data_logger.save_summary(self.collider)
        else:
            print("No data logger available")

    def update_frame(self, frame):
        """Update animation frame"""
        dt = 0.05  # Time step in seconds
        self.collider.update(dt)

        # Clear old trail lines and particle markers
        for line in self.trail_lines:
            line.remove()
        self.trail_lines = []

        # Clear old particle scatter
        if hasattr(self, 'particle_markers'):
            for marker in self.particle_markers:
                marker.remove()
        self.particle_markers = []

        for particle in self.collider.particles:
            if len(particle.trail) > 0 or particle.hit_calorimeter:
                # Color based on deflection state
                if particle.hit_calorimeter:
                    color = 'red'  # Red when stopped at calorimeter
                elif particle.deflected:
                    color = 'orange'
                else:
                    color = 'blue'

                # Draw particle with its alpha value (for fading)
                marker, = self.ax.plot(particle.position[0], particle.position[1],
                                      'o', color=color, markersize=8,
                                      alpha=particle.alpha)
                self.particle_markers.append(marker)

                # Draw trail
                if len(particle.trail) > 1:
                    trail_array = np.array(particle.trail)
                    # Trail alpha based on particle state
                    trail_alpha = 0.3 * particle.alpha if not particle.active else 0.5 * particle.alpha
                    line, = self.ax.plot(trail_array[:, 0], trail_array[:, 1],
                                        'b-', alpha=trail_alpha, linewidth=1)
                    self.trail_lines.append(line)

        # Update title with stats
        active_count = sum(1 for p in self.collider.particles if p.active)
        self.ax.set_title(f'Particle Collider Simulation\n'
                         f'Time: {self.collider.time_elapsed:.1f}s | '
                         f'Active: {active_count} | '
                         f'Total: {self.collider.particle_count}')

        # Update pixel detector text box
        if self.collider.recent_pixel_hits:
            pixel_text_lines = ['Pixel Detector Hits:']
            for hit in list(self.collider.recent_pixel_hits)[-5:]:
                pixel_text_lines.append(
                    f"Pixel {hit['pixel']:4d} @ t={hit['time']:.2f}s"
                )
            self.pixel_text.set_text('\n'.join(pixel_text_lines))
        else:
            self.pixel_text.set_text('Pixel Detector Hits:\n(waiting...)')

        # Update calorimeter histogram
        for i, bar in enumerate(self.hist_bars):
            bar.set_width(self.collider.calorimeter_counts[i])

        # Update histogram x-axis to fit data
        max_count = max(self.collider.calorimeter_counts) if max(self.collider.calorimeter_counts) > 0 else 10
        self.ax_hist.set_xlim(0, max_count * 1.1)

        # Sync sliders with collider values (in case they were changed via XML-RPC)
        current_speed_range = self.slider_speed_range.val
        desired_speed_range = (self.collider.speed_min, self.collider.speed_max)
        if abs(current_speed_range[0] - desired_speed_range[0]) > 0.01 or \
           abs(current_speed_range[1] - desired_speed_range[1]) > 0.01:
            self.slider_speed_range.eventson = False
            self.slider_speed_range.set_val(desired_speed_range)
            self.slider_speed_range.eventson = True

        current_interval_range = self.slider_interval_range.val
        desired_interval_range = (self.collider.interval_min, self.collider.interval_max)
        if abs(current_interval_range[0] - desired_interval_range[0]) > 0.01 or \
           abs(current_interval_range[1] - desired_interval_range[1]) > 0.01:
            self.slider_interval_range.eventson = False
            self.slider_interval_range.set_val(desired_interval_range)
            self.slider_interval_range.eventson = True

        # Update DAQ waterfall display
        # Get the waterfall buffer from DAQ (already decimated to 10 FPS)
        waterfall_data = self.collider.calorimeter_daq.waterfall_buffer.copy()

        # Clip values to fixed range [0, 1.5] for saturation
        waterfall_data = np.clip(waterfall_data, 0.0, 1.5)

        # Update the image data
        self.daq_image.set_data(waterfall_data)

        # Update sparkline oscilloscope traces (stacked with vertical offset)
        # Amplify pulse for visibility
        for ch in range(64):
            offset = ch * self.trace_offset
            if self.collider.calorimeter_daq.free_running:
                # Free-running mode - show continuously scrolling data
                # Use 50x amplification for visibility
                amplitude_scale = 50.0
                waveform = (self.collider.calorimeter_daq.free_running_buffer[ch, :] * amplitude_scale) + offset
                self.sparkline_lines[ch].set_xdata(self.sparkline_time_freerun)
                self.sparkline_lines[ch].set_ydata(waveform)
            else:
                # Triggered mode - use 50x amplification
                amplitude_scale = 50.0
                self.sparkline_lines[ch].set_xdata(self.sparkline_time)
                if self.collider.calorimeter_daq.trigger_has_data[ch]:
                    # Get captured waveform, amplify by 50x, and add offset
                    waveform = (self.collider.calorimeter_daq.trigger_samples[ch, :] * amplitude_scale) + offset
                    # Update trace
                    self.sparkline_lines[ch].set_ydata(waveform)
                else:
                    # No data yet - show baseline at offset
                    self.sparkline_lines[ch].set_ydata(np.zeros(1000) + offset)

        # Manually trigger redraw of sparklines figure (it's a separate figure with no animation loop)
        self.fig_sparklines.canvas.draw_idle()
        self.fig_sparklines.canvas.flush_events()

        return tuple(self.particle_markers + self.trail_lines),

    def run(self, interval=50):
        """Run the animation"""
        anim = animation.FuncAnimation(
            self.fig, self.update_frame,
            interval=interval, blit=False, cache_frame_data=False
        )
        plt.show()


def main():
    """Main entry point"""
    print("=" * 60)
    print("Particle Collider Simulation")
    print("=" * 60)
    print("\nControls:")
    print("  - Speed Min/Max: Adjust particle speed range")
    print("  - Interval Min/Max: Adjust injection timing range")
    print("  - Pause/Resume: Pause or resume the simulation")
    print("  - Reset: Clear all particles and restart")
    print("  - Save: Save summary statistics to file")
    print("\nClose the plot window to exit and save final data.")
    print("=" * 60 + "\n")

    # Create data logger
    data_logger = DataLogger()

    # Create collider with data logger
    collider = ParticleCollider(data_logger=data_logger)

    # Create visualizer first (so we can pass it to RPC server)
    visualizer = ColliderVisualizer(collider)

    # Start XML-RPC server for remote control with visualizer reference
    rpc_server = ColliderRPCServer(collider, visualizer=visualizer, host='localhost', port=8000)
    rpc_server.start()

    # Setup cleanup on close
    def on_close(event):
        print("\nSaving final summary...")
        data_logger.save_summary(collider)

        # Export DAQ data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        daq_filename = f"calorimeter_daq_{timestamp}.h5"
        collider.calorimeter_daq.export_hdf5(daq_filename)

        rpc_server.stop()
        print("Simulation ended.")

    visualizer.fig.canvas.mpl_connect('close_event', on_close)

    # Run simulation
    visualizer.run()


if __name__ == '__main__':
    main()
