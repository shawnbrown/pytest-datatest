#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import codecs
from setuptools import setup


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding='utf-8').read()


setup(
    name='pytest-datatest',
    version='0.1.1',
    author='Shawn Brown',
    maintainer='Shawn Brown',
    license='MIT',
    url='https://github.com/shawnbrown/pytest-datatest',
    description=("A pytest plugin for test driven data-wrangling (this is the "
                 "development version of datatest's pytest integration)."),
    long_description=read('README.rst'),
    py_modules=['pytest_datatest'],
    install_requires=[
        'pytest>=3.1.1',
        'datatest>=0.8.3',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Pytest',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
    ],
    entry_points={
        'pytest11': [
            'datatest_devel = pytest_datatest',
        ],
    },
)
