# ============================================================
#  Medicare Robot - Configuration
# ============================================================

# ---- Network ----
LAPTOP_IP = "10.110.128.3"         # Your laptop's IP (change this!)
STREAM_PORT = 8080                  # Video stream port

# ---- Camera (optimized for Pi 3B+) ----
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
CAMERA_FPS = 15
JPEG_QUALITY = 50

# ---- Servo Motor (SG90) ----
SERVO_PIN = 18                      # GPIO 18 (PWM0)
SERVO_BOX_1 = 0                     # Box 1 -> 0 degrees
SERVO_BOX_2 = 30                    # Box 2 -> 30 degrees
SERVO_BOX_3 = 60                    # Box 3 -> 60 degrees

# ---- DC Motors (L298N) ----
MOTOR_A_IN1 = 17                    # Left wheel
MOTOR_A_IN2 = 27
MOTOR_B_IN1 = 23                    # Right wheel
MOTOR_B_IN2 = 24

# ---- Voice ----
SAMPLE_RATE = 16000
LISTEN_TIMEOUT = 5
PHRASE_TIME_LIMIT = 8

# ---- Gemini API ----
GEMINI_API_KEY = "AIzaSyAp4N0GUh9i1iBlgpWkfTlDkdSnKaCwknE"
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_SYSTEM_PROMPT = (
    "You ARE a Medicare robot. You are a real, physical medical care robot "
    "working in a hospital. You have wheels, a medicine dispenser with 3 boxes, "
    "a camera, and a speaker. Speak warmly like a caring nurse. "
    "Never say you are an AI. You are 'Medicare Robot'. "
    "Keep responses short (2-3 sentences), clear, and comforting."
)

# ---- Text-to-Speech ----
TTS_LANGUAGE = "en"
AUDIO_TEMP_FILE = "/tmp/tts_output.mp3"
