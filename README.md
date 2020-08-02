# Dim

Simple terminal text editor based on Vim

# Installation

## Precompiled Binary

There are two zip files that you can download for Windows and Mac/Linux and then extract in the releases tab. The executables can be found inside the folders.

There may also be zip files which contain compiled binaries that are bound inside a single executable. These executables seem to be significantly slower than the multifile version.

## Building Manually

First, download or clone this repository and navigate into the main folder with Python 3 and Pip installed.

To launch the editor with Python, run the following command.

```bash
python src/dim.py
```

To build the executable yourself, run the following commands.

Note: you may want to use a virtual environment to install these dependencies.

```bash
# Windows:
pip install windows-curses
pip install pyinstaller # or a similar tool
pyinstaller src/dim.py --add-data "src/debug/*;debug" --add-data "src/tutorial/*;tutorial"
# Mac/Linux
pip install pyinstaller # or a similar tool
pyinstaller src/dim.py --add-data "src/debug/*:debug" --add-data "src/tutorial/*:tutorial"
```

This should build a dist folder and inside it a dim folder. Your executable will be found in the dim folder.
