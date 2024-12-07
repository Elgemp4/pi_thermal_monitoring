#!/bin/bash

# Define the path to your virtual environment and your main Python script
VENV_DIR="/usr/local/bin/pi-therm-monitoring/venv"
MAIN_SCRIPT="/usr/local/bin/pi-therm-monitoring/main.py"
sudo modprobe v4l2loopback video_nr=59 card_label="VirtualCam"
# Run the Python program
"$VENV_DIR/bin/python" "$MAIN_SCRIPT"

ffmpeg -f v4l2 -i /dev/video59 -c:v libx264 -preset ultrafast -tune zerolatency -g 25 -keyint_min 25 -sc_threshold 0 -hls_time 1 -hls_list_size 3 -hls_flags delete_segments -hls_segment_type mpegts  -f flv rtmp://node.elgem.be/show/stream
