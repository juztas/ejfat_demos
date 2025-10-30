# Particle Collider XML-RPC Remote Control

## Overview

The particle collider simulation includes an XML-RPC server that allows remote control via HTTP. This enables external programs and web interfaces to control simulation parameters in real-time.

## Server Configuration

- **Host**: localhost
- **Port**: 8000
- **Protocol**: XML-RPC over HTTP

The server starts automatically when you run the particle collider simulation.

## Available RPC Methods

### Control Methods

#### `set_speed_min(value: float)`
Set the minimum particle speed (0.1 - 1.0)

**Parameters:**
- `value`: Float between 0.1 and 1.0

**Returns:**
```python
{
    "success": True,
    "value": 0.5
}
```

#### `set_speed_max(value: float)`
Set the maximum particle speed (0.1 - 1.5)

**Parameters:**
- `value`: Float between 0.1 and 1.5

**Returns:**
```python
{
    "success": True,
    "value": 1.0
}
```

#### `set_interval_min(value: float)`
Set the minimum injection interval in seconds (0.1 - 2.0)

**Parameters:**
- `value`: Float between 0.1 and 2.0

**Returns:**
```python
{
    "success": True,
    "value": 0.5
}
```

#### `set_interval_max(value: float)`
Set the maximum injection interval in seconds (0.1 - 2.0)

**Parameters:**
- `value`: Float between 0.1 and 2.0

**Returns:**
```python
{
    "success": True,
    "value": 1.0
}
```

#### `pause()`
Pause the simulation

**Returns:**
```python
{
    "success": True,
    "paused": True
}
```

#### `resume()`
Resume the simulation

**Returns:**
```python
{
    "success": True,
    "paused": False
}
```

#### `reset()`
Reset the simulation (clears all particles, resets time)

**Returns:**
```python
{
    "success": True
}
```

### Query Methods

#### `get_status()`
Get current simulation status

**Returns:**
```python
{
    "time_elapsed": 123.45,
    "particle_count": 150,
    "active_particles": 12,
    "paused": False,
    "speed_min": 0.5,
    "speed_max": 1.0,
    "interval_min": 0.5,
    "interval_max": 1.0
}
```

#### `get_statistics()`
Get simulation statistics

**Returns:**
```python
{
    "total_particles": 150,
    "current_particles": 25,
    "speed": {
        "mean": 0.752,
        "min": 0.503,
        "max": 0.998
    },
    "deflection_angle": {
        "mean": -12.34,
        "min": -134.87,
        "max": 132.45
    }
}
```

## Usage Examples

### Python Client

```python
import xmlrpc.client

# Connect to the collider RPC server
proxy = xmlrpc.client.ServerProxy("http://localhost:8000/")

# Set parameters
result = proxy.set_speed_min(0.6)
print(result)  # {'success': True, 'value': 0.6}

result = proxy.set_speed_max(1.2)
print(result)  # {'success': True, 'value': 1.2}

# Pause simulation
proxy.pause()

# Get status
status = proxy.get_status()
print(f"Time: {status['time_elapsed']:.1f}s")
print(f"Particles: {status['particle_count']}")
print(f"Paused: {status['paused']}")

# Resume
proxy.resume()

# Get statistics
stats = proxy.get_statistics()
print(f"Mean speed: {stats['speed']['mean']:.3f}")
```

### JavaScript Client (Browser)

```javascript
async function setSpeedMin(value) {
    const xmlRequest = `<?xml version="1.0"?>
<methodCall>
    <methodName>set_speed_min</methodName>
    <params>
        <param><value><double>${value}</double></value></param>
    </params>
</methodCall>`;

    const response = await fetch('http://localhost:8000', {
        method: 'POST',
        headers: { 'Content-Type': 'text/xml' },
        body: xmlRequest
    });

    const text = await response.text();
    // Parse XML response...
}

// Call the function
setSpeedMin(0.7);
```

### cURL

```bash
# Set speed minimum
curl -X POST http://localhost:8000 \
  -H "Content-Type: text/xml" \
  -d '<?xml version="1.0"?>
<methodCall>
  <methodName>set_speed_min</methodName>
  <params>
    <param><value><double>0.7</double></value></param>
  </params>
</methodCall>'

# Get status
curl -X POST http://localhost:8000 \
  -H "Content-Type: text/xml" \
  -d '<?xml version="1.0"?>
<methodCall>
  <methodName>get_status</methodName>
  <params></params>
</methodCall>'
```

## Web Interface

A pre-built web interface is included for easy control via browser.

### Starting the Web Interface

1. **Start the particle collider simulation:**
   ```bash
   python particle_collider.py
   ```

2. **In a separate terminal, start the web server:**
   ```bash
   python web_server.py
   ```

3. **Open in your browser:**
   ```
   http://localhost:8001/collider_control.html
   ```

The web interface provides:
- Real-time status display (time, particle counts, running/paused)
- Interactive sliders for all parameters
- Pause/Resume/Reset buttons
- Auto-refreshing status every second

## Architecture

```
┌─────────────────┐         XML-RPC          ┌──────────────────┐
│                 │◄─────── (port 8000) ──────┤                  │
│   Particle      │                           │  Remote Client   │
│   Collider      │                           │  (Python/Web/    │
│   Simulation    │                           │   Other)         │
│                 │                           │                  │
└─────────────────┘                           └──────────────────┘
        ▲
        │
        │ Controls
        │
        ▼
┌─────────────────┐
│  matplotlib     │
│  Visualization  │
└─────────────────┘
```

The XML-RPC server runs in a background thread, allowing simultaneous:
- Real-time visualization via matplotlib
- Remote control via XML-RPC
- Data logging to CSV/JSON

## Security Note

**WARNING**: The XML-RPC server is configured for `localhost` only and is intended for local development and demonstrations. For production use or network access:

1. Add authentication
2. Use HTTPS/TLS encryption
3. Implement rate limiting
4. Add input validation
5. Consider using a more secure protocol (REST API with JWT, etc.)

## Troubleshooting

### Connection Refused
- Ensure the particle collider simulation is running
- Check that port 8000 is not blocked by firewall
- Verify the server started successfully (check console output)

### Web Interface Not Loading
- Make sure both the collider AND web server are running
- The collider runs on port 8000 (XML-RPC)
- The web server runs on port 8001 (HTTP)
- Check browser console for errors

### Parameter Changes Not Working
- Verify parameter values are within valid ranges
- Check that min values are less than max values
- Look for error messages in the simulation console

## Integration Examples

### GNU Radio Integration

```python
# In a GNU Radio block or Python snippet
import xmlrpc.client

collider = xmlrpc.client.ServerProxy("http://localhost:8000/")

# Control collider from GNU Radio flowgraph
collider.set_speed_min(0.8)
collider.pause()
```

### Automated Testing

```python
import xmlrpc.client
import time

proxy = xmlrpc.client.ServerProxy("http://localhost:8000/")

# Reset to known state
proxy.reset()

# Test different speed ranges
for speed in [0.5, 0.7, 0.9]:
    proxy.set_speed_min(speed)
    proxy.set_speed_max(speed + 0.2)
    time.sleep(10)  # Run for 10 seconds
    stats = proxy.get_statistics()
    print(f"Speed {speed}: {stats}")
```

## References

- [XML-RPC Specification](http://xmlrpc.com/spec.md)
- [Python xmlrpc.client](https://docs.python.org/3/library/xmlrpc.client.html)
- [Python xmlrpc.server](https://docs.python.org/3/library/xmlrpc.server.html)
