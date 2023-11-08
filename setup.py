from setuptools import setup

APP = ['beetle-battle.py']
DATA_FILES = []
OPTIONS = {
    'iconfile': 'icon.icns',
    'plist': {
        'CFBundleShortVersionString': '0.1.0',
        'CFBundleName': 'Beetle Battle',
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
