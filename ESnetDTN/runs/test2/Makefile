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

HOSTS_tx := cern773-dtn1-mgt.es.net \
            denv-dtn1-mgt.es.net \
            hous-dtn1-mgt.es.net

HOSTS_rx := star-dtn1-mgt.es.net \
            wash-dtn1-mgt.es.net \
            sunn-dtn1-mgt.es.net \
	    sunn-dtn1-mgt.es.net

# Include host configuration from run_output directory
# This file defines SENDERS_LIST and RECEIVERS_LIST
-include run_output/Makefile.hosts

# Fallback defaults if Makefile.hosts is not found
SENDERS_LIST ?= $(HOSTS)
RECEIVERS_LIST ?= $(HOSTS_rx)

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

# Upload control - set to true to skip uploading config files (for fast restarts)
SKIP_UPLOADS ?= false

# Start time synchronization - offset in minutes from RUN_ID timestamp
START_OFFSET_MINUTES ?= 0

# Sender start delay - additional seconds to wait after receiver start time
# This gives receivers time to initialize before senders start transmitting
SENDER_START_DELAY_SECONDS ?= 10

# CPU monitor node - which DTN to run cpu-monitor on
CPU_MONITOR_NODE ?= $(PRIMARY_DTN)

# Determine remote working directory dynamically based on current location
# This makes the Makefile relocatable within the ejfat_demos directory tree
# On remote nodes, ejfat_demos is located under the user's home directory
CURRENT_DIR := $(shell pwd)
RELATIVE_PATH := $(shell echo $(CURRENT_DIR) | sed 's|.*/ejfat_demos/||')
REMOTE_WORK_DIR := ~/ejfat_demos/$(RELATIVE_PATH)

.PHONY: help reserve free overview cpu-monitor cpu-monitor-remote receive send run tcpdump-commands get-logs summarize-logs sync-scripts survey-hardware clean-run calculate-runtime kill-e2sar kill-receivers kill-senders

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
	@echo "  calculate-runtime Calculate expected experiment runtime and data volume"
	@echo "  reserve           Reserve a load balancer on primary DTN"
	@echo "  free              Free the load balancer on primary DTN"
	@echo "  overview          Monitor load balancer status (lbadm --overview)"
	@echo "  cpu-monitor       Monitor CPU usage across cores on remote node"
	@echo "  cpu-monitor-remote Monitor CPU remotely with local display (all DTNs by default)"
	@echo "  receive           Start receivers on nodes in RECEIVERS_LIST"
	@echo "  send              Start senders on nodes in SENDERS_LIST"
	@echo "  run               Run complete workflow: reserve, receive, send"
	@echo "  get-logs          Retrieve all logs and pcap files from remote nodes"
	@echo "  summarize-logs    Summarize all tx and rx logs from run_output directory"
	@echo "  clean-run         Remove all files from remote run_output directories"
	@echo "  sync-scripts      Update scripts on all nodes via git pull"
	@echo "  survey-hardware   Compare CPU hardware across all DTN nodes using lscpu"
	@echo "  tcpdump-commands  Generate tcpdump commands for manual packet capture"
	@echo "  kill-e2sar        Kill all e2sar processes on all HOSTS or specific node"
	@echo "  kill-receivers    Kill only receiver (e2sar_perf -recv) processes on nodes"
	@echo "  kill-senders      Kill only sender (e2sar_perf -send) processes on nodes"
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
	@echo "  SKIP_UPLOADS      Skip uploading config files: true or false (default: $(SKIP_UPLOADS))"
	@echo "  START_OFFSET_MINUTES  Minutes to add to RUN_ID for synchronized start (default: $(START_OFFSET_MINUTES))"
	@echo "  SENDER_START_DELAY_SECONDS  Additional seconds for senders to wait after receiver start (default: $(SENDER_START_DELAY_SECONDS))"
	@echo "  CPU_MONITOR_NODE  DTN node for cpu-monitor (single node)"
	@echo "  NODES             Space-separated list of DTN nodes for cpu-monitor-remote"
	@echo "                    If not specified, monitors all HOSTS (default)"
	@echo "  NODE              Specific node for kill-e2sar (default: all HOSTS)"
	@echo ""
	@echo "USAGE:"
	@echo "  make calculate-runtime"
	@echo "  make reserve EJFAT_URI_BETA=ejfat://useless@192.168.100.1:18347/lb/1"
	@echo "  make reserve EJFAT_URI_BETA=\$$EJFAT_URI_BETA LB_NAME=my_test"
	@echo "  make free"
	@echo "  make free IP_VERSION=4"
	@echo "  make overview EJFAT_URI_BETA=\$$EJFAT_URI_BETA"
	@echo "  make cpu-monitor"
	@echo "  make cpu-monitor CPU_MONITOR_NODE=star-dtn1-mgt.es.net"
	@echo "  make cpu-monitor-remote"
	@echo "  make cpu-monitor-remote NODES=\"star-dtn1-mgt.es.net wash-dtn1-mgt.es.net\""
	@echo "  make receive"
	@echo "  make receive RECEIVERS_LIST=\"wash-dtn1-mgt.es.net sunn-dtn1-mgt.es.net\""
	@echo "  make receive SKIP_UPLOADS=true"
	@echo "  make send"
	@echo "  make send SENDERS_LIST=\"wash-dtn1-mgt.es.net sunn-dtn1-mgt.es.net\""
	@echo "  make send SKIP_UPLOADS=true"
	@echo "  make run SENDERS_LIST=\"wash-dtn1-mgt.es.net\" RECEIVERS_LIST=\"sunn-dtn1-mgt.es.net star-dtn1-mgt.es.net\""
	@echo "  make run START_OFFSET_MINUTES=5"
	@echo "  make run SENDER_START_DELAY_SECONDS=30"
	@echo "  make get-logs"
	@echo "  make summarize-logs"
	@echo "  make clean-run"
	@echo "  make sync-scripts"
	@echo "  make survey-hardware"
	@echo "  make tcpdump-commands"
	@echo "  make kill-e2sar"
	@echo "  make kill-e2sar NODE=star-dtn1-mgt.es.net"
	@echo "  make kill-receivers NODES=\"star-dtn1-mgt.es.net wash-dtn1-mgt.es.net\""
	@echo "  make kill-senders NODES=\"cern773-dtn1-mgt.es.net denv-dtn1-mgt.es.net\""
	@echo ""
	@echo "========================================================================"

calculate-runtime:
	@echo "========================================================================"
	@echo "Calculating Experiment Runtime"
	@echo "========================================================================"
	@$(SCRIPT_DIR)/calculate_sender_duration --config $(SENDER_CONFIG) --makefile $(CURDIR)/Makefile

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

overview:
	@if [ -z "$(EJFAT_URI_BETA)" ]; then \
		echo "Error: EJFAT_URI_BETA is required."; \
		echo "Usage: make overview EJFAT_URI_BETA=ejfat://..."; \
		exit 1; \
	fi
	@echo "========================================================================"
	@echo "Load Balancer Overview Monitor"
	@echo "========================================================================"
	@echo "EJFAT_URI_BETA:      $(EJFAT_URI_BETA)"
	@echo "Running on:          $(PRIMARY_DTN)"
	@echo "Update interval:     1 second"
	@echo "IP Version:          IPv$(IP_VERSION)"
	@echo ""
	@echo "Press Ctrl-C to stop monitoring"
	@echo "========================================================================"
	@echo ""
	@ssh -t $(PRIMARY_DTN) bash -i -c "'conda activate e2sar && \
		cd $(REMOTE_WORK_DIR) && \
		export EJFAT_URI=\"$(EJFAT_URI_BETA)\" && \
		export IP_VERSION=\"-$(IP_VERSION)\" && \
		watch -n 1 $(SCRIPT_DIR)/overview'"

cpu-monitor:
	@echo "========================================================================"
	@echo "CPU Monitor"
	@echo "========================================================================"
	@echo "Running on:          $(CPU_MONITOR_NODE)"
	@echo ""
	@echo "Press Ctrl-C to stop monitoring"
	@echo "========================================================================"
	@echo ""
	@ssh -t $(CPU_MONITOR_NODE) bash -i -c "'conda activate e2sar && \
		cd $(REMOTE_WORK_DIR) && \
		python3 $(SCRIPT_DIR)/cpu_monitor.py'"

cpu-monitor-remote:
	@echo "========================================================================"
	@echo "CPU Monitor (Remote)"
	@echo "========================================================================"
	@if [ -n "$(NODES)" ]; then \
		TARGET_NODES="$(NODES)"; \
	else \
		TARGET_NODES="$(HOSTS)"; \
	fi; \
	echo "Monitoring:          $$TARGET_NODES"; \
	echo "Display:             Local"; \
	echo ""; \
	echo "Press Ctrl-C to stop monitoring"; \
	echo "========================================================================"; \
	echo ""; \
	python3 $(SCRIPT_DIR)/cpu_monitor_remote.py --host $$TARGET_NODES

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
	@if [ -n "$(START_TIME)" ]; then \
		echo "Target Start Time:   $$(date -u -d @$(START_TIME) +"%Y-%m-%d %H:%M:%S UTC" 2>/dev/null || date -u -r $(START_TIME) +"%Y-%m-%d %H:%M:%S UTC")"; \
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
	nodes_seen=""; \
	for node in $(RECEIVERS_LIST); do \
		log_file="rx_$$i.log"; \
		hostname=$$(echo $$node | cut -d'-' -f1); \
		ordinal=$$(echo " $$nodes_seen " | grep -o " $$node " | wc -l | tr -d ' '); \
		nodes_seen="$$nodes_seen $$node"; \
		echo "------------------------------------------------------------------------"; \
		echo "Starting receiver $$i on $$node..."; \
		echo "  Log file: $(RECEIVER_LOG_DIR)/$$log_file"; \
		echo "  RX Index: $$i"; \
		echo "  Ordinal:  $$ordinal ($$((ordinal + 1))th receiver on $$hostname)"; \
		echo "  Creating remote directories..."; \
		ssh $$node "mkdir -p $(REMOTE_WORK_DIR)/$(RECEIVER_LOG_DIR)"; \
		if [ "$(SKIP_UPLOADS)" != "true" ]; then \
			echo "  Copying config files to $$node..."; \
			cat INSTANCE_URI | ssh $$node "cat > $(REMOTE_WORK_DIR)/INSTANCE_URI"; \
			scp $(RECEIVER_CONFIG) $$node:$(REMOTE_WORK_DIR)/$(RECEIVER_LOG_DIR)/$(RECEIVER_CONFIG)_$$hostname; \
		else \
			echo "  Skipping uploads (SKIP_UPLOADS=true)..."; \
		fi; \
		echo "  Starting receiver in background..."; \
		ssh -t $$node bash -i -c "'conda activate e2sar && \
			cd $(REMOTE_WORK_DIR) && \
			source INSTANCE_URI && \
			mkdir -p $(RECEIVER_LOG_DIR) && \
			export WORK_DIR=$(RECEIVER_LOG_DIR) && \
			export RUN_ID=\"$(RUN_ID)\" && \
			export START_TIME=\"$(START_TIME)\" && \
			export RX_ORDINAL=$$ordinal && \
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
	@if [ -n "$(START_TIME)" ]; then \
		echo "Target Start Time:   $$(date -u -d @$(START_TIME) +"%Y-%m-%d %H:%M:%S UTC" 2>/dev/null || date -u -r $(START_TIME) +"%Y-%m-%d %H:%M:%S UTC")"; \
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
	nodes_seen=""; \
	for node in $(SENDERS_LIST); do \
		log_file="tx_$$i.log"; \
		data_id=$$((100 + i)); \
		hostname=$$(echo $$node | cut -d'-' -f1); \
		ordinal=$$(echo " $$nodes_seen " | grep -o " $$node " | wc -l | tr -d ' '); \
		nodes_seen="$$nodes_seen $$node"; \
		echo "------------------------------------------------------------------------"; \
		echo "Starting sender $$i on $$node..."; \
		echo "  Log file: $(SENDER_LOG_DIR)/$$log_file"; \
		echo "  Data ID:  $$data_id"; \
		echo "  Ordinal:  $$ordinal ($$((ordinal + 1))th sender on $$hostname)"; \
		echo "  Creating remote directories..."; \
		ssh $$node "mkdir -p $(REMOTE_WORK_DIR)/$(SENDER_LOG_DIR)"; \
		if [ "$(SKIP_UPLOADS)" != "true" ]; then \
			echo "  Copying config files to $$node..."; \
			cat INSTANCE_URI | ssh $$node "cat > $(REMOTE_WORK_DIR)/INSTANCE_URI"; \
			scp $(SENDER_CONFIG) $$node:$(REMOTE_WORK_DIR)/$(SENDER_LOG_DIR)/$(SENDER_CONFIG)_$$hostname; \
			echo "  Modifying config to set data_id: $$data_id"; \
			ssh $$node "sed 's/^# data_id:.*/data_id: $$data_id/' $(REMOTE_WORK_DIR)/$(SENDER_LOG_DIR)/$(SENDER_CONFIG)_$$hostname > $(REMOTE_WORK_DIR)/$(SENDER_LOG_DIR)/$(SENDER_CONFIG)_$$hostname.tmp && mv $(REMOTE_WORK_DIR)/$(SENDER_LOG_DIR)/$(SENDER_CONFIG)_$$hostname.tmp $(REMOTE_WORK_DIR)/$(SENDER_LOG_DIR)/$(SENDER_CONFIG)_$$hostname"; \
		else \
			echo "  Skipping uploads (SKIP_UPLOADS=true)..."; \
		fi; \
		echo "  Starting sender in background..."; \
		ssh -t $$node bash -i -c "'conda activate e2sar && \
			cd $(REMOTE_WORK_DIR) && \
			source INSTANCE_URI && \
			mkdir -p $(SENDER_LOG_DIR) && \
			export WORK_DIR=$(SENDER_LOG_DIR) && \
			export RUN_ID=\"$(RUN_ID)\" && \
			export START_TIME=\"$(START_TIME)\" && \
			export TX_ORDINAL=$$ordinal && \
			nohup $(SCRIPT_DIR)/send --tx-index $$i $(REMOTE_WORK_DIR)/$(SENDER_LOG_DIR)/$(SENDER_CONFIG)_$$hostname > $(SENDER_LOG_DIR)/$$log_file 2>&1 & \
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
	@mkdir -p $(RECEIVER_LOG_DIR)
	@RUN_ID=$$(date -u +"%Y%m%d_%H%M%S"); \
	export RUN_ID; \
	echo "Run ID: $$RUN_ID (UTC)"; \
	echo "$$RUN_ID" > $(RECEIVER_LOG_DIR)/RUN_ID; \
	if BASE_TIME=$$(date -u -d "$$RUN_ID" +"%s" 2>/dev/null); then \
		RX_START_TIME=$$((BASE_TIME + $(START_OFFSET_MINUTES) * 60)); \
	else \
		BASE_TIME=$$(date -u -j -f "%Y%m%d_%H%M%S" "$$RUN_ID" +%s 2>/dev/null); \
		RX_START_TIME=$$((BASE_TIME + $(START_OFFSET_MINUTES) * 60)); \
	fi; \
	TX_START_TIME=$$((RX_START_TIME + $(SENDER_START_DELAY_SECONDS))); \
	export RX_START_TIME; \
	export TX_START_TIME; \
	echo "Start offset: $(START_OFFSET_MINUTES) minutes"; \
	echo "Sender delay: $(SENDER_START_DELAY_SECONDS) seconds"; \
	echo "Receiver start time: $$(date -u -d @$$RX_START_TIME +"%Y-%m-%d %H:%M:%S UTC" 2>/dev/null || date -u -r $$RX_START_TIME +"%Y-%m-%d %H:%M:%S UTC")"; \
	echo "Sender start time:   $$(date -u -d @$$TX_START_TIME +"%Y-%m-%d %H:%M:%S UTC" 2>/dev/null || date -u -r $$TX_START_TIME +"%Y-%m-%d %H:%M:%S UTC") (+$(SENDER_START_DELAY_SECONDS)s)"; \
	echo "$$RX_START_TIME" > $(RECEIVER_LOG_DIR)/RX_START_TIME; \
	echo "$$TX_START_TIME" > $(RECEIVER_LOG_DIR)/TX_START_TIME; \
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
	$(MAKE) receive RUN_ID=$$RUN_ID START_TIME=$$RX_START_TIME; \
	echo ""; \
	echo "Waiting 5 seconds for receivers to initialize..."; \
	sleep 5; \
	echo ""; \
	echo "Step 3: Starting sender..."; \
	echo "------------------------------------------------------------------------"; \
	$(MAKE) send RUN_ID=$$RUN_ID START_TIME=$$TX_START_TIME; \
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
	echo "   make get-logs"; \
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
	@$(SCRIPT_DIR)/generate_tcpdump_commands.sh $(RECEIVER_CONFIG) INSTANCE_URI $(REMOTE_WORK_DIR) $(RECEIVER_LOG_DIR) $(RECEIVERS_LIST)

get-logs:
	@echo "========================================================================"
	@echo "Retrieving Logs from Remote Nodes (using rsync)"
	@echo "========================================================================"
	@echo "Creating local log directories..."
	@mkdir -p $(RECEIVER_LOG_DIR)
	@mkdir -p $(SENDER_LOG_DIR)
	@echo ""
	@echo "Syncing receiver logs from all receiver nodes..."
	@i=0; \
	for node in $(RECEIVERS_LIST); do \
		hostname=$$(echo $$node | cut -d'-' -f1); \
		echo "------------------------------------------------------------------------"; \
		echo "Syncing logs from $$node (receiver $$i, hostname: $$hostname)..."; \
		echo "  Running rsync..."; \
		rsync -avz --progress --stats --human-readable \
			--partial --partial-dir=.rsync-partial \
			--itemize-changes \
			--exclude="[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9][0-9][0-9]/" \
			--include="RUN_ID" \
			--include="rx_$$i.log" \
			--include="rx_$$i.pcap" \
			--include="rx_*_csvfile.csv" \
			--include="*_$$hostname.yaml" \
			--include="reassembler_config_rx_*.ini" \
			--exclude="*" \
			$$node:$(REMOTE_WORK_DIR)/$(RECEIVER_LOG_DIR)/ \
			./$(RECEIVER_LOG_DIR)/ 2>&1 | grep -E "(sent|received|speedup|rx_|csv|yaml|ini|RUN_ID|total size)" || true; \
		echo "  ✓ Sync complete for $$node"; \
		echo ""; \
		i=$$((i+1)); \
	done
	@echo "Syncing sender logs from all sender nodes..."
	@i=0; \
	for node in $(SENDERS_LIST); do \
		hostname=$$(echo $$node | cut -d'-' -f1); \
		echo "------------------------------------------------------------------------"; \
		echo "Syncing logs from $$node (sender $$i, hostname: $$hostname)..."; \
		echo "  Running rsync..."; \
		rsync -avz --progress --stats --human-readable \
			--partial --partial-dir=.rsync-partial \
			--itemize-changes \
			--exclude="[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9][0-9][0-9]/" \
			--include="tx_$$i.log" \
			--include="*_$$hostname.yaml" \
			--include="segmenter_config_tx_*.ini" \
			--exclude="*" \
			$$node:$(REMOTE_WORK_DIR)/$(SENDER_LOG_DIR)/ \
			./$(SENDER_LOG_DIR)/ 2>&1 | grep -E "(sent|received|speedup|tx_|yaml|ini|total size)" || true; \
		echo "  ✓ Sync complete for $$node"; \
		echo ""; \
		i=$$((i+1)); \
	done
	@echo ""
	@echo "========================================================================"
	@echo "Log Retrieval Complete!"
	@echo "========================================================================"
	@echo "All logs saved to: $(RECEIVER_LOG_DIR)/ and $(SENDER_LOG_DIR)/"
	@echo ""
	@echo "Retrieved files:"
	@ls -lh $(RECEIVER_LOG_DIR)/*.log $(RECEIVER_LOG_DIR)/*.pcap $(RECEIVER_LOG_DIR)/*.csv $(SENDER_LOG_DIR)/*.log 2>/dev/null | awk '{printf "  %s %s %s\n", $$5, $$9, ""}' || echo "  (no files found)"
	@echo ""
	@echo "Summary:"
	@echo "  RX logs:        $$(ls -1 $(RECEIVER_LOG_DIR)/rx_*.log 2>/dev/null | wc -l) files"
	@echo "  TX logs:        $$(ls -1 $(SENDER_LOG_DIR)/tx_*.log 2>/dev/null | wc -l) files"
	@echo "  Socket CSVs:    $$(ls -1 $(RECEIVER_LOG_DIR)/rx_*_csvfile.csv 2>/dev/null | wc -l) files"
	@echo "  PCAP files:     $$(ls -1 $(RECEIVER_LOG_DIR)/*.pcap 2>/dev/null | wc -l) files"
	@echo "  YAML configs:   $$(ls -1 $(RECEIVER_LOG_DIR)/*_config_*.yaml $(SENDER_LOG_DIR)/*_config_*.yaml 2>/dev/null | wc -l) files"
	@echo "  INI configs:    $$(ls -1 $(RECEIVER_LOG_DIR)/reassembler_config_rx_*.ini $(SENDER_LOG_DIR)/segmenter_config_tx_*.ini 2>/dev/null | wc -l) files"
	@echo "  Archive YAMLs:  $$(ls -1 $(RECEIVER_LOG_DIR)/*.archive $(SENDER_LOG_DIR)/*.archive 2>/dev/null | wc -l) files"
	@echo "========================================================================"
	@echo ""

summarize-logs:
	@echo "========================================================================"
	@echo "Summarizing EJFAT Logs"
	@echo "========================================================================"
	@if [ ! -d $(RECEIVER_LOG_DIR) ]; then \
		echo "Error: Log directory '$(RECEIVER_LOG_DIR)' does not exist."; \
		echo "Please run 'make get-logs' first to fetch logs from remote nodes."; \
		exit 1; \
	fi
	@if [ ! -f $(SCRIPT_DIR)/summarize_logs.py ]; then \
		echo "Error: summarize_logs.py script not found in $(SCRIPT_DIR)."; \
		exit 1; \
	fi
	@if [ ! -f $(RECEIVER_LOG_DIR)/RUN_ID ]; then \
		echo "Warning: RUN_ID file not found in $(RECEIVER_LOG_DIR)/. Using timestamp for output directory."; \
		RUN_ID=$$(date -u +"%Y%m%d_%H%M%S"); \
	else \
		RUN_ID=$$(cat $(RECEIVER_LOG_DIR)/RUN_ID); \
	fi; \
	echo "Run ID: $$RUN_ID"; \
	echo "Creating output directory: $(RECEIVER_LOG_DIR)/$$RUN_ID/"; \
	mkdir -p $(RECEIVER_LOG_DIR)/$$RUN_ID; \
	echo "Running log analysis..."; \
	python3 $(SCRIPT_DIR)/summarize_logs.py $(RECEIVER_LOG_DIR) > $(RECEIVER_LOG_DIR)/$$RUN_ID/log_summary.txt 2>&1; \
	echo ""; \
	echo "========================================================================";\
	echo "Summary saved to: $(RECEIVER_LOG_DIR)/$$RUN_ID/log_summary.txt"; \
	echo "========================================================================"; \
	echo ""; \
	echo "Displaying summary:"; \
	echo "------------------------------------------------------------------------"; \
	cat $(RECEIVER_LOG_DIR)/$$RUN_ID/log_summary.txt

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

survey-hardware:
	@echo "========================================================================"
	@echo "Surveying Hardware Across All DTN Nodes"
	@echo "========================================================================"
	@echo "Collecting system information from all hosts: $(HOSTS)"
	@echo ""
	@mkdir -p $(RECEIVER_LOG_DIR)
	@echo "Collecting lscpu data from all nodes..."
	@for node in $(HOSTS); do \
		hostname=$$(echo $$node | cut -d'-' -f1); \
		echo "  Fetching lscpu from $$node..."; \
		ssh $$node "lscpu" > $(RECEIVER_LOG_DIR)/lscpu_$$hostname.txt 2>&1 && \
			echo "    ✓ lscpu data saved to $(RECEIVER_LOG_DIR)/lscpu_$$hostname.txt" || \
			echo "    ✗ Failed to get lscpu from $$node"; \
	done
	@echo ""
	@echo "Collecting memory information from all nodes..."
	@for node in $(HOSTS); do \
		hostname=$$(echo $$node | cut -d'-' -f1); \
		echo "  Fetching memory info from $$node..."; \
		ssh $$node "free -h && echo && cat /proc/meminfo" > $(RECEIVER_LOG_DIR)/meminfo_$$hostname.txt 2>&1 && \
			echo "    ✓ memory data saved to $(RECEIVER_LOG_DIR)/meminfo_$$hostname.txt" || \
			echo "    ✗ Failed to get memory info from $$node"; \
	done
	@echo ""
	@echo "Collecting socket buffer configuration from all nodes..."
	@for node in $(HOSTS); do \
		hostname=$$(echo $$node | cut -d'-' -f1); \
		echo "  Fetching socket buffer config from $$node..."; \
		ssh $$node "echo 'Socket Buffer Maximums:' && \
			echo 'net.core.rmem_max:' && sysctl net.core.rmem_max && \
			echo 'net.core.wmem_max:' && sysctl net.core.wmem_max && \
			echo && echo 'Socket Buffer Defaults:' && \
			echo 'net.core.rmem_default:' && sysctl net.core.rmem_default && \
			echo 'net.core.wmem_default:' && sysctl net.core.wmem_default && \
			echo && echo 'TCP Buffer Settings:' && \
			echo 'net.ipv4.tcp_rmem:' && sysctl net.ipv4.tcp_rmem && \
			echo 'net.ipv4.tcp_wmem:' && sysctl net.ipv4.tcp_wmem && \
			echo && echo 'UDP Buffer Settings:' && \
			echo 'net.ipv4.udp_rmem_min:' && sysctl net.ipv4.udp_rmem_min && \
			echo 'net.ipv4.udp_wmem_min:' && sysctl net.ipv4.udp_wmem_min" > $(RECEIVER_LOG_DIR)/sysctl_$$hostname.txt 2>&1 && \
			echo "    ✓ socket buffer config saved to $(RECEIVER_LOG_DIR)/sysctl_$$hostname.txt" || \
			echo "    ✗ Failed to get socket buffer config from $$node"; \
	done
	@echo ""
	@echo "Comparing hardware configurations..."
	@if [ ! -f $(SCRIPT_DIR)/compare_hardware.py ]; then \
		echo "Error: compare_hardware.py script not found in $(SCRIPT_DIR)."; \
		echo "Creating compare_hardware.py..."; \
		python3 -c "import sys; sys.path.insert(0, '$(SCRIPT_DIR)'); exec(open('$(SCRIPT_DIR)/compare_hardware.py').read())" $(RECEIVER_LOG_DIR) 2>/dev/null || \
			echo "Please create $(SCRIPT_DIR)/compare_hardware.py to parse lscpu output"; \
	else \
		python3 $(SCRIPT_DIR)/compare_hardware.py $(RECEIVER_LOG_DIR); \
	fi
	@echo ""
	@echo "========================================================================"
	@echo "Hardware Survey Complete!"
	@echo "========================================================================"
	@echo ""

clean-run:
	@echo "========================================================================"
	@echo "Cleaning Remote Run Output Directories"
	@echo "========================================================================"
	@echo ""
	@echo "WARNING: This will remove ALL files from run_output directories on:"
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
	@read -p "Are you sure you want to continue? (yes/no): " confirm; \
	if [ "$$confirm" != "yes" ]; then \
		echo "Aborted."; \
		exit 1; \
	fi
	@echo ""
	@echo "Cleaning remote directories..."
	@all_nodes=""; \
	for node in $(SENDERS_LIST) $(RECEIVERS_LIST); do \
		if ! echo "$$all_nodes" | grep -q "$$node"; then \
			all_nodes="$$all_nodes $$node"; \
		fi; \
	done; \
	for node in $$all_nodes; do \
		echo "------------------------------------------------------------------------"; \
		echo "Cleaning $$node:$(REMOTE_WORK_DIR)/$(RECEIVER_LOG_DIR)/ (excluding INSTANCE_URI)"; \
		ssh $$node "find $(REMOTE_WORK_DIR)/$(RECEIVER_LOG_DIR)/ -mindepth 1 -maxdepth 1 ! -name 'INSTANCE_URI' -exec rm -rf {} + 2>/dev/null || true" && \
			echo "  ✓ Receiver log directory cleaned" || \
			echo "  ✗ Failed to clean receiver log directory"; \
		echo "Cleaning $$node:$(REMOTE_WORK_DIR)/$(SENDER_LOG_DIR)/ (excluding INSTANCE_URI)"; \
		ssh $$node "find $(REMOTE_WORK_DIR)/$(SENDER_LOG_DIR)/ -mindepth 1 -maxdepth 1 ! -name 'INSTANCE_URI' -exec rm -rf {} + 2>/dev/null || true" && \
			echo "  ✓ Sender log directory cleaned" || \
			echo "  ✗ Failed to clean sender log directory"; \
		echo ""; \
	done
	@echo "========================================================================"
	@echo "Remote Cleanup Complete!"
	@echo "========================================================================"
	@echo ""
	@echo "========================================================================"
	@echo "Cleaning Local Run Output Directory"
	@echo "========================================================================"
	@if [ -d "$(RECEIVER_LOG_DIR)" ]; then \
		echo "Removing local log, INI, and CSV files from $(RECEIVER_LOG_DIR)/ (excluding INSTANCE_URI)"; \
		rm -f $(RECEIVER_LOG_DIR)/*.log $(RECEIVER_LOG_DIR)/*.ini $(RECEIVER_LOG_DIR)/*.csv 2>/dev/null && \
			echo "  ✓ Local log, INI, and CSV files removed" || \
			echo "  ✗ No local log/INI/CSV files to remove"; \
	else \
		echo "  Local $(RECEIVER_LOG_DIR)/ directory does not exist"; \
	fi
	@echo ""
	@echo "Removing local timing and ID files (excluding INSTANCE_URI)..."
	@rm -f RUN_ID RX_START_TIME TX_START_TIME START_TIME 2>/dev/null && \
		echo "  ✓ RUN_ID, RX_START_TIME, TX_START_TIME, START_TIME removed" || \
		echo "  ✗ No timing/ID files to remove"
	@echo ""
	@echo "Note: INSTANCE_URI files are preserved on both local and remote systems"
	@echo ""
	@echo "========================================================================"
	@echo "Cleanup Complete!"
	@echo "========================================================================"
	@echo ""

kill-e2sar:
	@echo "========================================================================"
	@echo "Killing e2sar Processes"
	@echo "========================================================================"
	@if [ -n "$(NODE)" ]; then \
		echo "Target node: $(NODE)"; \
		echo "========================================================================"; \
		echo ""; \
		$(SCRIPT_DIR)/kill_e2sar $(NODE); \
	else \
		echo "Target nodes: $(HOSTS)"; \
		echo "========================================================================"; \
		echo ""; \
		for node in $(HOSTS); do \
			$(SCRIPT_DIR)/kill_e2sar $$node; \
		done; \
	fi
	@echo "========================================================================"
	@echo "Kill Complete!"
	@echo "========================================================================"
	@echo ""

kill-receivers:
	@echo "========================================================================"
	@echo "Stopping Receiver Processes (e2sar_perf -recv) with SIGTERM"
	@echo "========================================================================"
	@if [ -n "$(NODES)" ]; then \
		TARGET_NODES="$(NODES)"; \
	else \
		TARGET_NODES="$(RECEIVERS_LIST)"; \
	fi; \
	echo "Target nodes: $$TARGET_NODES"; \
	echo "========================================================================"; \
	echo ""; \
	for node in $$TARGET_NODES; do \
		echo "------------------------------------------------------------------------"; \
		echo "Checking $$node for receiver processes..."; \
		count=$$(ssh $$node "pgrep -f 'e2sar_perf.*-recv' 2>/dev/null | wc -l"); \
		if [ "$$count" -gt 0 ]; then \
			echo "  Found $$count receiver process(es)"; \
			ssh $$node "pkill -TERM -f 'e2sar_perf.*-recv'" && \
				echo "  ✓ Sent SIGTERM to receiver processes" || \
				echo "  ✗ Failed to signal some processes"; \
		else \
			echo "  No receiver processes found"; \
		fi; \
		echo ""; \
	done
	@echo "========================================================================"
	@echo "Stop Receivers Complete!"
	@echo "========================================================================"
	@echo ""

kill-senders:
	@echo "========================================================================"
	@echo "Stopping Sender Processes (e2sar_perf -send) with SIGTERM"
	@echo "========================================================================"
	@if [ -n "$(NODES)" ]; then \
		TARGET_NODES="$(NODES)"; \
	else \
		TARGET_NODES="$(SENDERS_LIST)"; \
	fi; \
	echo "Target nodes: $$TARGET_NODES"; \
	echo "========================================================================"; \
	echo ""; \
	for node in $$TARGET_NODES; do \
		echo "------------------------------------------------------------------------"; \
		echo "Checking $$node for sender processes..."; \
		count=$$(ssh $$node "pgrep -f 'e2sar_perf.*-send' 2>/dev/null | wc -l"); \
		if [ "$$count" -gt 0 ]; then \
			echo "  Found $$count sender process(es)"; \
			ssh $$node "pkill -TERM -f 'e2sar_perf.*-send'" && \
				echo "  ✓ Sent SIGTERM to sender processes" || \
				echo "  ✗ Failed to signal some processes"; \
		else \
			echo "  No sender processes found"; \
		fi; \
		echo ""; \
	done
	@echo "========================================================================"
	@echo "Stop Senders Complete!"
	@echo "========================================================================"
	@echo ""
