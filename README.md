# Beetle Battle
Beetle Battle board game in Python. Refer to "[Beetle Battle manual](manual)" for the manual. 

## Requirements
Be sure to install Python (https://www.python.org/downloads/).

## Execute the script
The script can be run by executing the command:
```
$ python3 app.py
```

## Create executable
The Python script can be packaged into an executable using the ``pyinstaller`` tool (see https://pyinstaller.org). This tool can be installed by executing the following command:
```
$ pip install pyinstaller
```

When the tool is installed, an executable can be created by executing the following command:
```
$ python3 -m PyInstaller "Beetle Battle.spec" 
```

This will create an executable in the `dist` folder. On OS X this is the ``Beetle Battle.app`` package which is an macOS app that can be executed and copied in your applications folder.

## Limited version
A limitited version of a 11x11 2 player version is implemented in [beetle_battle.py](beetle_battle.py).

## HTML version

An HTML/CSS/JavaScipt version of the 11x11 2-player version of the game was made.

**Click [here](https://htmlpreview.github.io/?https://raw.githubusercontent.com/computerguided/beetle-battle/refs/heads/main/beetle_battle.html) to run the game in your browser.**
