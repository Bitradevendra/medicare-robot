# ============================================================
#  Medicare Robot - Video Streamer (Script 1)
#  Run this separately: python stream.py
#  Streams webcam to laptop via MJPEG - runs independently
# ============================================================

import time
import threading
import cv2
from flask import Flask, Response
from config import CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS, JPEG_QUALITY, STREAM_PORT

app = Flask(__name__)
frame = None
lock = threading.Lock()
streaming = True


def capture_loop(camera):
    """Capture frames from camera continuously."""
    global frame
    delay = 1.0 / CAMERA_FPS

    while streaming:
        ret, f = camera.read()
        if ret:
            with lock:
                frame = f
        time.sleep(delay)


def generate():
    """Yield MJPEG frames."""
    params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]

    while streaming:
        with lock:
            f = frame

        if f is not None:
            ret, buf = cv2.imencode('.jpg', f, params)
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' +
                       buf.tobytes() + b'\r\n')
        else:
            time.sleep(0.05)


@app.route('/video_feed')
def video_feed():
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    return '<html><body style="background:#111;color:#0f0;text-align:center;padding:40px;font-family:monospace">' \
           '<h1>Medicare Robot Stream</h1>' \
           '<img src="/video_feed" style="max-width:90%;border:2px solid #0f0;border-radius:8px"></body></html>'


def main():
    print("=" * 50)
    print("  📹  VIDEO STREAMER")
    print("=" * 50)

    # Open camera
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        for idx in [1, 2, -1]:
            camera = cv2.VideoCapture(idx)
            if camera.isOpened():
                break

    if not camera.isOpened():
        print("  ❌  Camera not found!")
        return

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    camera.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    w = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"  ✅  Camera: {w}x{h}")
    print(f"  ✅  Stream: http://<PI_IP>:{STREAM_PORT}/video_feed")
    print("=" * 50)
    print()

    # Start capture thread
    t = threading.Thread(target=capture_loop, args=(camera,), daemon=True)
    t.start()

    # Start Flask (suppress logs)
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    try:
        app.run(host='0.0.0.0', port=STREAM_PORT, threaded=True, use_reloader=False)
    except KeyboardInterrupt:
        pass
    finally:
        global streaming
        streaming = False
        camera.release()
        print("\n  📹  Stream stopped")


if __name__ == "__main__":
    main()
