#!/usr/bin/env python
import os

from setuptools import find_packages, setup


# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

test_requires = [
    'pytest==3.6.3',
    'pytest-django==3.3.2',
    'pytest-xdist==1.22.2',
]

setup(
    name='django-postmark-utils',
    version='0.1',
    description='Django utilities to help track emails sent using Postmark',
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
    extras_require={
        'test': test_requires,
    },
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
