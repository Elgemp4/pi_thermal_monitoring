#!/bin/bash

# Define the path to your virtual environment and your main Python script
VENV_DIR="/usr/local/bin/pi-therm-monitoring/venv"
MAIN_SCRIPT="/usr/local/bin/pi-therm-monitoring/main.py"
sudo modprobe v4l2loopback video_nr=59 card_label="VirtualCam"
# Run the Python program
"$VENV_DIR/bin/python" "$MAIN_SCRIPT"