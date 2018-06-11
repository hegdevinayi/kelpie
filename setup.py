from setuptools import setup, find_packages
import os
from kelpie import __version__


with open(os.path.join(os.path.dirname(__file__), 'README.md'), 'r') as fr:
    long_description = fr.read()


setup(
    name='kelpie',
    version=__version__,
    description='A lean Python module for cluster-side management of VASP runs',
    long_description=long_description,
    url='https://gitlab.com/hegdevinayi/kelpie',
    author='Vinay Hegde',
    author_email='hegdevinayi@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='VASP DFT supercomputer high-throughput',
    packages=find_packages(exclude=['tests*', 'docs']),
    install_requires=[
        'six',
        'lxml',
        'numpy'
    ],
    include_package_data=True,
    scripts=[
        'bin/kelpie',
    ]
)
