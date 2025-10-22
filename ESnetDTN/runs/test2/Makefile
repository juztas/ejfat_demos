#
# Makefile for ESnetDTN Operations
#
# This Makefile provides targets for managing EJFAT load balancer operations
# across multiple DTN nodes.
#
#------------------------------------------------------------------------------------------------

# List of DTN nodes (in priority order)
DTN_LIST := wash-dtn1-mgt.es.net sunn-dtn1-mgt.es.net star-dtn1-mgt.es.net

# Get the first DTN from the list
PRIMARY_DTN := $(word 1,$(DTN_LIST))

# Path to scripts relative to this Makefile
# This same relative path works on both local and remote nodes
SCRIPT_DIR := ../../../scripts

# Default EJFAT_URI_BETA (can be overridden via environment or command line)
EJFAT_URI_BETA ?=

# Load balancer configuration
LB_NAME ?= yk_testing
LB_RESERVE_DURATION ?= 5
IP_VERSION ?= 6

# Receiver configuration
RECEIVER_CONFIG ?= receiver_config.yaml
RECEIVER_LOG_DIR ?= run_output

# Sender configuration
SENDER_CONFIG ?= sender_config.yaml
SENDER_LOG_DIR ?= run_output

# Determine remote working directory dynamically based on current location
# This makes the Makefile relocatable within the ejfat_demos directory tree
# On remote nodes, ejfat_demos is located under the user's home directory
CURRENT_DIR := $(shell pwd)
RELATIVE_PATH := $(shell echo $(CURRENT_DIR) | sed 's|.*/ejfat_demos/||')
REMOTE_WORK_DIR := ~/ejfat_demos/$(RELATIVE_PATH)

.PHONY: help reserve free receive send run

#------------------------------------------------------------------------------------------------
# TARGETS
#------------------------------------------------------------------------------------------------

help:
	@echo "========================================================================"
	@echo "ESnetDTN Operations Makefile"
	@echo "========================================================================"
	@echo ""
	@echo "TARGETS:"
	@echo "  help              Display this help message"
	@echo "  reserve           Reserve a load balancer on primary DTN"
	@echo "  free              Free the load balancer on primary DTN"
	@echo "  receive           Start receivers on all DTN nodes"
	@echo "  send              Start sender on primary DTN"
	@echo "  run               Run complete workflow: reserve, receive, send"
	@echo ""
	@echo "CONFIGURATION:"
	@echo "  DTN_LIST:         $(DTN_LIST)"
	@echo "  PRIMARY_DTN:      $(PRIMARY_DTN)"
	@echo "  SCRIPT_DIR:       $(SCRIPT_DIR)"
	@echo "  REMOTE_WORK_DIR:  $(REMOTE_WORK_DIR)"
	@echo ""
	@echo "VARIABLES:"
	@echo "  EJFAT_URI_BETA    Base URI for load balancer service (required)"
	@echo "  LB_NAME           Load balancer name (default: $(LB_NAME))"
	@echo "  LB_RESERVE_DURATION  Reserve duration in days (default: $(LB_RESERVE_DURATION))"
	@echo "  IP_VERSION        IP version: 4 or 6 (default: $(IP_VERSION))"
	@echo "  RECEIVER_CONFIG   Receiver config file (default: $(RECEIVER_CONFIG))"
	@echo "  RECEIVER_LOG_DIR  Receiver log directory (default: $(RECEIVER_LOG_DIR))"
	@echo "  SENDER_CONFIG     Sender config file (default: $(SENDER_CONFIG))"
	@echo "  SENDER_LOG_DIR    Sender log directory (default: $(SENDER_LOG_DIR))"
	@echo ""
	@echo "USAGE:"
	@echo "  make reserve EJFAT_URI_BETA=ejfat://useless@192.168.100.1:18347/lb/1"
	@echo "  make reserve EJFAT_URI_BETA=\$$EJFAT_URI_BETA LB_NAME=my_test"
	@echo "  make free"
	@echo "  make free IP_VERSION=4"
	@echo "  make receive"
	@echo "  make receive RECEIVER_CONFIG=custom_config.yaml"
	@echo "  make send"
	@echo "  make send SENDER_CONFIG=custom_sender_config.yaml"
	@echo ""
	@echo "========================================================================"

reserve:
	@if [ -z "$(EJFAT_URI_BETA)" ]; then \
		echo "Error: EJFAT_URI_BETA is required."; \
		echo "Usage: make reserve EJFAT_URI_BETA=ejfat://..."; \
		exit 1; \
	fi
	@echo "========================================================================"
	@echo "Reserving Load Balancer on $(PRIMARY_DTN)"
	@echo "========================================================================"
	@echo "EJFAT_URI_BETA:      $(EJFAT_URI_BETA)"
	@echo "LB Name:             $(LB_NAME)"
	@echo "Reserve Duration:    $(LB_RESERVE_DURATION) days"
	@echo "IP Version:          IPv$(IP_VERSION)"
	@echo "Remote Work Dir:     $(REMOTE_WORK_DIR)"
	@echo "========================================================================"
	@echo ""
	@ssh -t $(PRIMARY_DTN) bash -i -c "'conda activate e2sar && \
		cd $(REMOTE_WORK_DIR) && \
		export EJFAT_URI_BETA=\"$(EJFAT_URI_BETA)\" && \
		export LB_NAME=\"$(LB_NAME)\" && \
		export LB_RESERVE_DURATION=\"$(LB_RESERVE_DURATION)\" && \
		export IP_VERSION=\"-$(IP_VERSION)\" && \
		export INSTANCE_URI_FILE=\"INSTANCE_URI\" && \
		$(SCRIPT_DIR)/reserve'"
	@echo ""
	@echo "Fetching INSTANCE_URI file from remote..."
	@scp $(PRIMARY_DTN):$(REMOTE_WORK_DIR)/INSTANCE_URI ./INSTANCE_URI
	@echo "========================================================================"
	@echo "Reservation complete! INSTANCE_URI saved locally."
	@echo "========================================================================"
	@cat INSTANCE_URI
	@echo ""

free:
	@echo "========================================================================"
	@echo "Freeing Load Balancer on $(PRIMARY_DTN)"
	@echo "========================================================================"
	@echo "IP Version:          IPv$(IP_VERSION)"
	@echo "Remote Work Dir:     $(REMOTE_WORK_DIR)"
	@echo "========================================================================"
	@echo ""
	@if [ -f INSTANCE_URI ]; then \
		echo "Found local INSTANCE_URI file, copying to remote..."; \
		cat INSTANCE_URI | ssh -t $(PRIMARY_DTN) "cat > $(REMOTE_WORK_DIR)/INSTANCE_URI"; \
		echo ""; \
	fi
	@ssh -t $(PRIMARY_DTN) bash -i -c "'conda activate e2sar && \
		cd $(REMOTE_WORK_DIR) && \
		if [ -f INSTANCE_URI ]; then \
			source INSTANCE_URI; \
		else \
			echo \"Error: INSTANCE_URI file not found. Cannot free load balancer.\"; \
			exit 1; \
		fi && \
		export IP_VERSION=\"-$(IP_VERSION)\" && \
		$(SCRIPT_DIR)/free'"
	@echo ""
	@echo "========================================================================"
	@echo "Load balancer freed successfully."
	@echo "========================================================================"
	@echo ""

receive:
	@echo "========================================================================"
	@echo "Starting Receivers on All DTN Nodes"
	@echo "========================================================================"
	@echo "DTN Nodes:           $(DTN_LIST)"
	@echo "Receiver Config:     $(RECEIVER_CONFIG)"
	@echo "Log Directory:       $(RECEIVER_LOG_DIR)"
	@echo "Remote Work Dir:     $(REMOTE_WORK_DIR)"
	@echo "========================================================================"
	@echo ""
	@if [ ! -f INSTANCE_URI ]; then \
		echo "Error: INSTANCE_URI file not found."; \
		echo "Please run 'make reserve' first to create the load balancer."; \
		exit 1; \
	fi
	@if [ ! -f $(RECEIVER_CONFIG) ]; then \
		echo "Error: Receiver config file not found: $(RECEIVER_CONFIG)"; \
		exit 1; \
	fi
	@echo "Creating log directory if needed..."
	@mkdir -p $(RECEIVER_LOG_DIR)
	@echo ""
	@echo "Starting receivers on all DTN nodes..."
	@i=0; \
	for node in $(DTN_LIST); do \
		log_file="rx_$$i.log"; \
		echo "------------------------------------------------------------------------"; \
		echo "Starting receiver $$i on $$node..."; \
		echo "  Log file: $(RECEIVER_LOG_DIR)/$$log_file"; \
		echo "  Copying config files to $$node..."; \
		cat INSTANCE_URI | ssh $$node "cat > $(REMOTE_WORK_DIR)/INSTANCE_URI"; \
		scp $(RECEIVER_CONFIG) $$node:$(REMOTE_WORK_DIR)/$(RECEIVER_CONFIG); \
		echo "  Starting receiver in background..."; \
		ssh -t $$node bash -i -c "'conda activate e2sar && \
			cd $(REMOTE_WORK_DIR) && \
			source INSTANCE_URI && \
			mkdir -p $(RECEIVER_LOG_DIR) && \
			export WORK_DIR=$(RECEIVER_LOG_DIR) && \
			nohup $(SCRIPT_DIR)/receive $(REMOTE_WORK_DIR)/$(RECEIVER_CONFIG) > $(RECEIVER_LOG_DIR)/$$log_file 2>&1 & \
			echo \"Receiver started in background (PID: \$$!)\"'"; \
		echo ""; \
		i=$$((i+1)); \
	done
	@echo "========================================================================"
	@echo "All receivers started successfully!"
	@echo "Receivers running on: $(DTN_LIST)"
	@echo "Log files on remote nodes: $(REMOTE_WORK_DIR)/$(RECEIVER_LOG_DIR)/rx_*.log"
	@echo "========================================================================"
	@echo ""

send:
	@echo "========================================================================"
	@echo "Starting Sender on Primary DTN"
	@echo "========================================================================"
	@echo "Primary DTN:         $(PRIMARY_DTN)"
	@echo "Sender Config:       $(SENDER_CONFIG)"
	@echo "Log Directory:       $(SENDER_LOG_DIR)"
	@echo "Remote Work Dir:     $(REMOTE_WORK_DIR)"
	@echo "========================================================================"
	@echo ""
	@if [ ! -f INSTANCE_URI ]; then \
		echo "Error: INSTANCE_URI file not found."; \
		echo "Please run 'make reserve' first to create the load balancer."; \
		exit 1; \
	fi
	@if [ ! -f $(SENDER_CONFIG) ]; then \
		echo "Error: Sender config file not found: $(SENDER_CONFIG)"; \
		exit 1; \
	fi
	@echo "Creating log directory if needed..."
	@mkdir -p $(SENDER_LOG_DIR)
	@echo ""
	@echo "Starting sender on $(PRIMARY_DTN)..."
	@echo "------------------------------------------------------------------------"
	@echo "Copying config files to $(PRIMARY_DTN)..."
	@cat INSTANCE_URI | ssh $(PRIMARY_DTN) "cat > $(REMOTE_WORK_DIR)/INSTANCE_URI"
	@scp $(SENDER_CONFIG) $(PRIMARY_DTN):$(REMOTE_WORK_DIR)/$(SENDER_CONFIG)
	@echo "Starting sender..."
	@ssh -t $(PRIMARY_DTN) bash -i -c "'conda activate e2sar && \
		cd $(REMOTE_WORK_DIR) && \
		source INSTANCE_URI && \
		mkdir -p $(SENDER_LOG_DIR) && \
		export WORK_DIR=$(SENDER_LOG_DIR) && \
		$(SCRIPT_DIR)/send $(REMOTE_WORK_DIR)/$(SENDER_CONFIG) | tee $(SENDER_LOG_DIR)/sender.log'"
	@echo ""
	@echo "Fetching sender log from remote..."
	@scp $(PRIMARY_DTN):$(REMOTE_WORK_DIR)/$(SENDER_LOG_DIR)/sender.log ./$(SENDER_LOG_DIR)/sender.log
	@echo "========================================================================"
	@echo "Sender completed successfully!"
	@echo "Log file saved locally: $(SENDER_LOG_DIR)/sender.log"
	@echo "========================================================================"
	@echo ""

run:
	@echo "========================================================================"
	@echo "Running Complete EJFAT Workflow"
	@echo "========================================================================"
	@echo ""
	@echo "Step 1: Reserving load balancer..."
	@echo "------------------------------------------------------------------------"
	@$(MAKE) reserve
	@echo ""
	@echo "========================================================================"
	@echo "Load Balancer Summary"
	@echo "========================================================================"
	@if [ -f INSTANCE_URI ]; then \
		cat INSTANCE_URI; \
	else \
		echo "Error: INSTANCE_URI not found"; \
		exit 1; \
	fi
	@echo "========================================================================"
	@echo ""
	@echo "Waiting 5 seconds before starting receivers..."
	@sleep 5
	@echo ""
	@echo "Step 2: Starting receivers on all DTN nodes..."
	@echo "------------------------------------------------------------------------"
	@$(MAKE) receive
	@echo ""
	@echo "Waiting 5 seconds for receivers to initialize..."
	@sleep 5
	@echo ""
	@echo "Step 3: Starting sender..."
	@echo "------------------------------------------------------------------------"
	@$(MAKE) send
	@echo ""
	@echo "========================================================================"
	@echo "Workflow Complete!"
	@echo "========================================================================"
	@echo ""
