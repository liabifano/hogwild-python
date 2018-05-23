#!/usr/bin/env python
from setuptools import setup, find_packages

setup(name='hogwild',
      url='',
      author='',
      package_dir={'': 'src'},
      packages=find_packages('src'),
      version='0.0.1',
      install_requires=['pytest==2.9.2',
                        'grpcio==1.10.1',
                        'grpcio-tools==1.10.1',
                        'numpy==1.14.2',
                        'pytest==2.9.2'],
      include_package_data=True,
      zip_safe=False)
