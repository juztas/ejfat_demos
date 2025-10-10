# RDS Decoder Integration

## Overview

The `fm_receiver_shm.grc` flowgraph now includes RDS (Radio Data System) decoder blocks. These blocks are currently **disabled** as they require additional signal processing blocks to properly extract and condition the RDS subcarrier signal.

## What Was Added

1. **fm_freq variable** - Station frequency (default 88.5 MHz) used by the RDS panel
2. **rds_decoder_0** - Decodes RDS data from byte stream
3. **rds_parser_0** - Parses decoded RDS messages (configured for North America PTY codes)
4. **rds_panel_0** - GUI panel to display RDS information (station name, program type, radio text, etc.)

## Current Status

The RDS blocks are set to `state: disabled` because they need:

1. **RDS Subcarrier Extraction** - Filter to extract 57 kHz RDS subcarrier from FM demodulator output
2. **Carrier Recovery** - PLL to recover the 57 kHz carrier
3. **Demodulation** - BPSK demodulation of the RDS signal
4. **Symbol Synchronization** - Timing recovery for 1187.5 baud RDS data
5. **Differential Decoding** - Convert to bytes for the RDS decoder

## To Enable RDS Decoding

You'll need to add the complete RDS signal processing chain between the FM demodulator and the RDS decoder. Reference:
- Example flowgraph: `/opt/anaconda3/envs/gnuradio/share/gnuradio/examples/rds/rds_rx.grc`
- This shows the full signal processing chain needed for RDS

The typical chain includes:
- Band-pass filter (centered at 57 kHz)
- PLL for carrier recovery  
- Multiply/mix for demodulation
- Root-raised cosine filter
- Symbol synchronization
- Constellation decoder
- Differential decoder
- RDS decoder (already added)
- RDS parser (already added)
- RDS panel (already added)

## Quick Enable (for testing)

To enable the RDS blocks in GRC:
1. Open `fm_receiver_shm.grc` in gnuradio-companion
2. Find the three RDS blocks (decoder, parser, panel)
3. Right-click each and change "State" from "Disabled" to "Enabled"
4. Add the required signal conditioning blocks (see example above)
5. Connect them properly

## Notes

- The RDS blocks are functional and gr-rds has been successfully installed
- PTY locale is set to North America (pty_locale: '1')
- FM frequency can be adjusted via the `fm_freq` variable
- The RDS panel will display: Station Name, Program Type, Radio Text, and other RDS data when properly connected

