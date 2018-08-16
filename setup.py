#!/usr/bin/env python

from setuptools import setup


setup(
    name='cachecleaner',
    version='0.3',
    description='Keeps dir size in given capacity.',
    author='Alexander Karpinsky',
    author_email='homm86@gmail.com',
    url='https://github.com/homm/cachecleaner',
    py_modules=['cachecleaner'],
    install_requires=[
        'tqdm>=4.20.0',
    ]
)
