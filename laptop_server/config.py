# ============================================================
#  Medicare Robot - Laptop Server Configuration
# ============================================================

# ---- Raspberry Pi Connection ----
RASPBERRY_PI_IP = "10.110.46.3"       # Your Pi's IP address (change this!)
STREAM_PORT = 8080                       # Must match Pi's STREAM_PORT
VIDEO_STREAM_URL = f"http://{RASPBERRY_PI_IP}:{STREAM_PORT}/video_feed"

# ---- YOLO Settings ----
YOLO_MODEL = "yolov8n.pt"               # Nano model (fastest, smallest)
YOLO_CONFIDENCE = 0.45                   # Minimum confidence threshold
YOLO_IOU_THRESHOLD = 0.5                # IoU threshold for NMS

# ---- MediaPipe Settings ----
MEDIAPIPE_DETECTION_CONFIDENCE = 0.5
MEDIAPIPE_TRACKING_CONFIDENCE = 0.5

# ---- Display Settings ----
WINDOW_NAME = "Medicare Robot - Detection View"
DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720
SHOW_FPS = True

# ---- Detection Mode ----
# Options: "yolo", "mediapipe", "both"
DETECTION_MODE = "both"

# ---- Colors (BGR format for OpenCV) ----
COLOR_YOLO_BOX = (0, 255, 0)            # Green for YOLO detections
COLOR_MEDIAPIPE = (255, 0, 128)          # Pink for MediaPipe
COLOR_FPS = (0, 255, 255)               # Yellow for FPS counter
COLOR_PERSON = (0, 128, 255)            # Orange for person detection
COLOR_LABEL_BG = (0, 0, 0)             # Black background for labels
FONT_SCALE = 0.6
FONT_THICKNESS = 2

# ---- Recording (optional) ----
RECORD_OUTPUT = False
RECORD_FILENAME = "detection_output.avi"
RECORD_FPS = 20
