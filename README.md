# Beetle Battle
Beetle Battle board game in Python

# Requirements
Be sure to install Python (https://www.python.org/downloads/).

# Execute the script
The script can be run by executing the caommand:
```
$ python3 beetle-battle.py
```

# Create executable
The Python script can be packaged into an executable using the ``pyinstaller`` tool (see https://pyinstaller.org). This tool can be installed by executing the following command:
```
$ pip install pyinstaller
```

When the tool is installed, an executable can be created by executing the following command:
```
$ pyinstaller Beetle\ Battle.spec 
```

This will create an executable in the `dist` folder. On OS X this is the ``Beetle Battle.app`` package which is an macOS app that can be executed and copied in your applications folder.