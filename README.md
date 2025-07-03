This is a project to turn an SVG into gCode that a 3d Printer can draw out

The GUI allows you to import a SVG, rotate, scale, and translate it. Then export it as a gcode file

# Instalation

First download a copy of the repo

## .exe

- If on windows you can run the exe in {path-to-repo}/build/main

## From source

- To build from source you must have python installed on your sytem

1. Navigate to the folder containing the repo in a terminal
2. run ```pip install -r requirements.txt``` to download the dependancies
3. run ```python source/main.py``` to run the project


# General

- Please create an issue if there is a SVG that does not parse correctly so I can fix any bugs
- I plan on adding support for other formats like PNG and JPEG in the future