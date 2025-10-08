# FM Receiver Plan for GNU Radio with RTL-SDR

## Basic FM Receiver Architecture

**1. RTL-SDR Source**
- Use the `osmocom Source` or `RTL-SDR Source` block
- Set sample rate to 2.4 MHz (or 2 MHz)
- Tune to desired FM station frequency (88-108 MHz)
- Set appropriate RF gain

**2. Signal Processing Chain**
- **Low-pass filter**: Isolate the FM channel (~200 kHz bandwidth)
- **Rational resampler**: Downsample to a lower rate (e.g., 480 kHz)
- **WBFM Receive**: Demodulate FM signal (quadrature demod)
- **Audio resampler**: Resample to 48 kHz for audio output
- **Volume control**: Multiply block for gain adjustment
- **Audio sink**: Output to speakers

**3. Key Parameters**
- RTL-SDR sample rate: 2.4 MHz
- FM channel bandwidth: ~200 kHz
- Audio output rate: 48 kHz
- FM deviation: 75 kHz (standard in most regions)

**4. Optional Enhancements**
- Add FFT sink to visualize spectrum
- Add waterfall sink for signal monitoring
- QT GUI Range slider for frequency tuning
- Squelch block to mute weak signals

**5. Testing**
- Start with a strong local FM station
- Adjust RF gain to avoid overload
- Fine-tune frequency offset if needed
- Monitor audio quality and adjust filter parameters

This basic flowgraph should give you clear FM radio reception from broadcast stations.
