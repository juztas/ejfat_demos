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

# Determine remote working directory dynamically based on current location
# This makes the Makefile relocatable within the ejfat_demos directory tree
# On remote nodes, ejfat_demos is located under the user's home directory
CURRENT_DIR := $(shell pwd)
RELATIVE_PATH := $(shell echo $(CURRENT_DIR) | sed 's|.*/ejfat_demos/||')
REMOTE_WORK_DIR := ~/ejfat_demos/$(RELATIVE_PATH)

.PHONY: help reserve

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
	@echo ""
	@echo "USAGE:"
	@echo "  make reserve EJFAT_URI_BETA=ejfat://useless@192.168.100.1:18347/lb/1"
	@echo "  make reserve EJFAT_URI_BETA=\$$EJFAT_URI_BETA LB_NAME=my_test"
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
		$(SCRIPT_DIR)/reserve_lb.sh \
			-u \"$(EJFAT_URI_BETA)\" \
			-n \"$(LB_NAME)\" \
			-d $(LB_RESERVE_DURATION) \
			-i $(IP_VERSION)'"
	@echo ""
	@echo "Fetching INSTANCE_URI file from remote..."
	@scp $(PRIMARY_DTN):$(REMOTE_WORK_DIR)/INSTANCE_URI ./INSTANCE_URI
	@echo "========================================================================"
	@echo "Reservation complete! INSTANCE_URI saved locally."
	@echo "========================================================================"
	@cat INSTANCE_URI
	@echo ""
