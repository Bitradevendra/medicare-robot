# ============================================================
#  Medicare Robot - Video Streamer
#  Streams webcam video via MJPEG over HTTP to laptop server
# ============================================================

import time
import threading

import cv2
from flask import Flask, Response

from config import (
    CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS,
    JPEG_QUALITY, STREAM_PORT, PI_IP
)


class VideoStreamer:
    """Streams webcam video as MJPEG over HTTP for laptop processing."""

    def __init__(self):
        self.app = Flask(__name__)
        self.camera = None
        self.is_streaming = False
        self.frame = None
        self.lock = threading.Lock()
        self._server_thread = None

        # Setup Flask route
        self.app.add_url_rule("/video_feed", "video_feed", self._video_feed)
        self.app.add_url_rule("/", "index", self._index)

    def _index(self):
        """Simple status page."""
        return """
        <html>
        <head><title>Medicare Robot - Video Stream</title></head>
        <body style="background:#111;color:#0f0;font-family:monospace;text-align:center;padding:40px">
            <h1>🤖 Medicare Robot Video Stream</h1>
            <p>Stream is active!</p>
            <img src="/video_feed" style="max-width:90%;border:2px solid #0f0;border-radius:8px">
        </body>
        </html>
        """

    def _init_camera(self):
        """Initialize the webcam."""
        print("[STREAM] Initializing camera...")
        self.camera = cv2.VideoCapture(0)

        if not self.camera.isOpened():
            # Try different camera indices
            for idx in [1, 2, -1]:
                self.camera = cv2.VideoCapture(idx)
                if self.camera.isOpened():
                    break

        if not self.camera.isOpened():
            print("[STREAM] ERROR: Could not open camera!")
            return False

        # Set camera properties for performance
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        self.camera.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency

        actual_w = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"[STREAM] Camera opened: {actual_w}x{actual_h}")
        return True

    def _capture_loop(self):
        """Continuously capture frames from camera."""
        print("[STREAM] Starting capture loop...")
        frame_delay = 1.0 / CAMERA_FPS  # Limit capture rate to save CPU

        while self.is_streaming:
            if self.camera and self.camera.isOpened():
                ret, frame = self.camera.read()
                if ret:
                    with self.lock:
                        self.frame = frame
                time.sleep(frame_delay)  # Rate limit to save CPU on Pi 3B+
            else:
                time.sleep(0.1)

    def _generate_frames(self):
        """Generator that yields MJPEG frames."""
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]

        while self.is_streaming:
            with self.lock:
                frame = self.frame

            if frame is not None:
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame, encode_params)
                if ret:
                    yield (
                        b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' +
                        buffer.tobytes() +
                        b'\r\n'
                    )
            else:
                time.sleep(0.01)

    def _video_feed(self):
        """Flask route for MJPEG video feed."""
        return Response(
            self._generate_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )

    def start(self):
        """Start the video streaming server."""
        if self.is_streaming:
            print("[STREAM] Already streaming")
            return

        if not self._init_camera():
            return

        self.is_streaming = True

        # Start frame capture thread
        capture_thread = threading.Thread(
            target=self._capture_loop,
            daemon=True,
            name="CaptureLoop"
        )
        capture_thread.start()

        # Start Flask server in background thread
        self._server_thread = threading.Thread(
            target=lambda: self.app.run(
                host=PI_IP,
                port=STREAM_PORT,
                threaded=True,
                use_reloader=False
            ),
            daemon=True,
            name="StreamServer"
        )
        self._server_thread.start()

        print(f"[STREAM] 📹 Video stream active at http://<PI_IP>:{STREAM_PORT}/video_feed")

    def stop(self):
        """Stop the video streaming server."""
        self.is_streaming = False
        if self.camera:
            self.camera.release()
        print("[STREAM] Stopped streaming")

    def get_current_frame(self):
        """Get the current frame (for local use if needed)."""
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def cleanup(self):
        """Clean up resources."""
        self.stop()
        print("[STREAM] Cleaned up")


if __name__ == "__main__":
    streamer = VideoStreamer()
    try:
        streamer.start()
        print(f"Stream at: http://localhost:{STREAM_PORT}/video_feed")
        print("Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        streamer.cleanup()
