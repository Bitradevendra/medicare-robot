# ============================================================
#  Medicare Robot - Main Controller (Raspberry Pi)
#  Orchestrates all modules: voice, motors, servo, AI, stream
# ============================================================

import sys
import time
import signal
import threading

from config import STREAM_PORT
from servo_controller import ServoController
from motor_controller import MotorController
from voice_controller import VoiceController
from gemini_handler import GeminiHandler
from audio_output import AudioOutput
from video_streamer import VideoStreamer


class MedicareRobot:
    """Main robot controller - orchestrates all subsystems."""

    def __init__(self):
        print("=" * 60)
        print("  🤖  MEDICARE ROBOT - Initializing...")
        print("=" * 60)
        print()

        # Initialize all controllers
        self.servo = ServoController()
        self.motors = MotorController()
        self.gemini = GeminiHandler()
        self.streamer = VideoStreamer()
        self.voice = VoiceController(callback=self._on_voice_command)

        # Audio needs voice controller reference to mute mic during speech
        self.audio = AudioOutput(voice_controller=self.voice)

        # State
        self.running = False
        self._command_lock = threading.Lock()

        print()
        print("=" * 60)
        print("  ✅  All systems initialized!")
        print("=" * 60)
        print()

    def _on_voice_command(self, command, raw_text):
        """
        Handle recognized voice commands.
        Called from the voice controller thread.
        """
        with self._command_lock:
            print(f"\n[ROBOT] ⚡ Command: {command} (from: '{raw_text}')")

            if command == "wake_word":
                self._handle_wake_word()

            elif command == "box_1":
                self.audio.play_confirmation("box_1")
                self.servo.go_to_box(1)

            elif command == "box_2":
                self.audio.play_confirmation("box_2")
                self.servo.go_to_box(2)

            elif command == "box_3":
                self.audio.play_confirmation("box_3")
                self.servo.go_to_box(3)

            elif command == "move_forward":
                self.audio.play_confirmation("move_forward")
                self.motors.move_forward()

            elif command == "move_backward":
                self.audio.play_confirmation("move_backward")
                self.motors.move_backward()

            elif command == "turn_left":
                self.audio.play_confirmation("turn_left")
                self.motors.turn_left()

            elif command == "turn_right":
                self.audio.play_confirmation("turn_right")
                self.motors.turn_right()

            elif command == "stop":
                self.motors.stop()
                self.audio.play_confirmation("stop")

            else:
                print(f"[ROBOT] Unknown command: {command}")

    def _handle_wake_word(self):
        """Handle the 'hello' wake word - enter AI conversation mode."""
        print("[ROBOT] 🗣️  Wake word detected! Entering conversation mode...")
        self.audio.play_beep()

        # Tell voice controller to capture next phrase for Gemini
        self.voice.enter_conversation_mode(self._handle_conversation)

    def _handle_conversation(self, question):
        """Handle a conversation question - send to Gemini and speak response."""
        print(f"[ROBOT] 💬 User asked: '{question}'")

        # Get response from Gemini
        response = self.gemini.ask(question)

        # Speak the response through Bluetooth speaker
        self.audio.speak(response)

        print("[ROBOT] Back to command listening mode")

    def start(self):
        """Start all robot systems."""
        self.running = True

        print("[ROBOT] Starting all systems...")
        print()

        # Start video streaming to laptop
        self.streamer.start()
        print(f"[ROBOT] 📹 Video stream: http://<PI_IP>:{STREAM_PORT}/video_feed")
        print()

        # Start voice recognition
        self.voice.start_listening()
        print()

        print("=" * 60)
        print("  🤖  MEDICARE ROBOT IS RUNNING!")
        print("=" * 60)
        print()
        print("  Voice Commands:")
        print("    'hello'       → Talk to AI (Gemini)")
        print("    'box 1/2/3'   → Move servo to box")
        print("    'come here'   → Move forward")
        print("    'turn left'   → Turn left")
        print("    'turn right'  → Turn right")
        print("    'stop'        → Stop moving")
        print()
        print("  Press Ctrl+C to shutdown")
        print("=" * 60)
        print()

    def stop(self):
        """Stop all robot systems gracefully."""
        print("\n[ROBOT] Shutting down...")
        self.running = False

        # Stop in reverse order
        self.voice.stop_listening()
        self.motors.stop()
        self.streamer.stop()

        # Cleanup
        self.voice.cleanup()
        self.motors.cleanup()
        self.servo.cleanup()
        self.streamer.cleanup()
        self.audio.cleanup()

        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
        except ImportError:
            pass

        print()
        print("=" * 60)
        print("  🤖  Medicare Robot shutdown complete")
        print("=" * 60)


def main():
    robot = MedicareRobot()

    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        robot.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        robot.start()

        # Keep main thread alive
        while robot.running:
            time.sleep(1)

    except KeyboardInterrupt:
        pass
    finally:
        robot.stop()


if __name__ == "__main__":
    main()
