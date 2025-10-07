# Makefile for gr-ejfat Python blocks
# Simple installation helper for pure Python GNU Radio blocks

.PHONY: install uninstall test clean help

# Default target
help:
	@echo "gr-ejfat Installation Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make install    - Install Python blocks and GRC definitions"
	@echo "  make uninstall  - Remove installed blocks"
	@echo "  make test       - Run unit tests"
	@echo "  make clean      - Remove build artifacts"
	@echo "  make help       - Show this help message"

# Install Python package and GRC block definitions
install:
	@echo "Installing gr-ejfat Python blocks..."
	pip install -e .
	@echo ""
	@echo "Installing GRC block definitions..."
	mkdir -p ~/.grc_gnuradio
	cp grc/ejfat_ejfat_sink.block.yml ~/.grc_gnuradio/
	cp grc/ejfat_ejfat_source.block.yml ~/.grc_gnuradio/
	cp grc/ejfat_ejfat_shm_sink.block.yml ~/.grc_gnuradio/
	cp grc/ejfat_ejfat_shm_source.block.yml ~/.grc_gnuradio/
	@echo ""
	@echo "✓ Installation complete!"
	@echo ""
	@echo "Verify installation with:"
	@echo "  make test"
	@echo "  gnuradio-companion examples/test_ejfat_blocks.grc"

# Uninstall blocks
uninstall:
	@echo "Uninstalling gr-ejfat Python package..."
	pip uninstall -y gnuradio-ejfat || true
	@echo ""
	@echo "Removing GRC block definitions..."
	rm -f ~/.grc_gnuradio/ejfat_ejfat_sink.block.yml
	rm -f ~/.grc_gnuradio/ejfat_ejfat_source.block.yml
	rm -f ~/.grc_gnuradio/ejfat_ejfat_shm_sink.block.yml
	rm -f ~/.grc_gnuradio/ejfat_ejfat_shm_source.block.yml
	@echo ""
	@echo "✓ Uninstall complete!"

# Run unit tests
test:
	@echo "Running unit tests..."
	@echo ""
	@echo "Testing ejfat_sink block..."
	python python/ejfat/qa_ejfat_sink.py
	@echo ""
	@echo "Testing ejfat_source block..."
	python python/ejfat/qa_ejfat_source.py
	@echo ""
	@echo "Testing ejfat_shm_sink block..."
	python python/ejfat/qa_ejfat_shm_sink.py
	@echo ""
	@echo "Testing ejfat_shm_source block..."
	python python/ejfat/qa_ejfat_shm_source.py
	@echo ""
	@echo "✓ All tests complete!"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf gnuradio_ejfat.egg-info/
	rm -rf dist/
	find python -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find python -type f -name "*.pyc" -delete
	@echo "✓ Clean complete!"
