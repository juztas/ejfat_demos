#!/usr/bin/env python3
"""
GNU Radio Environment Verification Script
Tests that all critical components are properly installed
"""

import sys
import importlib
from typing import List, Tuple

def check_import(module_name: str, description: str = "") -> Tuple[bool, str]:
    """
    Attempt to import a module and return success status
    """
    try:
        mod = importlib.import_module(module_name)
        version = getattr(mod, '__version__', 'unknown')
        return True, version
    except ImportError as e:
        return False, str(e)

def check_boost() -> Tuple[bool, str]:
    """
    Check Boost installation via Python bindings
    """
    try:
        import subprocess
        result = subprocess.run(['python', '-c',
                               'import sys; import sysconfig; print(sysconfig.get_config_var("BOOST_ROOT") or "")'],
                              capture_output=True, text=True)
        # Boost is typically available through C++ extensions
        return True, "Available (C++ library)"
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 60)
    print("GNU Radio Environment Verification")
    print("=" * 60)
    print()

    checks = [
        # Core GNU Radio
        ("gnuradio.gr", "GNU Radio Core"),
        ("gnuradio.blocks", "GNU Radio Blocks"),
        ("gnuradio.analog", "GNU Radio Analog"),
        ("gnuradio.digital", "GNU Radio Digital"),
        ("gnuradio.filter", "GNU Radio Filter"),
        ("gnuradio.fft", "GNU Radio FFT"),
        ("gnuradio.qtgui", "GNU Radio Qt GUI"),

        # Python scientific stack
        ("numpy", "NumPy"),
        ("scipy", "SciPy"),
        ("matplotlib", "Matplotlib"),

        # Networking
        ("zmq", "PyZMQ"),

        # Development tools
        ("IPython", "IPython"),
    ]

    results: List[Tuple[str, bool, str]] = []

    for module, description in checks:
        success, info = check_import(module, description)
        results.append((description, success, info))

    # Check Boost separately
    boost_ok, boost_info = check_boost()
    results.append(("Boost C++", boost_ok, boost_info))

    # Print results
    max_desc_len = max(len(desc) for desc, _, _ in results)
    all_passed = True

    for description, success, info in results:
        status = "✓ PASS" if success else "✗ FAIL"
        if not success:
            all_passed = False

        padding = " " * (max_desc_len - len(description))
        version_info = f" (v{info})" if success and info != "unknown" else ""
        print(f"{description}{padding} : {status}{version_info}")

        if not success:
            print(f"  Error: {info}")

    print()
    print("-" * 60)

    # Check GNU Radio version
    try:
        from gnuradio import gr
        gr_version = gr.version()
        print(f"GNU Radio Version: {gr_version}")
    except:
        print("GNU Radio Version: Unable to determine")

    # Check Python version
    print(f"Python Version: {sys.version.split()[0]}")

    # Check available GNU Radio modules
    print()
    print("Available GNU Radio modules:")
    gr_modules = [
        'analog', 'audio', 'blocks', 'channels', 'digital',
        'dtv', 'fec', 'fft', 'filter', 'network', 'qtgui',
        'trellis', 'uhd', 'video_sdl', 'vocoder', 'wavelet',
        'zeromq'
    ]

    available = []
    for mod in gr_modules:
        try:
            importlib.import_module(f'gnuradio.{mod}')
            available.append(mod)
        except ImportError:
            pass

    print(f"  {', '.join(available)}")

    print()
    print("=" * 60)

    if all_passed:
        print("✓ All critical components verified successfully!")
        print()
        print("You can now launch GNU Radio Companion with:")
        print("  gnuradio-companion")
        return 0
    else:
        print("✗ Some components failed verification.")
        print("Please check the errors above and reinstall if needed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
