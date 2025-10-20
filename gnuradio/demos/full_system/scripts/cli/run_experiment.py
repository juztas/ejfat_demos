#!/usr/bin/env python3
"""
Command-line interface for running Bluesky experiments.

This script provides a simple CLI to list and run available experiments.

All experiments run through this CLI will use:
- Persistent DataBroker catalog (data/catalog/*.msgpack)
- JSON document backup (data/documents/*.jsonl)
- Standard callbacks and metadata
"""

import sys
import argparse
from pathlib import Path
import importlib.util
import os

# Add project root and scripts/config_setup to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts" / "config_setup"))

# Set environment variable to indicate running via CLI
# Experiments can check this to use standardized setup
os.environ['BLUESKY_CLI_MODE'] = '1'
os.environ['BLUESKY_USE_PERSISTENT_DB'] = '1'


def discover_experiments(experiments_dir='experiments'):
    """
    Discover available experiment modules.

    Parameters
    ----------
    experiments_dir : str or Path
        Directory containing experiment modules

    Returns
    -------
    dict
        Dictionary of experiment_name: module_path
    """
    # experiments_dir is relative to project root
    exp_path = Path(__file__).parent.parent.parent / experiments_dir
    experiments = {}

    for py_file in exp_path.glob('*.py'):
        if py_file.name.startswith('__'):
            continue

        # Load module to check for main() function
        try:
            spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, 'main'):
                experiments[py_file.stem] = {
                    'path': py_file,
                    'module': module,
                    'doc': module.__doc__ or 'No description available'
                }
        except Exception as e:
            print(f"Warning: Could not load {py_file.name}: {e}", file=sys.stderr)

    return experiments


def list_experiments():
    """List all available experiments."""
    experiments = discover_experiments()

    print("\n" + "="*70)
    print("AVAILABLE EXPERIMENTS")
    print("="*70 + "\n")

    if not experiments:
        print("No experiments found in experiments/ directory")
        return

    for name, info in sorted(experiments.items()):
        doc_lines = info['doc'].strip().split('\n')
        title = doc_lines[0] if doc_lines else name

        print(f"  {name}")
        print(f"    {title}")
        print()

    print("="*70)
    print(f"\nTotal: {len(experiments)} experiments")
    print("\nRun an experiment with:")
    print(f"  python run_experiment.py <experiment_name>")
    print("\nExample:")
    print(f"  python run_experiment.py mock_experiment")

    print("\n" + "-"*70)
    print("DATA STORAGE:")
    print("-"*70)
    print("  All experiments save data to:")
    print("    • Catalog:   data/catalog/*.msgpack   (DataBroker persistent)")
    print("    • Documents: data/documents/*.jsonl   (JSON backup)")
    print("\n  Retrieve data:")
    print("    python access_my_data.py              (latest run)")
    print("    python retrieve_data.py --list        (all runs)")
    print()


def show_catalog_status():
    """Show DataBroker catalog status."""
    print("\n" + "="*70)
    print("DATABROKER CATALOG STATUS")
    print("="*70 + "\n")

    # Check catalog directory
    from pathlib import Path
    import config

    catalog_dir = Path(config.CATALOG_DIR)
    doc_dir = Path(config.DOCUMENT_DIR)

    # Count catalog files
    catalog_files = list(catalog_dir.glob('*.msgpack'))
    print(f"📂 Catalog directory: {catalog_dir}")
    print(f"   Files: {len(catalog_files)} msgpack files")

    # Count document files
    doc_files = list(doc_dir.glob('*_documents.jsonl'))
    print(f"\n📂 Documents directory: {doc_dir}")
    print(f"   Files: {len(doc_files)} document files")

    # Try to load catalog
    print("\n" + "-"*70)
    print("ATTEMPTING TO LOAD CATALOG...")
    print("-"*70)

    try:
        from setup_databroker_helper import load_data_from_catalog

        cat = load_data_from_catalog(verbose=False)

        if cat:
            runs = list(cat.items())
            print(f"✅ Successfully loaded catalog")
            print(f"   Total runs: {len(runs)}")

            if runs:
                # Show latest run
                latest_uid, latest_run = runs[-1]
                start = latest_run.metadata['start']
                print(f"\n   Latest run:")
                print(f"     UID: {latest_uid[:8]}")
                print(f"     Plan: {start.get('plan_name', 'unknown')}")
                print(f"     Experiment: {start.get('experiment_id', 'N/A')}")
        else:
            print("⚠️  No catalog data found")
            print("   Run an experiment to create catalog data")

    except Exception as e:
        print(f"⚠️  Could not load catalog: {e}")
        print("   Install suitcase-msgpack: pip install suitcase-msgpack")

    # Try to load from documents
    if doc_files:
        print("\n" + "-"*70)
        print("DOCUMENT FILES (JSON BACKUP):")
        print("-"*70)

        try:
            from setup_databroker_helper import load_from_documents

            run_data = load_from_documents(verbose=False)

            if run_data:
                start = run_data['start']
                print(f"✅ Latest document file loaded")
                print(f"   UID: {start['uid'][:8]}")
                print(f"   Plan: {start.get('plan_name', 'unknown')}")
                print(f"   Events: {len(run_data['events'])}")

        except Exception as e:
            print(f"⚠️  Could not load documents: {e}")

    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("="*70)
    print("  View latest data:  python access_my_data.py")
    print("  List all runs:     python retrieve_data.py --list")
    print("  Run experiment:    python run_experiment.py mock_experiment")
    print("="*70 + "\n")


def run_experiment(experiment_name):
    """
    Run a specific experiment.

    Parameters
    ----------
    experiment_name : str
        Name of the experiment to run
    """
    experiments = discover_experiments()

    if experiment_name not in experiments:
        print(f"\n❌ Error: Experiment '{experiment_name}' not found\n")
        print("Available experiments:")
        for name in sorted(experiments.keys()):
            print(f"  - {name}")
        print("\nUse 'list' to see details about each experiment")
        return 1

    # Run the experiment's main() function
    print(f"\n{'='*70}")
    print(f"RUNNING: {experiment_name}")
    print(f"{'='*70}")
    print("Data will be saved to:")
    print("  • Catalog:   data/catalog/*.msgpack")
    print("  • Documents: data/documents/*.jsonl")
    print(f"{'='*70}\n")

    try:
        module = experiments[experiment_name]['module']
        result = module.main()

        # Show post-experiment info
        print("\n" + "="*70)
        print("EXPERIMENT FINISHED")
        print("="*70)
        print("\nAccess your data:")
        print("  python access_my_data.py        # View latest run")
        print("  python retrieve_data.py --list  # List all runs")
        print("="*70 + "\n")

        return result

    except KeyboardInterrupt:
        print("\n\n⚠️  Experiment interrupted by user\n")
        return 130
    except Exception as e:
        print(f"\n\n❌ Experiment failed with error:\n")
        import traceback
        traceback.print_exc()
        return 1


def show_experiment_info(experiment_name):
    """Show detailed information about an experiment."""
    experiments = discover_experiments()

    if experiment_name not in experiments:
        print(f"\n❌ Error: Experiment '{experiment_name}' not found\n")
        return 1

    info = experiments[experiment_name]

    print("\n" + "="*70)
    print(f"EXPERIMENT: {experiment_name}")
    print("="*70 + "\n")

    print("Description:")
    print(info['doc'])
    print()

    print(f"Path: {info['path']}")
    print()

    # Try to extract metadata from module
    module = info['module']

    if hasattr(module, '__version__'):
        print(f"Version: {module.__version__}")

    if hasattr(module, '__author__'):
        print(f"Author: {module.__author__}")

    print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Run Bluesky experiments with persistent DataBroker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                    # List all experiments
  %(prog)s status                  # Show DataBroker catalog status
  %(prog)s mock_experiment         # Run mock experiment
  %(prog)s info mock_experiment    # Show experiment details

Data Storage:
  All experiments automatically save data to:
    • Catalog:   data/catalog/*.msgpack   (DataBroker persistent)
    • Documents: data/documents/*.jsonl   (JSON backup)

  Retrieve data:
    python access_my_data.py              # View latest run
    python retrieve_data.py --list        # List all runs
        """
    )

    parser.add_argument(
        'command',
        nargs='?',
        help='Command: experiment name, "list", "status", or "info <experiment>"'
    )

    parser.add_argument(
        'experiment',
        nargs='?',
        help='Experiment name (for "info" command)'
    )

    parser.add_argument(
        '--catalog',
        choices=['temp', 'sqlite', 'mongodb'],
        default=None,
        help='DataBroker catalog type (overrides config)'
    )

    args = parser.parse_args()

    # Handle commands
    if args.command is None or args.command == 'list':
        list_experiments()
        return 0

    elif args.command == 'status':
        show_catalog_status()
        return 0

    elif args.command == 'info':
        if args.experiment is None:
            print("\n❌ Error: 'info' command requires an experiment name\n")
            print("Usage: python run_experiment.py info <experiment_name>")
            return 1
        return show_experiment_info(args.experiment)

    elif args.command == 'help':
        parser.print_help()
        return 0

    else:
        # Assume it's an experiment name
        return run_experiment(args.command)


if __name__ == "__main__":
    sys.exit(main())
