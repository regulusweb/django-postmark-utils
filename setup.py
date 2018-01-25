#!/usr/bin/env python
import os

from setuptools import find_packages, setup


# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-postmark-utils',
    version='0.1',
    description='A few useful utilities for using Postmark in Django',
    author='Regulus Ltd',
    author_email='reg@regulusweb.com',
    url='https://github.com/regulusweb/django-postmark-utils',
    packages=find_packages(),
    install_requires=[
        'postmarker>=0.11.3',
        'python-dateutil>=2.0',
    ],
)
