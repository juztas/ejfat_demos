#!/bin/bash

# Script to sync current directory to wash-dtn1-mgt.es.net
# Automatically determines the path relative to ejfat_demos and syncs to the same location on remote

REMOTE_HOST="wash-dtn1-mgt.es.net"

# Get the current working directory
CURRENT_DIR=$(pwd)

# Extract the relative path from ejfat_demos onwards
RELATIVE_PATH=$(echo "$CURRENT_DIR" | sed 's|.*/ejfat_demos/||')

# Construct the remote path
REMOTE_PATH="~/ejfat_demos/${RELATIVE_PATH}"

echo "Current directory: ${CURRENT_DIR}"
echo "Syncing to ${REMOTE_HOST}:${REMOTE_PATH}..."
echo ""

# Ensure remote directory exists
ssh "${REMOTE_HOST}" "mkdir -p ${REMOTE_PATH}"

if [ $? -ne 0 ]; then
    echo "Failed to create remote directory"
    exit 1
fi

# Sync current directory to remote
# -a: archive mode (preserve permissions, timestamps, etc.)
# -v: verbose
# -z: compress during transfer
# --progress: show progress
# --delete: delete files on remote that don't exist locally (optional, commented out by default)
rsync -avz --progress \
    --exclude '.git' \
    --exclude '*.pyc' \
    --exclude '__pycache__' \
    --exclude '.DS_Store' \
    ./ "${REMOTE_HOST}:${REMOTE_PATH}/"

if [ $? -eq 0 ]; then
    echo ""
    echo "Sync completed successfully!"
    echo "Remote location: ${REMOTE_HOST}:${REMOTE_PATH}"
else
    echo ""
    echo "Sync failed with error code $?"
    exit 1
fi
