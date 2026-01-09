# Original ZeroG Author: Antony Njoro
# setup.py
# Modified by: Paul Ndirangu
"""
Removes the Mac-specific py2app logic and focuses on the dependencies required for Ubuntu.
"""
from setuptools import setup, find_packages

setup(
    name='ZeroG',
    version='0.9.0',
    description='Open Source Voice Typing for Ubuntu',
    author='Paul Ndirangu',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'faster-whisper',
        'sounddevice',
        'numpy',
        'pyperclip',
        'pynput',
        'google-genai',
        'python-dotenv',
        'certifi'
    ],
    entry_points={
        'console_scripts': [
            'zerog=main:main',
        ],
    },
)