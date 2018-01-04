from setuptools import setup, find_packages
import os


with open(os.path.join(os.path.dirname(__file__), 'VERSION'), 'r') as fr:
    version = fr.read().strip()

with open(os.path.join(os.path.dirname(__file__), 'README.md'), 'r') as fr:
    long_description = fr.read()

setup(
    name='waspy',
    version=version,
    description='A Python-based project for cluster-side management of VASP runs',
    long_description=long_description,
    url='https://gitlab.com/hegdevinayi/waspy',
    author='Vinay Hegde',
    author_email='hegdevinayi@gmail.com',
    license='LICENSE',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='VASP DFT supercomputer high-throughput',
    packages=find_packages(),
    install_requires=[
        'beautifulsoup4',
        'numpy'
    ],
    include_package_data=True,
    scripts=[
        'bin/waspy'
    ]
)
