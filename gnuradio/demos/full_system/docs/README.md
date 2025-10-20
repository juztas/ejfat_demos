# Documentation Index

This directory contains all documentation for the Bluesky-based experiment control framework for GNU Radio and EJFAT data acquisition.

## Quick Navigation

- **New Users**: Start with [Tutorial](#tutorial-documentation)
- **Running Experiments**: See [User Documentation](#user-documentation)
- **Contributing**: See [Developer Documentation](#developer-documentation)

## Tutorial Documentation

Step-by-step guides for getting started:

### Getting Started
- **[Quick Start (DataBroker)](tutorial/QUICK_START_DATABROKER.md)** - 5-minute quick start for data storage and retrieval
- **[Running Experiments Tutorial](tutorial/TUTORIAL_RUNNING_EXPERIMENTS.md)** - Complete guide to running experiments with the framework

### Summaries
- **[Tutorial Summary](tutorial/TUTORIAL_SUMMARY.md)** - Overview of tutorial content and learning path

## User Documentation

Guides and references for using the framework:

### Guides
- **[Data Retrieval and Analysis Guide](user/DATA_RETRIEVAL_AND_ANALYSIS_GUIDE.md)** - Comprehensive guide to retrieving and analyzing experiment data
- **[DataBroker Connection Guide](user/DATABROKER_CONNECTION_GUIDE.md)** - Connecting to and using the DataBroker catalog

### Quick References
- **[Quick Reference](user/QUICK_REFERENCE.md)** - Command reference and common operations
- **[DataBroker Quick Reference](user/DATABROKER_QUICK_REFERENCE.md)** - Fast reference for DataBroker operations

## Developer Documentation

Design documents, implementation details, and development guides:

### Architecture and Design
- **[Bluesky Comprehensive Plan](developer/BLUESKY_COMPREHENSIVE_PLAN.md)** - Original design document and architecture overview
- **[Implementation Status](developer/IMPLEMENTATION_STATUS.md)** - Current status of all planned features
- **[FM/SHM Integration Plan](developer/FM_SHM_INTEGRATION_PLAN.md)** - EJFAT shared memory integration design

### Implementation Phases
- **[Phase 1: Basic Integration](developer/PHASE1_COMPLETE.md)** - Basic Bluesky integration completion
- **[Phase 2: Persistent Storage](developer/PHASE2_README.md)** - DataBroker persistent storage implementation
- **[Phase 3: Advanced Features](developer/PHASE3_COMPLETE.md)** - Advanced callbacks and metadata
- **[Phase 4: Analysis Tools](developer/PHASE4_IMPLEMENTATION.md)** - Data export and visualization

### Setup and Configuration
- **[DataBroker Setup](developer/DATABROKER_SETUP.md)** - Setting up persistent data storage
- **[DataBroker Fix Guide](developer/DATABROKER_FIX_GUIDE.md)** - Troubleshooting and common issues
- **[Persistent DataBroker Update](developer/PERSISTENT_DATABROKER_UPDATE.md)** - Migration to persistent storage

### Development Notes
- **[Claude Code Instructions](developer/CLAUDE.md)** - AI assistant instructions for code development
- **[Claude Update Summary](developer/CLAUDE_UPDATE_SUMMARY.md)** - Recent development updates
- **[Notebook Creation Summary](developer/NOTEBOOK_CREATION_SUMMARY.md)** - Jupyter notebook development notes
- **[Jupyter Book Conversion Summary](developer/JUPYTER_BOOK_CONVERSION_SUMMARY.md)** - Documentation format notes

## Interactive Notebooks

Located in `../notebooks/`:
- **quick_start.ipynb** - 5-minute interactive quick start
- **data_retrieval_and_analysis_tutorial.ipynb** - 30-45 minute comprehensive tutorial

See `../notebooks/README.md` for details.

## External Resources

- [Bluesky Project Documentation](https://blueskyproject.io/)
- [Ophyd Documentation](https://blueskyproject.io/ophyd/)
- [DataBroker Documentation](https://blueskyproject.io/databroker/)
- [GNU Radio Wiki](https://wiki.gnuradio.org/)

## Documentation Categories Explained

### Tutorial Documentation
- **Purpose**: Learn how to use the framework
- **Audience**: New users, beginners
- **Format**: Step-by-step guides with examples
- **Start here if**: You're new to the framework or want to learn specific workflows

### User Documentation
- **Purpose**: Daily usage reference and guides
- **Audience**: Regular users running experiments
- **Format**: Reference guides, how-tos, quick lookups
- **Use this when**: You know what you want to do and need the syntax or procedure

### Developer Documentation
- **Purpose**: Understand internals, contribute code, extend functionality
- **Audience**: Developers, contributors, advanced users
- **Format**: Architecture docs, design decisions, implementation details
- **Refer to this when**: You're modifying code, adding features, or need to understand how things work under the hood
