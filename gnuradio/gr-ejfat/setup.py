#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='gnuradio-ejfat',
    version='1.0.0',
    description='GNU Radio EJFAT file source and sink blocks',
    author='gr-ejfat author',
    packages=['gnuradio.ejfat'],
    package_dir={'gnuradio.ejfat': 'python/ejfat'},
    install_requires=[
        'numpy',
    ],
    python_requires='>=3.6',
    namespace_packages=['gnuradio'],
)
