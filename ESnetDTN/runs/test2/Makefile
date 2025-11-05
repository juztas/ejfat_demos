#
# Makefile for ESnetDTN Operations
#
# This Makefile provides targets for managing EJFAT load balancer operations
# across multiple DTN nodes.
#
#------------------------------------------------------------------------------------------------

# Available DTN hosts
HOSTS := cern773-dtn1-mgt.es.net \
         denv-dtn1-mgt.es.net \
         hous-dtn1-mgt.es.net \
         star-dtn1-mgt.es.net \
         sunn-dtn1-mgt.es.net \
         wash-dtn1-mgt.es.net

# List of DTN nodes for senders (in priority order)
SENDERS_LIST ?= wash-dtn1-mgt.es.net star-dtn1-mgt.es.net

# List of DTN nodes for receivers (in priority order)
RECEIVERS_LIST ?= wash-dtn1-mgt.es.net sunn-dtn1-mgt.es.net star-dtn1-mgt.es.net
# RECEIVERS_LIST ?= wash-dtn1-mgt.es.net

# Get the first DTN from the senders list for reservation operations
PRIMARY_DTN := $(word 1,$(SENDERS_LIST))

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

.PHONY: help reserve free receive send run tcpdump-commands retrieve-logs summarize-logs sync-scripts

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
	@echo "  receive           Start receivers on nodes in RECEIVERS_LIST"
	@echo "  send              Start senders on nodes in SENDERS_LIST"
	@echo "  run               Run complete workflow: reserve, receive, send"
	@echo "  retrieve-logs     Retrieve all logs and pcap files from remote nodes"
	@echo "  summarize-logs    Summarize all tx and rx logs from run_output directory"
	@echo "  sync-scripts      Update scripts on all nodes via git pull"
	@echo "  tcpdump-commands  Generate tcpdump commands for manual packet capture"
	@echo ""
	@echo "CONFIGURATION:"
	@echo "  SENDERS_LIST:     $(SENDERS_LIST)"
	@echo "  RECEIVERS_LIST:   $(RECEIVERS_LIST)"
	@echo "  PRIMARY_DTN:      $(PRIMARY_DTN)"
	@echo "  SCRIPT_DIR:       $(SCRIPT_DIR)"
	@echo "  REMOTE_WORK_DIR:  $(REMOTE_WORK_DIR)"
	@echo ""
	@echo "VARIABLES:"
	@echo "  HOSTS             Available DTN hosts (reference list)"
	@echo "                    $(HOSTS)"
	@echo "  SENDERS_LIST      Space-separated list of DTN nodes for senders"
	@echo "                    (default: $(SENDERS_LIST))"
	@echo "  RECEIVERS_LIST    Space-separated list of DTN nodes for receivers"
	@echo "                    (default: $(RECEIVERS_LIST))"
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
	@echo "  make receive RECEIVERS_LIST=\"wash-dtn1-mgt.es.net sunn-dtn1-mgt.es.net\""
	@echo "  make send"
	@echo "  make send SENDERS_LIST=\"wash-dtn1-mgt.es.net sunn-dtn1-mgt.es.net\""
	@echo "  make run SENDERS_LIST=\"wash-dtn1-mgt.es.net\" RECEIVERS_LIST=\"sunn-dtn1-mgt.es.net star-dtn1-mgt.es.net\""
	@echo "  make retrieve-logs"
	@echo "  make summarize-logs"
	@echo "  make sync-scripts"
	@echo "  make tcpdump-commands"
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
	@echo "Starting Receivers on DTN Nodes"
	@echo "========================================================================"
	@echo "Receiver Nodes:      $(RECEIVERS_LIST)"
	@echo "Receiver Config:     $(RECEIVER_CONFIG)"
	@echo "Log Directory:       $(RECEIVER_LOG_DIR)"
	@echo "Remote Work Dir:     $(REMOTE_WORK_DIR)"
	@if [ -n "$(RUN_ID)" ]; then \
		echo "Run ID:              $(RUN_ID)"; \
	fi
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
	@echo "Archiving receiver config to local run_output..."
	@cp $(RECEIVER_CONFIG) $(RECEIVER_LOG_DIR)/$(RECEIVER_CONFIG).archive
	@echo "  ✓ $(RECEIVER_CONFIG) saved to $(RECEIVER_LOG_DIR)/$(RECEIVER_CONFIG).archive"
	@echo ""
	@echo "Starting receivers on all receiver nodes..."
	@i=0; \
	for node in $(RECEIVERS_LIST); do \
		log_file="rx_$$i.log"; \
		hostname=$$(echo $$node | cut -d'-' -f1); \
		echo "------------------------------------------------------------------------"; \
		echo "Starting receiver $$i on $$node..."; \
		echo "  Log file: $(RECEIVER_LOG_DIR)/$$log_file"; \
		echo "  RX Index: $$i"; \
		echo "  Copying config files to $$node..."; \
		cat INSTANCE_URI | ssh $$node "cat > $(REMOTE_WORK_DIR)/INSTANCE_URI"; \
		scp $(RECEIVER_CONFIG) $$node:$(REMOTE_WORK_DIR)/$(RECEIVER_LOG_DIR)/$(RECEIVER_CONFIG)_$$hostname; \
		echo "  Starting receiver in background..."; \
		ssh -t $$node bash -i -c "'conda activate e2sar && \
			cd $(REMOTE_WORK_DIR) && \
			source INSTANCE_URI && \
			mkdir -p $(RECEIVER_LOG_DIR) && \
			export WORK_DIR=$(RECEIVER_LOG_DIR) && \
			export RUN_ID=\"$(RUN_ID)\" && \
			nohup $(SCRIPT_DIR)/receive --rx-index $$i $(REMOTE_WORK_DIR)/$(RECEIVER_LOG_DIR)/$(RECEIVER_CONFIG)_$$hostname > $(RECEIVER_LOG_DIR)/$$log_file 2>&1 & \
			echo \"Receiver started in background (PID: \$$!)\"'"; \
		echo ""; \
		i=$$((i+1)); \
	done
	@echo "========================================================================"
	@echo "All receivers started successfully!"
	@echo "Receivers running on: $(RECEIVERS_LIST)"
	@echo "Log files on remote nodes: $(REMOTE_WORK_DIR)/$(RECEIVER_LOG_DIR)/rx_*.log"
	@echo "========================================================================"
	@echo ""

send:
	@echo "========================================================================"
	@echo "Starting Senders on DTN Nodes"
	@echo "========================================================================"
	@echo "Sender Nodes:        $(SENDERS_LIST)"
	@echo "Sender Config:       $(SENDER_CONFIG)"
	@echo "Log Directory:       $(SENDER_LOG_DIR)"
	@echo "Remote Work Dir:     $(REMOTE_WORK_DIR)"
	@if [ -n "$(RUN_ID)" ]; then \
		echo "Run ID:              $(RUN_ID)"; \
	fi
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
	@echo "Archiving sender config to local run_output..."
	@cp $(SENDER_CONFIG) $(SENDER_LOG_DIR)/$(SENDER_CONFIG).archive
	@echo "  ✓ $(SENDER_CONFIG) saved to $(SENDER_LOG_DIR)/$(SENDER_CONFIG).archive"
	@echo ""
	@echo "Starting senders on all sender nodes..."
	@i=0; \
	for node in $(SENDERS_LIST); do \
		log_file="tx_$$i.log"; \
		data_id=$$((100 + i)); \
		hostname=$$(echo $$node | cut -d'-' -f1); \
		echo "------------------------------------------------------------------------"; \
		echo "Starting sender $$i on $$node..."; \
		echo "  Log file: $(SENDER_LOG_DIR)/$$log_file"; \
		echo "  Data ID:  $$data_id"; \
		echo "  Copying config files to $$node..."; \
		cat INSTANCE_URI | ssh $$node "cat > $(REMOTE_WORK_DIR)/INSTANCE_URI"; \
		scp $(SENDER_CONFIG) $$node:$(REMOTE_WORK_DIR)/$(SENDER_LOG_DIR)/$(SENDER_CONFIG)_$$hostname; \
		echo "  Modifying config to set data_id: $$data_id"; \
		ssh $$node "sed 's/^# data_id:.*/data_id: $$data_id/' $(REMOTE_WORK_DIR)/$(SENDER_LOG_DIR)/$(SENDER_CONFIG)_$$hostname > $(REMOTE_WORK_DIR)/$(SENDER_LOG_DIR)/$(SENDER_CONFIG)_$$hostname.tmp && mv $(REMOTE_WORK_DIR)/$(SENDER_LOG_DIR)/$(SENDER_CONFIG)_$$hostname.tmp $(REMOTE_WORK_DIR)/$(SENDER_LOG_DIR)/$(SENDER_CONFIG)_$$hostname"; \
		echo "  Starting sender in background..."; \
		ssh -t $$node bash -i -c "'conda activate e2sar && \
			cd $(REMOTE_WORK_DIR) && \
			source INSTANCE_URI && \
			mkdir -p $(SENDER_LOG_DIR) && \
			export WORK_DIR=$(SENDER_LOG_DIR) && \
			export RUN_ID=\"$(RUN_ID)\" && \
			nohup $(SCRIPT_DIR)/send $(REMOTE_WORK_DIR)/$(SENDER_LOG_DIR)/$(SENDER_CONFIG)_$$hostname > $(SENDER_LOG_DIR)/$$log_file 2>&1 & \
			echo \"Sender started in background (PID: \$$!)\"'"; \
		echo ""; \
		i=$$((i+1)); \
	done
	@echo "========================================================================"
	@echo "All senders started successfully!"
	@echo "Senders running on: $(SENDERS_LIST)"
	@echo "Log files on remote nodes: $(REMOTE_WORK_DIR)/$(SENDER_LOG_DIR)/tx_*.log"
	@echo "========================================================================"
	@echo ""

run:
	@echo "========================================================================"
	@echo "Running Complete EJFAT Workflow"
	@echo "========================================================================"
	@echo ""
	@RUN_ID=$$(date +"%Y%m%d_%H%M%S"); \
	export RUN_ID; \
	echo "Run ID: $$RUN_ID"; \
	echo "$$RUN_ID" > RUN_ID; \
	echo ""; \
	echo "Step 1: Reserving load balancer..."; \
	echo "------------------------------------------------------------------------"; \
	$(MAKE) reserve; \
	export RUN_ID=$$RUN_ID; \
	echo ""; \
	echo "========================================================================"; \
	echo "Load Balancer Summary"; \
	echo "========================================================================"; \
	if [ -f INSTANCE_URI ]; then \
		cat INSTANCE_URI; \
	else \
		echo "Error: INSTANCE_URI not found"; \
		exit 1; \
	fi; \
	echo "========================================================================"; \
	echo ""; \
	echo "Waiting 5 seconds before starting receivers..."; \
	sleep 5; \
	echo ""; \
	echo "Step 2: Starting receivers on all DTN nodes..."; \
	echo "------------------------------------------------------------------------"; \
	$(MAKE) receive RUN_ID=$$RUN_ID; \
	echo ""; \
	echo "Waiting 5 seconds for receivers to initialize..."; \
	sleep 5; \
	echo ""; \
	echo "Step 3: Starting sender..."; \
	echo "------------------------------------------------------------------------"; \
	$(MAKE) send RUN_ID=$$RUN_ID; \
	echo ""; \
	echo "========================================================================"; \
	echo "Workflow Started Successfully!"; \
	echo "========================================================================"; \
	echo ""; \
	echo "Run ID:              $$RUN_ID"; \
	echo "Receivers running on: $(RECEIVERS_LIST)"; \
	echo "Senders running on:   $(SENDERS_LIST)"; \
	echo ""; \
	echo "Remote log directories:"; \
	echo "  Receiver logs: $(REMOTE_WORK_DIR)/$(RECEIVER_LOG_DIR)/"; \
	echo "  Sender logs:   $(REMOTE_WORK_DIR)/$(SENDER_LOG_DIR)/"; \
	echo ""; \
	echo "========================================================================"; \
	echo "NEXT STEPS:"; \
	echo "========================================================================"; \
	echo ""; \
	echo "1. Monitor the test progress on remote nodes (optional)"; \
	echo "   ssh <node> 'tail -f $(REMOTE_WORK_DIR)/$(RECEIVER_LOG_DIR)/rx_*.log'"; \
	echo ""; \
	echo "2. Wait for the test to complete"; \
	echo "   - Receivers will run for the configured duration (rx_duration)"; \
	echo "   - Sender will complete when all frames are sent"; \
	echo ""; \
	echo "3. Retrieve logs when ready:"; \
	echo "   make retrieve-logs"; \
	echo ""; \
	echo "========================================================================"; \
	echo ""

tcpdump-commands:
	@echo "========================================================================"
	@echo "Generating tcpdump Commands"
	@echo "========================================================================"
	@if [ ! -f INSTANCE_URI ]; then \
		echo "Error: INSTANCE_URI file not found."; \
		echo "Please run 'make reserve' first to create the load balancer."; \
		exit 1; \
	fi
	@if [ ! -f $(RECEIVER_CONFIG) ]; then \
		echo "Error: Receiver config file not found: $(RECEIVER_CONFIG)"; \
		exit 1; \
	fi
	@$(SCRIPT_DIR)/generate_tcpdump_commands.sh $(RECEIVER_CONFIG) INSTANCE_URI $(RECEIVERS_LIST)

retrieve-logs:
	@echo "========================================================================"
	@echo "Retrieving Logs from Remote Nodes"
	@echo "========================================================================"
	@echo "Creating local log directories..."
	@mkdir -p $(RECEIVER_LOG_DIR)
	@mkdir -p $(SENDER_LOG_DIR)
	@echo ""
	@echo "Fetching receiver logs from all receiver nodes..."
	@i=0; \
	for node in $(RECEIVERS_LIST); do \
		echo "------------------------------------------------------------------------"; \
		echo "Fetching logs from $$node (receiver $$i)..."; \
		scp $$node:$(REMOTE_WORK_DIR)/$(RECEIVER_LOG_DIR)/rx_$$i.log ./$(RECEIVER_LOG_DIR)/rx_$$i.log 2>/dev/null && \
			echo "  ✓ rx_$$i.log retrieved" || \
			echo "  ✗ rx_$$i.log not found on $$node"; \
		scp $$node:$(REMOTE_WORK_DIR)/$(RECEIVER_LOG_DIR)/*_rx_csvfile.csv ./$(RECEIVER_LOG_DIR)/ 2>/dev/null && \
			echo "  ✓ CSV files retrieved from $$node" || \
			echo "  ✗ No CSV files found on $$node"; \
		scp $$node:$(REMOTE_WORK_DIR)/$(RECEIVER_LOG_DIR)/rx_$$i.pcap ./$(RECEIVER_LOG_DIR)/rx_$$i.pcap 2>/dev/null && \
			echo "  ✓ rx_$$i.pcap retrieved ($(shell du -h ./$(RECEIVER_LOG_DIR)/rx_$$i.pcap 2>/dev/null | awk '{print $$1}'))" || \
			echo "  ✗ No PCAP file found on $$node"; \
		i=$$((i+1)); \
		echo ""; \
	done
	@echo "Fetching sender logs from all sender nodes..."
	@i=0; \
	for node in $(SENDERS_LIST); do \
		echo "------------------------------------------------------------------------"; \
		echo "Fetching logs from $$node (sender $$i)..."; \
		scp $$node:$(REMOTE_WORK_DIR)/$(SENDER_LOG_DIR)/tx_$$i.log ./$(SENDER_LOG_DIR)/tx_$$i.log 2>/dev/null && \
			echo "  ✓ tx_$$i.log retrieved" || \
			echo "  ✗ tx_$$i.log not found on $$node"; \
		i=$$((i+1)); \
		echo ""; \
	done
	@echo "Fetching YAML and INI config files..."
	@i=0; \
	for node in $(SENDERS_LIST); do \
		hostname=$$(echo $$node | cut -d'-' -f1); \
		scp $$node:$(REMOTE_WORK_DIR)/$(SENDER_LOG_DIR)/$(SENDER_CONFIG)_$$hostname ./$(SENDER_LOG_DIR)/$(SENDER_CONFIG)_$$hostname 2>/dev/null && \
			echo "  ✓ $(SENDER_CONFIG)_$$hostname retrieved from $$node" || \
			echo "  ✗ $(SENDER_CONFIG)_$$hostname not found on $$node"; \
		scp $$node:$(REMOTE_WORK_DIR)/$(SENDER_LOG_DIR)/segmenter_config.ini ./$(SENDER_LOG_DIR)/segmenter_config_$$hostname.ini 2>/dev/null && \
			echo "  ✓ segmenter_config.ini retrieved from $$node" || \
			echo "  ✗ segmenter_config.ini not found on $$node"; \
		i=$$((i+1)); \
	done
	@i=0; \
	for node in $(RECEIVERS_LIST); do \
		hostname=$$(echo $$node | cut -d'-' -f1); \
		scp $$node:$(REMOTE_WORK_DIR)/$(RECEIVER_LOG_DIR)/$(RECEIVER_CONFIG)_$$hostname ./$(RECEIVER_LOG_DIR)/$(RECEIVER_CONFIG)_$$hostname 2>/dev/null && \
			echo "  ✓ $(RECEIVER_CONFIG)_$$hostname retrieved from $$node" || \
			echo "  ✗ $(RECEIVER_CONFIG)_$$hostname not found on $$node"; \
		scp $$node:$(REMOTE_WORK_DIR)/$(RECEIVER_LOG_DIR)/reassembler_config.ini ./$(RECEIVER_LOG_DIR)/reassembler_config_$$hostname.ini 2>/dev/null && \
			echo "  ✓ reassembler_config.ini retrieved from $$node" || \
			echo "  ✗ reassembler_config.ini not found on $$node"; \
		i=$$((i+1)); \
	done
	@echo ""
	@echo "========================================================================"
	@echo "Log Retrieval Complete!"
	@echo "========================================================================"
	@echo "All logs saved to: $(RECEIVER_LOG_DIR)/ and $(SENDER_LOG_DIR)/"
	@echo ""
	@echo "Retrieved files:"
	@ls -lh $(RECEIVER_LOG_DIR)/*.log $(RECEIVER_LOG_DIR)/*.pcap $(RECEIVER_LOG_DIR)/*.csv $(SENDER_LOG_DIR)/*.log 2>/dev/null | awk '{printf "  %s %s %s\n", $$5, $$9, ""}'
	@echo ""
	@echo "Summary:"
	@echo "  RX logs:        $$(ls -1 $(RECEIVER_LOG_DIR)/rx_*.log 2>/dev/null | wc -l) files"
	@echo "  TX logs:        $$(ls -1 $(SENDER_LOG_DIR)/tx_*.log 2>/dev/null | wc -l) files"
	@echo "  CSV files:      $$(ls -1 $(RECEIVER_LOG_DIR)/*.csv 2>/dev/null | wc -l) files"
	@echo "  PCAP files:     $$(ls -1 $(RECEIVER_LOG_DIR)/*.pcap 2>/dev/null | wc -l) files"
	@echo "  YAML configs:   $$(ls -1 $(RECEIVER_LOG_DIR)/*_config_*.yaml $(SENDER_LOG_DIR)/*_config_*.yaml 2>/dev/null | wc -l) files"
	@echo "  INI configs:    $$(ls -1 $(RECEIVER_LOG_DIR)/reassembler_config_*.ini $(SENDER_LOG_DIR)/segmenter_config_*.ini 2>/dev/null | wc -l) files"
	@echo "  Archive YAMLs:  $$(ls -1 $(RECEIVER_LOG_DIR)/*.archive $(SENDER_LOG_DIR)/*.archive 2>/dev/null | wc -l) files"
	@echo "========================================================================"
	@echo ""

summarize-logs:
	@echo "========================================================================"
	@echo "Summarizing EJFAT Logs"
	@echo "========================================================================"
	@if [ ! -d $(RECEIVER_LOG_DIR) ]; then \
		echo "Error: Log directory '$(RECEIVER_LOG_DIR)' does not exist."; \
		echo "Please run 'make retrieve-logs' first to fetch logs from remote nodes."; \
		exit 1; \
	fi
	@if [ ! -f $(SCRIPT_DIR)/summarize_logs.py ]; then \
		echo "Error: summarize_logs.py script not found in $(SCRIPT_DIR)."; \
		exit 1; \
	fi
	@python3 $(SCRIPT_DIR)/summarize_logs.py $(RECEIVER_LOG_DIR)

sync-scripts:
	@echo "========================================================================"
	@echo "Syncing Scripts on Remote Nodes"
	@echo "========================================================================"
	@echo "This will run 'git pull' in ~/ejfat_demos on all nodes"
	@echo ""
	@echo "Nodes to update:"
	@all_nodes=""; \
	for node in $(SENDERS_LIST) $(RECEIVERS_LIST); do \
		if ! echo "$$all_nodes" | grep -q "$$node"; then \
			all_nodes="$$all_nodes $$node"; \
		fi; \
	done; \
	for node in $$all_nodes; do \
		echo "  - $$node"; \
	done
	@echo ""
	@all_nodes=""; \
	for node in $(SENDERS_LIST) $(RECEIVERS_LIST); do \
		if ! echo "$$all_nodes" | grep -q "$$node"; then \
			all_nodes="$$all_nodes $$node"; \
		fi; \
	done; \
	for node in $$all_nodes; do \
		echo "------------------------------------------------------------------------"; \
		echo "Updating $$node..."; \
		ssh $$node "cd ~/ejfat_demos && git pull" && \
			echo "  ✓ Successfully updated $$node" || \
			echo "  ✗ Failed to update $$node"; \
		echo ""; \
	done
	@echo "========================================================================"
	@echo "Script Sync Complete!"
	@echo "========================================================================"
	@echo ""
