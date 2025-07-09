#!/bin/bash
# This command builds the main.py file into an executable
pyinstaller --onefile --hidden-import=tkinter --hidden-import=PIL._tkinter_finder main.py