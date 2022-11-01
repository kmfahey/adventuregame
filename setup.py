#!/usr/bin/python3

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='adventuregame',
    version='0.9',
    description='A text-adventure game inspired by ADVENT but compatible with Dungeons & Dragons.',
    long_description=readme,
    author='Kerne MacDonald Fahey',
    author_email='kernefahey@protonmail.com',
    url='https://github.com/kmfahey/adventuregame/',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
