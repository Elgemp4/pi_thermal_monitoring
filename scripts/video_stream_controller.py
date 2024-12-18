import subprocess
import time

class VideoStreamController:
    _process : subprocess.Popen
    _stream_url : str

    def __init__(self, stream_url):
        self._process = None
        self._stream_url = stream_url

    def _start_stream(self, url) -> None:
        self._process = subprocess.Popen([
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

    def set_stream_url(self, url) -> None:
        self._stream_url = url
        if(self.is_streaming()):
            self.stop_stream()
            self._start_stream(url)

    def stop_stream(self) -> None:
        if self._process is None:
            return
        
        self._process.kill()
        self._process = None
        print("Stopped stream")

    def handle_stream_state(self, stream_until) -> None:
        if(self.is_streaming() and self._process.poll() is not None):
            print("Stream stopped unexpectedly, restarting...")
            self.stop_stream()
            self._start_stream(self._stream_url)

        if(stream_until > time.time() and not self.is_streaming()):
            self._start_stream(self._stream_url)
        elif(stream_until < time.time() and self.is_streaming()):
            self.stop_stream()

    def is_streaming(self):
        return self._process is not None