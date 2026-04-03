# ============================================================
#  Medicare Robot - Laptop Detection Server (OPTIMIZED)
#  Receives video stream from Pi, runs YOLO + MediaPipe
#  Displays live annotated view with object/person detection
#  
#  Optimizations:
#  - Detection runs every Nth frame (skip frames for speed)
#  - YOLO runs on small frame, results scaled to display
#  - MediaPipe uses model_complexity=0 (fastest)
#  - Only Pose detection (Face + Hands removed for speed)
#  - Display and detection are decoupled
# ============================================================

import sys
import time
import cv2
import numpy as np
from collections import deque

from config import (
    VIDEO_STREAM_URL, DETECTION_MODE,
    YOLO_MODEL, YOLO_CONFIDENCE, YOLO_IOU_THRESHOLD,
    MEDIAPIPE_DETECTION_CONFIDENCE, MEDIAPIPE_TRACKING_CONFIDENCE,
    WINDOW_NAME, DISPLAY_WIDTH, DISPLAY_HEIGHT, SHOW_FPS,
    COLOR_YOLO_BOX, COLOR_MEDIAPIPE, COLOR_FPS,
    COLOR_PERSON, COLOR_LABEL_BG,
    FONT_SCALE, FONT_THICKNESS,
    RECORD_OUTPUT, RECORD_FILENAME, RECORD_FPS,
)

# How often to run detection (1 = every frame, 3 = every 3rd frame)
DETECT_EVERY_N_FRAMES = 3


class YOLODetector:
    """YOLOv8 object detection wrapper."""

    def __init__(self):
        from ultralytics import YOLO
        print("[YOLO] Loading model: " + YOLO_MODEL)
        self.model = YOLO(YOLO_MODEL)
        print("[YOLO] Model loaded")

    def detect(self, frame):
        """Run YOLO on frame. Returns list of (class_name, conf, x1, y1, x2, y2)."""
        results = self.model.predict(
            frame,
            conf=YOLO_CONFIDENCE,
            iou=YOLO_IOU_THRESHOLD,
            verbose=False,
            imgsz=320,  # Run inference at small size for speed
        )

        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    cls_name = self.model.names[cls_id]
                    detections.append((cls_name, conf, x1, y1, x2, y2))

        return detections


class MediaPipeDetector:
    """MediaPipe pose detection only (fastest config)."""

    def __init__(self):
        import mediapipe as mp
        self.mp = mp
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_draw_styles = mp.solutions.drawing_styles

        # Pose only (model_complexity=0 = fastest)
        self.pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=0,  # 0=lite, 1=full, 2=heavy
            min_detection_confidence=MEDIAPIPE_DETECTION_CONFIDENCE,
            min_tracking_confidence=MEDIAPIPE_TRACKING_CONFIDENCE,
        )

        print("[MEDIAPIPE] Initialized (Pose only, lite model)")

    def detect(self, frame):
        """Run pose detection. Returns annotated frame and person boxes."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        annotated = frame.copy()
        persons = []
        h, w, _ = frame.shape

        result = self.pose.process(rgb)
        if result.pose_landmarks:
            self.mp_draw.draw_landmarks(
                annotated,
                result.pose_landmarks,
                self.mp.solutions.pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_draw_styles.get_default_pose_landmarks_style()
            )

            landmarks = result.pose_landmarks.landmark
            x_coords = [lm.x for lm in landmarks if lm.visibility > 0.5]
            y_coords = [lm.y for lm in landmarks if lm.visibility > 0.5]

            if x_coords and y_coords:
                x1 = int(min(x_coords) * w) - 20
                y1 = int(min(y_coords) * h) - 20
                x2 = int(max(x_coords) * w) + 20
                y2 = int(max(y_coords) * h) + 20
                persons.append(("Person", x1, y1, x2, y2))

        return annotated, persons

    def cleanup(self):
        self.pose.close()


class DetectionServer:
    """Main detection server - YOLO + MediaPipe with frame skipping."""

    def __init__(self):
        print("=" * 50)
        print("  MEDICARE ROBOT - Detection Server")
        print("=" * 50)

        self.yolo = None
        self.mediapipe = None
        self.cap = None
        self.fps_history = deque(maxlen=30)
        self.writer = None

        if DETECTION_MODE in ("yolo", "both"):
            self.yolo = YOLODetector()

        if DETECTION_MODE in ("mediapipe", "both"):
            self.mediapipe = MediaPipeDetector()

    def _draw_yolo(self, frame, detections):
        """Draw YOLO boxes on frame."""
        for cls_name, conf, x1, y1, x2, y2 in detections:
            color = COLOR_PERSON if cls_name == "person" else COLOR_YOLO_BOX

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            label = f"{cls_name} {conf:.0%}"
            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE, FONT_THICKNESS)
            cv2.rectangle(frame, (x1, y1 - lh - 10), (x1 + lw + 10, y1), color, -1)
            cv2.putText(frame, label, (x1 + 5, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE, (255, 255, 255), FONT_THICKNESS)

        return frame

    def _draw_overlay(self, frame, fps, count):
        """Draw FPS and info bar."""
        h, w, _ = frame.shape

        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 40), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        cv2.putText(frame, "MEDICARE ROBOT", (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        if SHOW_FPS:
            cv2.putText(frame, f"FPS: {fps:.0f}", (w - 120, 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_FPS, 2)

        cv2.putText(frame, f"Objects: {count}", (w - 260, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        return frame

    def connect(self):
        """Connect to Pi stream."""
        print(f"\n  Connecting: {VIDEO_STREAM_URL}")
        self.cap = cv2.VideoCapture(VIDEO_STREAM_URL)

        if not self.cap.isOpened():
            print("  ❌  Failed to connect!")
            return False

        print("  ✅  Connected!")
        return True

    def run(self):
        """Main loop with frame skipping for speed."""
        if not self.connect():
            print("  Retrying in 5s...")
            time.sleep(5)
            if not self.connect():
                print("  ❌  Could not connect. Exiting.")
                return

        if RECORD_OUTPUT:
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.writer = cv2.VideoWriter(RECORD_FILENAME, fourcc, RECORD_FPS,
                                          (DISPLAY_WIDTH, DISPLAY_HEIGHT))

        print(f"\n  Detection running (every {DETECT_EVERY_N_FRAMES} frames)")
        print("  Q=quit  M=mode  S=screenshot\n")

        mode = DETECTION_MODE
        frame_num = 0
        total_frames = 0
        start = time.time()

        # Cache last detection results
        last_yolo = []
        last_persons = []

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("  ⚠  Lost stream. Reconnecting...")
                time.sleep(2)
                self.cap = cv2.VideoCapture(VIDEO_STREAM_URL)
                continue

            t0 = time.time()

            # Resize for display
            display = cv2.resize(frame, (DISPLAY_WIDTH, DISPLAY_HEIGHT))

            # --- Run detection only every Nth frame ---
            run_detection = (frame_num % DETECT_EVERY_N_FRAMES == 0)

            if run_detection:
                total_detections = 0

                # YOLO - run on original small frame for speed
                if self.yolo and mode in ("yolo", "both"):
                    last_yolo = self.yolo.detect(display)

                # MediaPipe
                if self.mediapipe and mode in ("mediapipe", "both"):
                    display, last_persons = self.mediapipe.detect(display)

            # --- Always draw last known detections ---
            if self.yolo and mode in ("yolo", "both"):
                display = self._draw_yolo(display, last_yolo)

            # Draw person boxes from MediaPipe
            if last_persons and mode in ("mediapipe", "both"):
                for label, x1, y1, x2, y2 in last_persons:
                    cv2.rectangle(display, (x1, y1), (x2, y2), COLOR_PERSON, 2)
                    cv2.putText(display, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE, COLOR_PERSON, FONT_THICKNESS)

            # FPS
            dt = time.time() - t0
            fps = 1.0 / max(dt, 0.001)
            self.fps_history.append(fps)
            avg_fps = sum(self.fps_history) / len(self.fps_history)

            count = len(last_yolo) + len(last_persons)
            display = self._draw_overlay(display, avg_fps, count)

            cv2.imshow(WINDOW_NAME, display)

            if self.writer:
                self.writer.write(display)

            # Keyboard
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q'):
                break
            elif key == ord('m') or key == ord('M'):
                modes = ["yolo", "mediapipe", "both"]
                idx = modes.index(mode)
                mode = modes[(idx + 1) % len(modes)]
                last_yolo = []
                last_persons = []
                print(f"  Mode: {mode.upper()}")
            elif key == ord('s') or key == ord('S'):
                name = f"screenshot_{int(time.time())}.jpg"
                cv2.imwrite(name, display)
                print(f"  Screenshot: {name}")

            frame_num += 1
            total_frames += 1

        elapsed = time.time() - start
        print(f"\n  {total_frames} frames in {elapsed:.1f}s (avg {total_frames/max(elapsed,1):.1f} FPS)")
        self.cleanup()

    def cleanup(self):
        if self.cap:
            self.cap.release()
        if self.writer:
            self.writer.release()
        if self.mediapipe:
            self.mediapipe.cleanup()
        cv2.destroyAllWindows()
        print("  Cleaned up")


def main():
    server = DetectionServer()
    try:
        server.run()
    except KeyboardInterrupt:
        print("\n  Interrupted")
        server.cleanup()


if __name__ == "__main__":
    main()
