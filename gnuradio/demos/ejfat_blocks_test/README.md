# EJFAT Blocks Test & Demo

This directory contains a comprehensive test flowgraph for all EJFAT GNU Radio blocks.

## Overview

The `ejfat_blocks_test` flowgraph demonstrates and tests all EJFAT blocks working together:
- EJFAT Source/Sink blocks
- EJFAT SHM (Shared Memory) Source/Sink blocks
- Signal generation and visualization

## Files

- **ejfat_blocks_test.grc** - GNU Radio Companion flowgraph
- **ejfat_blocks_test.py** - Generated Python code (auto-generated from .grc)

## Purpose

This test flowgraph is designed to:
1. **Test all EJFAT blocks** - Validates that all blocks load and work
2. **Demonstrate functionality** - Shows how to use each block
3. **Verify integration** - Tests blocks working together
4. **Random data testing** - Uses random signals for basic validation

## What It Tests

### EJFAT Blocks Included:
- **ejfat.ejfat_source** - Receives data via EJFAT protocol
- **ejfat.ejfat_sink** - Sends data via EJFAT protocol
- **ejfat.ejfat_shm_source** - Receives data via shared memory
- **ejfat.ejfat_shm_sink** - Sends data via shared memory

### Signal Path:
```
Random Source → EJFAT Sink → EJFAT Source → Display
Random Source → SHM Sink → SHM Source → Display
```

## Quick Start

### Open in GNU Radio Companion

```bash
cd /Users/yak/Projects/EJFAT/ejfat_demos/gnuradio/demos/ejfat_blocks_test
conda activate gnuradio
gnuradio-companion ejfat_blocks_test.grc
```

Then click the Execute (▶) button to run.

### Run from Command Line

```bash
cd /Users/yak/Projects/EJFAT/ejfat_demos/gnuradio/demos/ejfat_blocks_test
conda activate gnuradio
python ejfat_blocks_test.py
```

## Prerequisites

- GNU Radio environment: `conda activate gnuradio`
- gr-ejfat module installed
- ejfat_shm Python package installed

### Verify Prerequisites

```bash
conda activate gnuradio
python -c "from gnuradio import ejfat; print('✓ gr-ejfat found')"
python -c "import ejfat_shm; print('✓ ejfat_shm found')"
```

## Expected Results

When running successfully:
- Multiple GUI windows showing time and frequency plots
- Random data flowing through EJFAT blocks
- No error messages in console
- Smooth signal display (not frozen or stuttering)

## Configuration

The flowgraph includes default configurations for:
- Sample rate: 32 kHz (default)
- EJFAT URI: Default loopback configuration
- SHM buffer parameters: Default sizes
- Vector sizes: Configured for testing

To modify:
1. Open `ejfat_blocks_test.grc` in GNU Radio Companion
2. Double-click blocks to edit parameters
3. Click Generate (⚙) to regenerate Python code
4. Click Execute (▶) to run

## Differences from E2SAR Tests

This test is different from the E2SAR tests in `../e2sar_test/`:

| Feature | EJFAT Blocks Test | E2SAR Test |
|---------|-------------------|------------|
| Purpose | Test all EJFAT blocks | Test E2SAR segmenter/reassembler |
| Blocks | All EJFAT blocks (source, sink, shm) | E2SAR specific blocks |
| Data | Random signals | Real signals (tone) |
| Focus | Block functionality | E2SAR protocol testing |

## Troubleshooting

### "Module not found: ejfat"

```bash
# Install gr-ejfat module
cd /Users/yak/Projects/EJFAT/ejfat_demos/gnuradio/gr-ejfat
make install
```

### "Module not found: ejfat_shm"

```bash
# Install ejfat_shm package
cd /Users/yak/Projects/EJFAT/ejfat_demos/gnuradio/ejfat_shm
pip install -e .
```

### Blocks don't appear in GRC

```bash
# Update GRC block cache
gnuradio-companion --clear-cache
```

### Flowgraph won't execute

- Check that all prerequisites are installed
- Verify GNU Radio environment is activated
- Check console for specific error messages

## Related Demos

- **E2SAR Tests**: `../e2sar_test/` - E2SAR segmenter/reassembler specific tests
- **FM Demos**: `../fm/` - Real-world FM radio applications
- **Widget Demos**: `../widget/` - Bluesky control integration

## See Also

- gr-ejfat module: `/Users/yak/Projects/EJFAT/ejfat_demos/gnuradio/gr-ejfat/`
- ejfat_shm package: `/Users/yak/Projects/EJFAT/ejfat_demos/gnuradio/ejfat_shm/`
- EJFAT blocks documentation: `../custom/`
