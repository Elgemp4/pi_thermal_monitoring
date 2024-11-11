#!/bin/bash

# Define the path to your virtual environment and your main Python script
VENV_DIR=/usr/local/bin/pi-therm-monitoring/venv
MAIN_SCRIPT=/usr/local/bin/pi-therm-monitoring/main.py

# Activate the virtual environment
source $VENV_DIR/bin/activate

# Run the Python program
python $MAIN_SCRIPT "$@"

# Deactivate the virtual environment after the script finishes
deactivate
