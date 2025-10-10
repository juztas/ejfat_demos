#!/usr/bin/env python3
"""
Command-line interface for running Bluesky experiments.

This script provides a simple CLI to list and run available experiments.
"""

import sys
import argparse
from pathlib import Path
import importlib.util


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
    exp_path = Path(__file__).parent / experiments_dir
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
    print()


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
    print(f"{'='*70}\n")

    try:
        module = experiments[experiment_name]['module']
        return module.main()
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
        description='Run Bluesky experiments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                    # List all experiments
  %(prog)s mock_experiment         # Run mock experiment
  %(prog)s info mock_experiment    # Show experiment details
        """
    )

    parser.add_argument(
        'command',
        nargs='?',
        help='Command: experiment name, "list", or "info <experiment>"'
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
