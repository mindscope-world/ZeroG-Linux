from setuptools import setup
import sys

# Fix for RecursionError in py2app modulegraph
sys.setrecursionlimit(5000)

APP = ['main.py']
DATA_FILES = [
    '.env',
    'macdictate/core/gemini_prompt.txt',
]
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'LSUIElement': True,
        'CFBundleName': 'MacDictate',
        'CFBundleDisplayName': 'MacDictate',
        'CFBundleIdentifier': 'com.antony.macdictate',
        'CFBundleVersion': '0.7.0',
    },
    'packages': ['macdictate', 'sounddevice', 'numpy', 'mlx_whisper', 'Quartz', 'google'],
    'includes': ['google.genai', 'certifi'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
