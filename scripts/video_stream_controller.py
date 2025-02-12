import subprocess
import time

class VideoStreamController:
    _process : subprocess.Popen
    _stream_url : str

    def __init__(self):
        self._process = None
        self._stream_url = None
        self._token = None

    def _start_stream(self, url, stream_key) -> None:
        url_with_key = f"{url}?key={stream_key}"
        
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
        url_with_key
    ])
        print("Started stream at : ", url)

    def set_stream_url_if_changed(self, url) -> None:
        if(self._stream_url == url):
            return
        
        self._stream_url = url
        if(self.is_streaming()):
            self.stop_stream()
            self._start_stream(url)

    def set_stream_key(self, token) -> None:
        self._token = token

    def stop_stream(self) -> None:
        if self._process is None:
            return
        
        self._process.kill()
        self._process = None
        print("Stopped stream")

    def handle_stream_state(self, stream_until, stream_key) -> None:
        if(self._stream_url is None or stream_key is None):
            return

        if(self.is_streaming() and self._process.poll() is not None):
            print("Stream stopped unexpectedly, restarting...")
            self.stop_stream()
            self._start_stream(self._stream_url, stream_key)

        if(stream_until > time.time() and not self.is_streaming()):
            self._start_stream(self._stream_url, stream_key)
        elif(stream_until < time.time() and self.is_streaming()):
            self.stop_stream()

    def is_streaming(self):
        return self._process is not None