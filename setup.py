#!/usr/bin/env python
import os

from setuptools import find_packages, setup


# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-postmark-utils',
    version='0.1',
    author='Regulus Ltd',
    author_email='reg@regulusweb.com',
    url='https://github.com/regulusweb/django-postmark-utils',
    license='MIT License',
    packages=find_packages(),
    python_requires='>=3.4',
    install_requires=[
        'postmarker>=0.11.3',
        'python-dateutil>=2.0',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Communications :: Email',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
