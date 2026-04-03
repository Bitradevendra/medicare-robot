# ============================================================
#  Medicare Robot - Main Controller (Script 2)
#  Run this separately: python robot.py
#  Handles: Voice → Commands → Motors/Servo → Gemini → Speaker
# ============================================================

import os
import sys
import time
import subprocess
import speech_recognition as sr
from gtts import gTTS

from config import (
    SAMPLE_RATE, LISTEN_TIMEOUT, PHRASE_TIME_LIMIT,
    SERVO_PIN, SERVO_BOX_1, SERVO_BOX_2, SERVO_BOX_3,
    MOTOR_A_IN1, MOTOR_A_IN2, MOTOR_B_IN1, MOTOR_B_IN2,
    GEMINI_API_KEY, GEMINI_MODEL, GEMINI_SYSTEM_PROMPT,
    TTS_LANGUAGE, AUDIO_TEMP_FILE,
)

# ---- GPIO Setup ----
try:
    import RPi.GPIO as GPIO
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    # Motors
    for pin in [MOTOR_A_IN1, MOTOR_A_IN2, MOTOR_B_IN1, MOTOR_B_IN2]:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

    # Servo
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    servo_pwm = GPIO.PWM(SERVO_PIN, 50)
    servo_pwm.start(0)

    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False

# ---- Gemini Setup ----
gemini_chat = None
try:
    from google import genai
    from google.genai import types

    if GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
        client = genai.Client(api_key=GEMINI_API_KEY)
        gemini_chat = client.chats.create(
            model=GEMINI_MODEL,
            config=types.GenerateContentConfig(
                system_instruction=GEMINI_SYSTEM_PROMPT
            )
        )
except Exception as e:
    print(f"  ⚠  Gemini error: {e}")


# ============================================================
#  Motor Functions
# ============================================================

def motors_forward():
    if HAS_GPIO:
        GPIO.output(MOTOR_A_IN1, GPIO.HIGH)
        GPIO.output(MOTOR_A_IN2, GPIO.LOW)
        GPIO.output(MOTOR_B_IN1, GPIO.HIGH)
        GPIO.output(MOTOR_B_IN2, GPIO.LOW)


def motors_backward():
    if HAS_GPIO:
        GPIO.output(MOTOR_A_IN1, GPIO.LOW)
        GPIO.output(MOTOR_A_IN2, GPIO.HIGH)
        GPIO.output(MOTOR_B_IN1, GPIO.LOW)
        GPIO.output(MOTOR_B_IN2, GPIO.HIGH)


def motors_left():
    if HAS_GPIO:
        GPIO.output(MOTOR_A_IN1, GPIO.LOW)
        GPIO.output(MOTOR_A_IN2, GPIO.LOW)
        GPIO.output(MOTOR_B_IN1, GPIO.HIGH)
        GPIO.output(MOTOR_B_IN2, GPIO.LOW)


def motors_right():
    if HAS_GPIO:
        GPIO.output(MOTOR_A_IN1, GPIO.HIGH)
        GPIO.output(MOTOR_A_IN2, GPIO.LOW)
        GPIO.output(MOTOR_B_IN1, GPIO.LOW)
        GPIO.output(MOTOR_B_IN2, GPIO.LOW)


def motors_stop():
    if HAS_GPIO:
        GPIO.output(MOTOR_A_IN1, GPIO.LOW)
        GPIO.output(MOTOR_A_IN2, GPIO.LOW)
        GPIO.output(MOTOR_B_IN1, GPIO.LOW)
        GPIO.output(MOTOR_B_IN2, GPIO.LOW)


# ============================================================
#  Servo Functions
# ============================================================

def servo_move(angle):
    if HAS_GPIO:
        duty = 2.5 + (angle / 180.0) * 10.0
        servo_pwm.ChangeDutyCycle(duty)
        time.sleep(0.5)
        servo_pwm.ChangeDutyCycle(0)


def servo_box(box_num):
    angles = {1: SERVO_BOX_1, 2: SERVO_BOX_2, 3: SERVO_BOX_3}
    if box_num in angles:
        servo_move(angles[box_num])


# ============================================================
#  Speaker Functions
# ============================================================

def speak(text):
    """Convert text to speech and play it."""
    if not text:
        return
    try:
        tts = gTTS(text=text, lang=TTS_LANGUAGE, slow=False)
        tts.save(AUDIO_TEMP_FILE)
        # Try mpg321 first, then mpg123
        try:
            subprocess.run(["mpg321", "-q", AUDIO_TEMP_FILE],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        except FileNotFoundError:
            subprocess.run(["mpg123", "-q", AUDIO_TEMP_FILE],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    except Exception as e:
        print(f"  ⚠  Speaker error: {e}")
    finally:
        if os.path.exists(AUDIO_TEMP_FILE):
            os.remove(AUDIO_TEMP_FILE)


# ============================================================
#  Gemini Functions
# ============================================================

def ask_gemini(question):
    """Send question to Gemini and return response."""
    if not gemini_chat:
        return "Sorry, AI service is not available."
    try:
        response = gemini_chat.send_message(question)
        return response.text.strip()
    except Exception as e:
        return f"Sorry, error occurred: {e}"


# ============================================================
#  Voice Listening
# ============================================================

def listen(recognizer, microphone):
    """Listen for speech and return recognized text (or None)."""
    try:
        with microphone as source:
            audio = recognizer.listen(source, timeout=LISTEN_TIMEOUT,
                                      phrase_time_limit=PHRASE_TIME_LIMIT)
        text = recognizer.recognize_google(audio)
        return text.lower().strip()
    except sr.WaitTimeoutError:
        return None
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        print("  ⚠  No internet! Check WiFi")
        return None
    except Exception:
        return None


# ============================================================
#  Command Matching
# ============================================================

COMMANDS = {
    # Wake word
    "hello": "hello",
    "hey": "hello",

    # Movement
    "come here": "forward",
    "move forward": "forward",
    "go forward": "forward",
    "come back": "backward",
    "go back": "backward",
    "move backward": "backward",
    "turn left": "left",
    "go left": "left",
    "turn right": "right",
    "go right": "right",
    "stop": "stop",
    "halt": "stop",

    # Servo
    "box one": "box_1",
    "box 1": "box_1",
    "box two": "box_2",
    "box 2": "box_2",
    "box three": "box_3",
    "box 3": "box_3",
}


def match_command(text):
    """Match text to a command. Returns command string or None."""
    if not text:
        return None
    for phrase, cmd in COMMANDS.items():
        if phrase in text:
            return cmd
    return None


# ============================================================
#  Main Loop
# ============================================================

def main():
    print()
    print("=" * 50)
    print("  🤖  MEDICARE ROBOT")
    print("=" * 50)

    # Status
    print(f"  {'✅' if HAS_GPIO else '⚠️'}  GPIO: {'Ready' if HAS_GPIO else 'Simulation mode'}")
    print(f"  {'✅' if gemini_chat else '⚠️'}  Gemini: {'Ready' if gemini_chat else 'Not configured'}")

    # Setup voice
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    microphone = sr.Microphone(sample_rate=SAMPLE_RATE)

    print("  ⏳  Calibrating microphone...")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=2)

    print("  ✅  Microphone ready")
    print()
    print("=" * 50)
    print("  🎤  Listening for commands...")
    print("=" * 50)
    print()

    try:
        while True:
            # Listen
            text = listen(recognizer, microphone)
            if text is None:
                continue

            # Match command
            cmd = match_command(text)

            if cmd is None:
                print(f"  👂  Heard: \"{text}\" (not a command)")
                continue

            # ---- Execute command ----

            if cmd == "hello":
                print(f"  🗣️  Wake word detected!")
                speak("yes?")
                print(f"  🎤  Listening for your question...")
                question = listen(recognizer, microphone)
                if question:
                    print(f"  💬  Question: \"{question}\"")
                    print(f"  ⏳  Thinking...")
                    answer = ask_gemini(question)
                    print(f"  🤖  Answer: \"{answer}\"")
                    speak(answer)
                else:
                    print(f"  ❌  No question heard")
                print()

            elif cmd == "forward":
                print(f"  🏃  Moving forward")
                motors_forward()

            elif cmd == "backward":
                print(f"  🔙  Moving backward")
                motors_backward()

            elif cmd == "left":
                print(f"  ⬅️  Turning left")
                motors_left()

            elif cmd == "right":
                print(f"  ➡️  Turning right")
                motors_right()

            elif cmd == "stop":
                print(f"  🛑  Stopped")
                motors_stop()

            elif cmd == "box_1":
                print(f"  💊  Servo → Box 1 (0°)")
                speak("Moving to box one")
                servo_box(1)

            elif cmd == "box_2":
                print(f"  💊  Servo → Box 2 (30°)")
                speak("Moving to box two")
                servo_box(2)

            elif cmd == "box_3":
                print(f"  💊  Servo → Box 3 (60°)")
                speak("Moving to box three")
                servo_box(3)

    except KeyboardInterrupt:
        print()
        print("=" * 50)
        print("  🤖  Shutting down...")
        motors_stop()
        if HAS_GPIO:
            servo_pwm.stop()
            GPIO.cleanup()
        print("  ✅  Goodbye!")
        print("=" * 50)


if __name__ == "__main__":
    main()
