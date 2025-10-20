#!/usr/bin/env python3
"""
Register the ejfat_gnuradio catalog with intake/databroker.

This makes Broker.named('ejfat_gnuradio') work across sessions.
"""

import sys
from pathlib import Path
import yaml
import config


def get_intake_config_dir():
    """Get the intake configuration directory."""
    # Default intake config location
    config_dir = Path.home() / '.intake'
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def create_catalog_config():
    """
    Create intake catalog configuration for ejfat_gnuradio.

    Returns
    -------
    dict
        Catalog configuration
    """
    catalog_config = {
        'sources': {
            'ejfat_gnuradio': {
                'driver': 'bluesky-msgpack-catalog',
                'args': {
                    'paths': [str(config.CATALOG_DIR / '*.msgpack')],
                },
                'description': 'EJFAT GNU Radio Experiments',
                'metadata': {
                    'facility': 'EJFAT',
                    'beamline': 'gnuradio_testbed',
                    'location': 'Ottawa',
                }
            }
        }
    }

    return catalog_config


def register_catalog(verbose=True):
    """
    Register ejfat_gnuradio catalog with intake.

    This creates a configuration file that makes the catalog
    accessible via Broker.named('ejfat_gnuradio').
    """
    if verbose:
        print("\n" + "="*70)
        print("REGISTERING EJFAT_GNURADIO CATALOG")
        print("="*70 + "\n")

    # Get config directory
    config_dir = get_intake_config_dir()
    config_file = config_dir / 'ejfat_gnuradio.yml'

    if verbose:
        print(f"Intake config directory: {config_dir}")
        print(f"Catalog config file: {config_file}")

    # Create catalog config
    catalog_config = create_catalog_config()

    # Write config file
    with open(config_file, 'w') as f:
        yaml.dump(catalog_config, f, default_flow_style=False)

    if verbose:
        print(f"\n✅ Catalog configuration written to: {config_file}")
        print(f"   Catalog directory: {config.CATALOG_DIR}")

    # Try to load it
    try:
        from databroker import catalog

        if 'ejfat_gnuradio' in catalog:
            if verbose:
                print("\n✅ Catalog successfully registered!")
                print("   You can now use: Broker.named('ejfat_gnuradio')")

            # Try to access it
            cat = catalog['ejfat_gnuradio']

            # Count runs
            try:
                runs = list(cat)
                if verbose:
                    print(f"\n📊 Catalog contains {len(runs)} runs")

                    if runs:
                        latest = runs[-1]
                        start = latest.metadata['start']
                        print(f"\n   Latest run:")
                        print(f"     UID: {start['uid'][:8]}")
                        print(f"     Plan: {start.get('plan_name', 'unknown')}")
                        print(f"     Experiment: {start.get('experiment_id', 'N/A')}")
            except Exception as e:
                if verbose:
                    print(f"\n⚠️  Could not count runs: {e}")
        else:
            if verbose:
                print("\n⚠️  Catalog not found after registration")
                print("   You may need to restart Python")

    except ImportError as e:
        if verbose:
            print(f"\n⚠️  Could not verify catalog: {e}")
            print("   The config file was created, but you may need:")
            print("   pip install intake-bluesky")

    if verbose:
        print("\n" + "="*70)
        print("REGISTRATION COMPLETE")
        print("="*70)
        print("\nTo use the catalog in Python:")
        print("  from databroker import Broker")
        print("  db = Broker.named('ejfat_gnuradio')")
        print("  run = db[-1]")
        print("  table = run.table()")
        print("\nOr:")
        print("  from databroker import catalog")
        print("  cat = catalog['ejfat_gnuradio']")
        print("  runs = list(cat)")
        print("="*70 + "\n")


def test_catalog_access():
    """Test accessing the registered catalog."""
    print("\n" + "="*70)
    print("TESTING CATALOG ACCESS")
    print("="*70 + "\n")

    try:
        from databroker import Broker

        print("Attempting: Broker.named('ejfat_gnuradio')...")
        db = Broker.named('ejfat_gnuradio')
        print("✅ Success! Broker.named('ejfat_gnuradio') works!")

        # Try to get a run
        try:
            run = db[-1]
            print(f"\n✅ Retrieved latest run: {run.start['uid'][:8]}")
            print(f"   Plan: {run.start.get('plan_name', 'unknown')}")

            # Try to get table
            table = run.table()
            print(f"   Data points: {len(table)}")
            print(f"   Columns: {list(table.columns)}")

        except IndexError:
            print("\n⚠️  No runs in catalog yet")
            print("   Run an experiment: python run_experiment.py mock_experiment")
        except Exception as e:
            print(f"\n⚠️  Could not retrieve run: {e}")

    except Exception as e:
        print(f"❌ Failed: {e}")
        print("\nTry using the helper functions instead:")
        print("  from setup_databroker_helper import load_data_from_catalog")
        print("  cat = load_data_from_catalog()")

    print("\n" + "="*70 + "\n")


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Register ejfat_gnuradio catalog with intake/databroker'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test catalog access after registration'
    )

    args = parser.parse_args()

    # Register catalog
    register_catalog(verbose=True)

    # Test if requested
    if args.test:
        test_catalog_access()

    return 0


if __name__ == "__main__":
    sys.exit(main())
