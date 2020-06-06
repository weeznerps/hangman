#!/usr/bin/env python
from setuptools import setup, find_packages
from hangman import __version__

# NOTE: Install requirements from requirements.txt

setup(
    version=__version__,
    name="hangman",
    packages=find_packages()
)

