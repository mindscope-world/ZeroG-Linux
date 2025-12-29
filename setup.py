from setuptools import setup

APP = ['main.py']
DATA_FILES = [
    'macdictate/core',
    'macdictate/gui',
    '.env',
    'gemini_prompt.txt',
    'mac_dictate.log'
]
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'LSUIElement': True,
        'CFBundleName': 'MacDictate',
        'CFBundleDisplayName': 'MacDictate',
        'CFBundleIdentifier': 'com.antony.macdictate',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
    },
    'packages': ['macdictate', 'sounddevice', 'numpy', 'mlx_whisper', 'google.generativeai'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
