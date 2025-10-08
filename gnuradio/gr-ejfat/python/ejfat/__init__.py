#
# Copyright 2008,2009 Free Software Foundation, Inc.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

# The presence of this file turns this directory into a Python package

'''
This is the GNU Radio EJFAT module. Place your Python package
description here (python/__init__.py).
'''
import os

# import pybind11 generated symbols into the ejfat namespace
try:
    # this might fail if the module is python-only
    from .ejfat_python import *
except ModuleNotFoundError:
    pass

# import any pure python here
from .ejfat_sink import ejfat_sink
from .ejfat_source import ejfat_source
from .ejfat_shm_sink import ejfat_shm_sink
from .ejfat_shm_source import ejfat_shm_source

# E2SAR blocks - only import if e2sar_py is available
try:
    from .e2sar_segmenter_sink import e2sar_segmenter_sink
    from .e2sar_reassembler_source import e2sar_reassembler_source
except ImportError:
    # e2sar_py not available - E2SAR blocks will not be available
    pass
#
