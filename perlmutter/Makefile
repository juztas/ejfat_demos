
#
#  This makefile runs on a Perlmutter login node, and provides the podman-hpc and slurm commands
#  to build and operate the EJFAT load balancer.
#
#  Yatish Kumar
#  July 2024
#------------------------------------------------------------------------------------------------

.PHONY: help build reserve free receive send monitor send_file receive_file

#------------------------------------------------------------------------------------------------
# VARIABLE DOCUMENTATION
#------------------------------------------------------------------------------------------------
# All configuration variables are defined here with sensible defaults.
# Override any variable using: make <target> VAR=value
#
# Network Configuration:
#   IP_VERSION        - IP version to use (-4 or -6)
#   LB_IP             - Load balancer IP address (auto-detected based on IP_VERSION)
#   MY_IP             - Local IP address (auto-detected)
#   MY_INTERFACE      - Network interface (auto-detected)
#   EJFAT_URI_BETA    - EJFAT URI for reservation
#   INSTANCE_URI      - Instance URI from reservation
#
# Performance Configuration:
#   RX_DURATION       - Receiver duration in seconds
#   RX_THREADS        - Number of receiver threads
#   RX_BUFSIZE        - Receiver buffer size in bytes
#   RX_TIMEOUT        - Receiver timeout in milliseconds
#   RX_CORES          - Number of cores for receiver
#   RX_DEQ            - Dequeue depth for receiver
#   TX_RATE           - Transmit rate in Gbps
#   TX_LENGTH         - Transmit data length in bytes
#   SEND_SOCKETS      - Number of sending sockets
#   NFRAMES           - Number of frames to send
#   DATA_ID           - Data ID for transmission
#
# File Transfer Configuration:
#   FT_EXTENSION      - File extension for file transfer
#   FT_PREFIX         - File prefix for file transfer
#   FT_RATE           - File transfer rate
#   FT_SOCKETS        - Number of sockets for file transfer
#   FT_TIMEOUT        - File transfer timeout in milliseconds
#   FT_THREADS        - Number of threads for file transfer
#   FT_NUMFILES       - Number of test files to generate
#   FT_FILESIZE       - Size of test files in MB
#   DATA_DIR          - Data directory path (for local containerized execution)
#   DATA_RX_DIR       - Receive data directory path (for local containerized execution)
#   DATA_PATH         - Data directory path on remote node (default: /data)
#
# Monitoring Configuration:
#   MONITOR_PORTS     - Port range to monitor (format: start-end)
#   MONITOR_INTERVAL  - Monitoring sample interval in seconds
#
# Load Balancer Configuration:
#   LB_RESERVE_DURATION - Reservation duration in days
#   LB_NAME             - Load balancer instance name
#
# Logging Configuration:
#   LOG_DIR           - Directory for log files
#
# Remote Execution Configuration:
#   NODE              - Optional remote node name for SSH execution (e.g., nid001234)
#                       When set, scripts execute on remote node via SSH with conda activation
#                       When empty, scripts execute locally in podman-hpc container
#------------------------------------------------------------------------------------------------

#------------------------------------------------------------------------------------------------
# NETWORK CONFIGURATION
#------------------------------------------------------------------------------------------------
IP_VERSION ?= -6

ifeq ($(IP_VERSION),-4)
  LB_IP ?= $(shell dig +short ejfat-lb.es.net A | tail -1 )
  MY_IP ?= $(shell ip route get $(LB_IP) | head -1 | sed 's/^.*src//' | awk '{ print $$1 }')
else
  LB_IP ?= $(shell dig +short ejfat-lb.es.net AAAA | tail -1 )
  MY_IP ?= $(shell ip route get $(LB_IP) | head -1 | sed 's/^.*src//' | awk '{ print $$1 }')
endif

MY_INTERFACE ?= $(shell ip route get $(LB_IP) | head -1 | sed 's/^.*dev//' | awk '{ print $$1 }')
INSTANCE_URI := $(shell cat INSTANCE_URI 2>/dev/null | sed 's/^[^=]*=//')

#------------------------------------------------------------------------------------------------
# PERFORMANCE CONFIGURATION
#------------------------------------------------------------------------------------------------
RX_DURATION ?= 120
RX_THREADS ?= 16
RX_BUFSIZE ?= 400000000
RX_TIMEOUT ?= 7000
RX_CORES ?= 1
RX_DEQ ?= 16

TX_RATE ?= 0.1
TX_LENGTH ?= 2097152
SEND_SOCKETS ?= 8
NFRAMES ?= 10000
DATA_ID ?= $(shell bash -c 'echo $$(( $$RANDOM % 1000 + 1 ))')

#------------------------------------------------------------------------------------------------
# FILE TRANSFER CONFIGURATION
#------------------------------------------------------------------------------------------------
FT_EXTENSION ?= root
FT_PREFIX ?= test
FT_RATE ?= 1
FT_SOCKETS ?= 4
FT_TIMEOUT ?= 7000
FT_THREADS ?= 4
FT_NUMFILES ?= 25
FT_FILESIZE ?= 300

DATA_DIR ?= $(SCRATCH)/storage/ejfat_ft/data
DATA_RX_DIR ?= $(SCRATCH)/storage/ejfat_ft/data_rx

#------------------------------------------------------------------------------------------------
# MONITORING CONFIGURATION
#------------------------------------------------------------------------------------------------
MONITOR_PORTS ?= 10000-10015
MONITOR_INTERVAL ?= 0.1

#------------------------------------------------------------------------------------------------
# LOAD BALANCER CONFIGURATION
#------------------------------------------------------------------------------------------------
LB_RESERVE_DURATION ?= 5
LB_NAME ?= yk_testing

#------------------------------------------------------------------------------------------------
# LOGGING CONFIGURATION
#------------------------------------------------------------------------------------------------
LOG_DIR ?= ./

#------------------------------------------------------------------------------------------------
# REMOTE EXECUTION CONFIGURATION
#------------------------------------------------------------------------------------------------
NODE ?=
DATA_PATH ?= /data

#------------------------------------------------------------------------------------------------
# MAKEFILE TARGETS
#------------------------------------------------------------------------------------------------

test :
	@echo "MY_IP: $(MY_IP)"
	@echo "MY_INTERFACE: $(MY_INTERFACE)"
	@echo "LB_IP: $(LB_IP)"
	@echo "SCRATCH: $(SCRATCH)"
	@echo "IP_VERSION: $(IP_VERSION)"

help :
	@echo "================================================================================================"
	@echo "EJFAT Perlmutter Makefile - Load Balancer and Data Transfer Demo"
	@echo "================================================================================================"
	@echo ""
	@echo "USAGE:"
	@echo "  make <target> [VAR=value ...]"
	@echo ""
	@echo "MAIN TARGETS:"
	@echo "  help              Display this help message"
	@echo "  build             Build the e2sar_dev container image"
	@echo "  reserve           Reserve a load balancer instance (saves to INSTANCE_URI file)"
	@echo "  free              Free the current load balancer reservation"
	@echo "  test              Display current network and configuration variables"
	@echo ""
	@echo "DATA TRANSFER TARGETS:"
	@echo "  send              Send test data through the load balancer"
	@echo "  receive           Receive data from the load balancer"
	@echo "  send_file         Send files through the load balancer"
	@echo "  receive_file      Receive files from the load balancer"
	@echo "  gen_test_files    Generate test files for file transfer"
	@echo "  monitor           Monitor load balancer statistics"
	@echo ""
	@echo "COMMON USAGE EXAMPLES:"
	@echo "  # Build container and reserve load balancer"
	@echo "  make build"
	@echo "  make reserve EJFAT_URI_BETA=<your-uri>"
	@echo ""
	@echo "  # Send/receive data (in separate terminals)"
	@echo "  make receive RX_DURATION=60"
	@echo "  make send TX_RATE=1.0 NFRAMES=5000"
	@echo ""
	@echo "  # Remote execution on compute node"
	@echo "  make receive NODE=nid001234"
	@echo "  make send NODE=nid001234"
	@echo ""
	@echo "  # File transfer workflow"
	@echo "  make gen_test_files FT_NUMFILES=10 FT_FILESIZE=100"
	@echo "  make receive_file"
	@echo "  make send_file FT_RATE=2.0"
	@echo ""
	@echo "  # Use IPv4 instead of IPv6"
	@echo "  make send IP_VERSION=-4"
	@echo ""
	@echo "  # Free reservation when done"
	@echo "  make free"
	@echo ""
	@echo "KEY CONFIGURATION VARIABLES:"
	@echo "  IP_VERSION        IP version (-4 or -6, default: -6)"
	@echo "  NODE              Remote node for SSH execution (default: local containerized)"
	@echo "  RX_DURATION       Receiver duration in seconds (default: 120)"
	@echo "  TX_RATE           Transmit rate in Gbps (default: 0.1)"
	@echo "  NFRAMES           Number of frames to send (default: 10000)"
	@echo "  FT_RATE           File transfer rate (default: 1)"
	@echo "  FT_NUMFILES       Number of test files (default: 25)"
	@echo "  FT_FILESIZE       Test file size in MB (default: 300)"
	@echo "  LOG_DIR           Directory for log files (default: ./)"
	@echo ""
	@echo "For complete variable documentation, see lines 13-67 in the Makefile."
	@echo ""
	@echo "EXECUTION MODES:"
	@echo "  1. Local containerized: Default mode, runs in podman-hpc container"
	@echo "     Example: make receive"
	@echo ""
	@echo "  2. Remote SSH: Set NODE variable to execute on compute node via SSH"
	@echo "     Example: make receive NODE=nid001234"
	@echo ""
	@echo "For detailed command help, run:"
	podman-hpc run \
		-v ./:/ejfat_demos/perlmutter \
		--network host --rm -it --entrypoint= \
		e2sar_dev /ejfat_demos/perlmutter/help
	@echo "================================================================================================"

build :
	cd .. ; podman-hpc build -t e2sar_dev:latest -f Containerfile.perlmutter
	podman-hpc migrate e2sar_dev:latest

reserve :
	podman-hpc run --cap-add=NET_RAW --cap-add=NET_ADMIN \
		-v ./:/ejfat_demos/perlmutter \
		--env EJFAT_URI_BETA=$(EJFAT_URI_BETA) \
		--env IP_VERSION=$(IP_VERSION) \
		--env LB_RESERVE_DURATION=$(LB_RESERVE_DURATION) \
		--env LB_NAME=$(LB_NAME) \
		--network host --rm -it --entrypoint= \
		e2sar_dev /ejfat_demos/perlmutter/reserve | grep "EJFAT_URI" >  ./INSTANCE_URI

receive :
ifeq ($(NODE),)
	podman-hpc run \
		--cap-add SYS_NICE \
		-v ./:/ejfat_demos/perlmutter \
		--env LOG_DIR=$(LOG_DIR) \
		--env EJFAT_URI=$(INSTANCE_URI) \
		--env IP_VERSION=$(IP_VERSION) \
		--env MY_INTERFACE=$(MY_INTERFACE) \
		--env RX_DURATION=$(RX_DURATION) \
		--env RX_THREADS=$(RX_THREADS) \
		--env RX_BUFSIZE=$(RX_BUFSIZE) \
		--env RX_TIMEOUT=$(RX_TIMEOUT) \
		--env RX_CORES=$(RX_CORES) \
		--env RX_DEQ=$(RX_DEQ) \
		--env MONITOR_PORTS=$(MONITOR_PORTS) \
		--env MONITOR_INTERVAL=$(MONITOR_INTERVAL) \
		--network host --rm -it --entrypoint= \
		e2sar_dev /ejfat_demos/perlmutter/receive
else
	IP_VERSION=$(IP_VERSION) \
	LOG_DIR=$(LOG_DIR) \
	RX_DURATION=$(RX_DURATION) \
	RX_BUFSIZE=$(RX_BUFSIZE) \
	RX_TIMEOUT=$(RX_TIMEOUT) \
	RX_CORES=$(RX_CORES) \
	RX_DEQ=$(RX_DEQ) \
	MONITOR_PORTS=$(MONITOR_PORTS) \
	MONITOR_INTERVAL=$(MONITOR_INTERVAL) \
	./receive --node $(NODE)
endif

send :
ifeq ($(NODE),)
	podman-hpc run \
		-v ./:/ejfat_demos/perlmutter \
		--env EJFAT_URI=$(INSTANCE_URI) \
		--env IP_VERSION=$(IP_VERSION) \
		--env SEND_SOCKETS=$(SEND_SOCKETS) \
		--env NFRAMES=$(NFRAMES) \
		--env TX_RATE=$(TX_RATE) \
		--env TX_LENGTH=$(TX_LENGTH) \
		--env DATA_ID=$(DATA_ID) \
		--network host --rm -it --entrypoint= \
		e2sar_dev /ejfat_demos/perlmutter/send
else
	IP_VERSION=$(IP_VERSION) \
	LOG_DIR=$(LOG_DIR) \
	TX_RATE=$(TX_RATE) \
	TX_LENGTH=$(TX_LENGTH) \
	NFRAMES=$(NFRAMES) \
	SEND_SOCKETS=$(SEND_SOCKETS) \
	DATA_ID=$(DATA_ID) \
	./send --node $(NODE)
endif

gen_test_files :
	podman-hpc run \
		-v ./:/ejfat_demos/perlmutter \
		--env FT_FILESIZE=$(FT_FILESIZE) \
		--env FT_PREFIX=$(FT_PREFIX) \
		--env FT_EXTENSION=$(FT_EXTENSION) \
		--env FT_NUMFILES=$(FT_NUMFILES) \
		--rm --network host -v $(DATA_DIR):/data \
		e2sar_dev generate-random-files.sh -s $(FT_FILESIZE) -p $(FT_PREFIX) -e $(FT_EXTENSION) -d /data -n $(FT_NUMFILES)

receive_file :
ifeq ($(NODE),)
	-rm -r $(DATA_RX_DIR)
	mkdir -p $(DATA_RX_DIR)
	podman-hpc run \
		-v ./:/ejfat_demos/perlmutter \
		--env EJFAT_URI=$(INSTANCE_URI) \
		--env IP_VERSION=$(IP_VERSION) \
		--env FT_EXTENSION=$(FT_EXTENSION) \
		--env FT_PREFIX=$(FT_PREFIX) \
		--env FT_TIMEOUT=$(FT_TIMEOUT) \
		--env FT_THREADS=$(FT_THREADS) \
		-v $(DATA_RX_DIR):/data \
		--network host --rm -it  --entrypoint= \
		e2sar_dev /ejfat_demos/perlmutter/receive_file
else
	IP_VERSION=$(IP_VERSION) \
	LOG_DIR=$(LOG_DIR) \
	FT_EXTENSION=$(FT_EXTENSION) \
	FT_PREFIX=$(FT_PREFIX) \
	FT_TIMEOUT=$(FT_TIMEOUT) \
	FT_THREADS=$(FT_THREADS) \
	DATA_PATH=$(DATA_PATH) \
	./receive_file --node $(NODE)
endif

send_file :
ifeq ($(NODE),)
	podman-hpc run \
		-v ./:/ejfat_demos/perlmutter \
		--env EJFAT_URI=$(INSTANCE_URI) \
		--env IP_VERSION=$(IP_VERSION) \
		--env NFRAMES=$(NFRAMES) \
		--env SEND_SOCKETS=$(FT_SOCKETS) \
		--env FT_EXTENSION=$(FT_EXTENSION) \
		--env FT_RATE=$(FT_RATE) \
		-v $(DATA_DIR):/data \
		--network host --rm -it --entrypoint= \
		e2sar_dev /ejfat_demos/perlmutter/send_file
else
	IP_VERSION=$(IP_VERSION) \
	LOG_DIR=$(LOG_DIR) \
	FT_EXTENSION=$(FT_EXTENSION) \
	FT_RATE=$(FT_RATE) \
	SEND_SOCKETS=$(FT_SOCKETS) \
	DATA_PATH=$(DATA_PATH) \
	./send_file --node $(NODE)
endif

monitor :
	podman-hpc run \
		-v ./:/ejfat_demos/perlmutter \
		--env EJFAT_URI=$(INSTANCE_URI) \
		--env IP_VERSION=$(IP_VERSION) \
		--network host --rm -it --entrypoint= \
		e2sar_dev /ejfat_demos/perlmutter/monitor

free :
	podman-hpc run \
		-v ./:/ejfat_demos/perlmutter \
		--env EJFAT_URI=$(INSTANCE_URI) \
		--env IP_VERSION=$(IP_VERSION) \
		--network host --rm -it --entrypoint= \
		e2sar_dev /ejfat_demos/perlmutter/free
