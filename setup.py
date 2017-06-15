#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import codecs
from setuptools import setup


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding='utf-8').read()


version = read('configmanager/__init__.py').split('\n')[0].split('=', 1)[1].strip().strip("'")


setup(
    name='configmanager',
    version=version,
    author='Jazeps Basko',
    author_email='jazeps.basko@gmail.com',
    maintainer='Jazeps Basko',
    maintainer_email='jazeps.basko@gmail.com',
    license='MIT',
    url='https://github.com/jbasko/configmanager',
    description='Extensible, object-oriented manager of configuration items and configuration trees of arbitrary depth',
    long_description=read('README.rst'),
    packages=['configmanager'],
    install_requires=['six==1.10.0', 'future==0.16.0', 'configparser==3.5.0', 'hookery<0.4.0'],
    extras_require={
        'yaml': ['PyYAML'],
        'click': ['click'],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: MIT License',
    ],
)
