# -*- coding: utf-8 -*-
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('README.md') as f:
    readme = f.read()

setup(
    name="redis-bloom-filter",
    version="1.0.1",
    description="Bloom filter based on redis",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="anexplore",
    maintainer='anexplore',
    packages=["redisbloomfilter"],
    package_dir={'redisbloomfilter': 'src'},
    url='https://github.com/anexplore/pyredisbloomfilter',
    license='Apache',
    install_requires=[
        'redis>=2.10.0',
        'mmh3>=2.5.0'
    ],
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4",
    keywords=[
        'bloom filter',
        'redis bloom filter',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Environment :: Web Environment',
        'Operating System :: POSIX',
        'License :: OSI Approved :: Apache Software License'
    ]
)