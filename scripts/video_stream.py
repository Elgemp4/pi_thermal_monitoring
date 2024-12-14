import subprocess

_process = None

def start_stream(url):
    global _process
    _process = subprocess.Popen([
    "ffmpeg",
    "-f", "v4l2",
    "-i", "/dev/video59",
    "-c:v", "libx264",
    "-preset", "ultrafast",
    "-tune", "zerolatency",
    "-g", "25",
    "-keyint_min", "25",
    "-sc_threshold", "0",
    "-hls_time", "1",
    "-hls_list_size", "3",
    "-hls_flags", "delete_segments",
    "-hls_segment_type", "mpegts",
    "-f", "flv",
    "rtmp://node.elgem.be/show/stream"
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Started stream at : ", url)

def stop_stream():
    global _process
    _process.kill()
    _process = None

    print("Stopped stream")

def is_streaming():
    return _process is not None