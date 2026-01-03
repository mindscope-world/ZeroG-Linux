from setuptools import setup
import sys

# Fix for RecursionError in py2app modulegraph
sys.setrecursionlimit(5000)

APP = ['main.py']
DATA_FILES = [
    '.env',
    'zerog/core/gemini_prompt.txt',
]
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'LSUIElement': True,
        'CFBundleName': 'ZeroG',
        'CFBundleDisplayName': 'ZeroG',
        'CFBundleIdentifier': 'com.antony.zerog',
        'CFBundleVersion': '0.7.0',
    },
    'packages': ['zerog', 'sounddevice', 'numpy', 'mlx_whisper', 'Quartz', 'google'],
    'includes': ['google.genai', 'certifi'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
