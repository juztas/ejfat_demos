# Makefile for EJFAT SHM Daemon

# Compiler settings
CC = gcc
CXX = g++
CFLAGS = -Wall -Wextra -O2 -g -fPIC
CXXFLAGS = -Wall -Wextra -O2 -g -fPIC -std=c++17
LDFLAGS = -pthread -lrt

# E2SAR settings
E2SAR_DIR ?= $(HOME)/Projects/E2SAR
E2SAR_BUILD_DIR ?= $(E2SAR_DIR)/build_fec
E2SAR_INCLUDE = $(E2SAR_DIR)/include
E2SAR_LIB = $(E2SAR_BUILD_DIR)/src/libe2sar.so

# Include paths
INCLUDES = -Iinclude -I$(E2SAR_INCLUDE)

# Source files
C_SOURCES = src/shm_reader.c src/config.c
CXX_SOURCES = src/ejfat_shm_daemon.cpp

# Object files
C_OBJECTS = $(C_SOURCES:.c=.o)
CXX_OBJECTS = $(CXX_SOURCES:.cpp=.o)
OBJECTS = $(C_OBJECTS) $(CXX_OBJECTS)

# Target executable
TARGET = ejfat_shm_daemon

# Installation directories
PREFIX ?= /usr/local
BINDIR = $(PREFIX)/bin
SYSCONFDIR = $(PREFIX)/etc

# Default target
all: check_e2sar $(TARGET)

# Check if E2SAR library exists
check_e2sar:
	@if [ ! -f "$(E2SAR_LIB)" ]; then \
		echo "Error: E2SAR library not found at $(E2SAR_LIB)"; \
		echo "Please set E2SAR_BUILD_DIR to point to your E2SAR build directory"; \
		echo "Example: make E2SAR_BUILD_DIR=~/Projects/E2SAR/build"; \
		exit 1; \
	fi
	@echo "Using E2SAR library: $(E2SAR_LIB)"

# Link target
$(TARGET): $(OBJECTS)
	$(CXX) -o $@ $^ $(LDFLAGS) -L$(E2SAR_BUILD_DIR)/src -le2sar -Wl,-rpath,$(E2SAR_BUILD_DIR)/src

# Compile C sources
%.o: %.c
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

# Compile C++ sources
%.o: %.cpp
	$(CXX) $(CXXFLAGS) $(INCLUDES) -c $< -o $@

# Install
install: $(TARGET)
	install -d $(DESTDIR)$(BINDIR)
	install -m 755 $(TARGET) $(DESTDIR)$(BINDIR)/
	install -d $(DESTDIR)$(SYSCONFDIR)
	install -m 644 ejfat_shm_daemon.conf.example $(DESTDIR)$(SYSCONFDIR)/

# Uninstall
uninstall:
	rm -f $(DESTDIR)$(BINDIR)/$(TARGET)
	rm -f $(DESTDIR)$(SYSCONFDIR)/ejfat_shm_daemon.conf.example

# Clean
clean:
	rm -f $(OBJECTS) $(TARGET)

# Clean all
distclean: clean
	rm -f *~ src/*~ include/*~

# Help
help:
	@echo "EJFAT SHM Daemon Build System"
	@echo ""
	@echo "Targets:"
	@echo "  all        - Build daemon (default)"
	@echo "  install    - Install daemon to $(PREFIX)"
	@echo "  uninstall  - Remove installed files"
	@echo "  clean      - Remove build artifacts"
	@echo "  distclean  - Remove all generated files"
	@echo "  help       - Show this help"
	@echo ""
	@echo "Variables:"
	@echo "  E2SAR_DIR       - E2SAR source directory (default: ~/Projects/E2SAR)"
	@echo "  E2SAR_BUILD_DIR - E2SAR build directory (default: E2SAR_DIR/build_fec)"
	@echo "  PREFIX          - Installation prefix (default: /usr/local)"
	@echo ""
	@echo "Example:"
	@echo "  make E2SAR_BUILD_DIR=~/Projects/E2SAR/build"
	@echo "  make install PREFIX=/usr/local"

.PHONY: all check_e2sar install uninstall clean distclean help

# Dependencies
src/shm_reader.o: src/shm_reader.c include/shm_reader.h
src/config.o: src/config.c include/config.h
src/ejfat_shm_daemon.o: src/ejfat_shm_daemon.cpp include/shm_reader.h include/config.h
