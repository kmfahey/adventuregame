#!/usr/bin/python3

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='adventuregame',
    version='0.9.001',
    description='A text-adventure game inspired by the old UNIX game ADVENT, running on a limited Dungeons-&-Dragons-like ruleset and implementing 24 action commands. The player explores a small underground complex, slaying foes, collecting treasure, and trying to find both the exit and the key to unlock it.',
    long_description=readme,
    author='Kerne MacDonald Fahey',
    author_email='kernefahey@protonmail.com',
    url='https://github.com/kmfahey/adventuregame/',
    license=license,
    packages=find_packages(exclude=('tests', 'docs', 'pyxtermjs'))
)
